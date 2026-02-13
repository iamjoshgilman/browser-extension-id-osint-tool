"""
Bulk search executor with concurrent scraping
"""
import queue
import logging
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Type
from database.manager import DatabaseManager
from scrapers.base import ExtensionScraper

logger = logging.getLogger(__name__)


class BulkSearchExecutor:
    """Executes bulk searches with concurrent scraping and progress tracking"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        scraper_classes: Dict[str, Type[ExtensionScraper]],
        max_workers: int = 6,
    ):
        """
        Initialize bulk search executor

        Args:
            db_manager: Database manager instance
            scraper_classes: Dict mapping store names to scraper classes (NOT instances)
            max_workers: Maximum number of concurrent workers
        """
        self.db_manager = db_manager
        self.scraper_classes = scraper_classes
        self.max_workers = max_workers
        self.result_queue = queue.Queue()
        self.cancel_flag = threading.Event()
        self.progress_lock = threading.Lock()

    def execute(
        self,
        job_id: str,
        extension_ids: List[str],
        stores: List[str],
        include_permissions: bool = False,
    ):
        """
        Execute bulk search with concurrent scraping

        Args:
            job_id: Unique job identifier
            extension_ids: List of extension IDs to search
            stores: List of stores to search
            include_permissions: Whether to include permissions (Chrome only)
        """
        try:
            # Update job status to running
            self.db_manager.update_bulk_job(
                job_id, status="running", started_at=datetime.now().isoformat()
            )

            # Create tasks (extension_id, store) tuples
            tasks = [(ext_id, store) for ext_id in extension_ids for store in stores]

            # Track results
            results = {}
            completed_tasks = 0
            failed_tasks = 0

            # Execute tasks concurrently
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_task = {
                    executor.submit(
                        self._process_task,
                        ext_id,
                        store,
                        include_permissions,
                    ): (ext_id, store)
                    for ext_id, store in tasks
                }

                # Process completed futures
                for future in as_completed(future_to_task):
                    if self.cancel_flag.is_set():
                        logger.info(f"Job {job_id} cancelled, stopping execution")
                        break

                    ext_id, store = future_to_task[future]

                    try:
                        result = future.result()

                        # Initialize extension results dict if needed
                        if ext_id not in results:
                            results[ext_id] = {}

                        # Store result
                        results[ext_id][store] = result

                        # Update progress
                        with self.progress_lock:
                            completed_tasks += 1

                            # Update database progress
                            self.db_manager.update_bulk_job(
                                job_id,
                                completed_tasks=completed_tasks,
                                results=results,
                            )

                            # Put progress event on queue for SSE
                            self.result_queue.put(
                                {
                                    "type": "progress",
                                    "extension_id": ext_id,
                                    "store": store,
                                    "completed": completed_tasks,
                                    "total": len(tasks),
                                    "result": result,
                                }
                            )

                            logger.info(
                                f"Job {job_id}: {completed_tasks}/{len(tasks)} "
                                f"completed ({ext_id} in {store})"
                            )

                    except Exception as e:
                        logger.error(
                            f"Task failed for {ext_id} in {store}: {e}", exc_info=True
                        )

                        with self.progress_lock:
                            failed_tasks += 1
                            completed_tasks += 1

                            # Update database
                            self.db_manager.update_bulk_job(
                                job_id,
                                completed_tasks=completed_tasks,
                                failed_tasks=failed_tasks,
                            )

                            # Put error event on queue
                            self.result_queue.put(
                                {
                                    "type": "error",
                                    "extension_id": ext_id,
                                    "store": store,
                                    "error": str(e),
                                    "completed": completed_tasks,
                                    "total": len(tasks),
                                }
                            )

            # Determine final status
            if self.cancel_flag.is_set():
                final_status = "cancelled"
            elif failed_tasks == len(tasks):
                final_status = "failed"
            else:
                final_status = "completed"

            # Update job to completed/cancelled
            self.db_manager.update_bulk_job(
                job_id,
                status=final_status,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                results=results,
                completed_at=datetime.now().isoformat(),
            )

            # Put completion event on queue
            self.result_queue.put(
                {
                    "type": "complete",
                    "status": final_status,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "total_tasks": len(tasks),
                }
            )

            logger.info(f"Job {job_id} {final_status}: {completed_tasks}/{len(tasks)}")

        except Exception as e:
            logger.error(f"Job {job_id} failed with error: {e}", exc_info=True)

            # Update job with error
            self.db_manager.update_bulk_job(
                job_id,
                status="failed",
                error_message=str(e),
                completed_at=datetime.now().isoformat(),
            )

            # Put error event on queue
            self.result_queue.put(
                {
                    "type": "complete",
                    "status": "failed",
                    "error": str(e),
                }
            )

    def _process_task(
        self, extension_id: str, store: str, include_permissions: bool
    ) -> Dict:
        """
        Process a single task (extension_id, store)

        Args:
            extension_id: Extension ID to scrape
            store: Store to scrape from
            include_permissions: Whether to include permissions

        Returns:
            Result dictionary
        """
        # Create a fresh scraper instance for this thread (thread safety)
        scraper_class = self.scraper_classes.get(store)
        if not scraper_class:
            raise ValueError(f"Unknown store: {store}")

        scraper = scraper_class()

        # Check cache first
        cached_data = self.db_manager.get_from_cache(extension_id, store)

        if cached_data:
            # Cache hit
            if cached_data.found:
                cached_data.cached = True
                logger.debug(f"Cache hit for {extension_id} in {store}")
                return cached_data.to_dict()
            else:
                # Cache shows not found - check if it was previously found (delisted)
                previous_cache = self.db_manager.get_previous_found_entry(
                    extension_id, store
                )
                if previous_cache:
                    result_dict = previous_cache.to_dict()
                    result_dict["delisted"] = True
                    result_dict["cached"] = True
                    logger.debug(
                        f"Extension {extension_id} marked as delisted in {store}"
                    )
                    return result_dict
                else:
                    # Not found, no previous entry
                    return {"found": False, "cached": True}

        # Cache miss - scrape
        try:
            # Pass include_permissions only to Chrome scraper
            if store == "chrome":
                extension_data = scraper.scrape(
                    extension_id, include_permissions=include_permissions
                )
            else:
                extension_data = scraper.scrape(extension_id)

            if extension_data:
                # Check for delisted BEFORE saving (save overwrites old entry)
                previous_cache = None
                if not extension_data.found:
                    previous_cache = self.db_manager.get_previous_found_entry(
                        extension_id, store
                    )

                # Save to cache regardless of found status
                self.db_manager.save_to_cache(extension_data)

                # Return appropriate result
                if extension_data.found:
                    return extension_data.to_dict()
                elif previous_cache:
                    # Extension was previously found but now gone = delisted
                    result_dict = previous_cache.to_dict()
                    result_dict["delisted"] = True
                    result_dict["cached"] = True
                    logger.info(f"Extension {extension_id} marked as delisted in {store}")
                    return result_dict
                else:
                    return {"found": False}
            else:
                return {"found": False}

        except Exception as e:
            logger.error(f"Error scraping {extension_id} from {store}: {e}")
            raise

    def cancel(self):
        """Cancel the running job"""
        self.cancel_flag.set()
