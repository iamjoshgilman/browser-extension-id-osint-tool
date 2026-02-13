"""
Unit tests for database manager
"""
import unittest
import tempfile
import os
from datetime import datetime, timedelta
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database.manager import DatabaseManager
from models.extension import ExtensionData
from models.api_key import ApiKeyData
import hashlib


class TestDatabaseManager(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        """Create temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_manager = DatabaseManager(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up temporary database"""
        self.temp_db.close()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_save_and_retrieve(self):
        """Test saving and retrieving extension data"""
        # Create test data
        test_data = ExtensionData(
            extension_id='test123',
            name='Test Extension',
            store_source='chrome',
            publisher='Test Publisher',
            description='Test description',
            version='1.0.0',
            found=True
        )
        
        # Save to database
        self.db_manager.save_to_cache(test_data)
        
        # Retrieve from database
        retrieved = self.db_manager.get_from_cache('test123', 'chrome')
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.extension_id, 'test123')
        self.assertEqual(retrieved.name, 'Test Extension')
        self.assertEqual(retrieved.publisher, 'Test Publisher')
        self.assertTrue(retrieved.found)
    
    def test_cache_expiry(self):
        """Test cache expiry"""
        # Create test data
        test_data = ExtensionData(
            extension_id='test456',
            name='Old Extension',
            store_source='firefox',
            found=True
        )

        # Save to database
        self.db_manager.save_to_cache(test_data)

        # Verify it's in cache with default expiry (7 days)
        retrieved = self.db_manager.get_from_cache('test456', 'firefox')
        self.assertIsNotNone(retrieved)

        # Set cache expiry to a very large value (100 days) - should still be cached
        self.db_manager.cache_expiry_days = 100
        retrieved = self.db_manager.get_from_cache('test456', 'firefox')
        self.assertIsNotNone(retrieved)

        # Set cache expiry to 0 - cache never expires
        self.db_manager.cache_expiry_days = 0
        retrieved = self.db_manager.get_from_cache('test456', 'firefox')
        self.assertIsNotNone(retrieved)
    
    def test_permissions_handling(self):
        """Test permissions list handling"""
        # Create test data with permissions
        test_data = ExtensionData(
            extension_id='test789',
            name='Permission Test',
            store_source='edge',
            permissions=['tabs', 'storage', 'history'],
            found=True
        )
        
        # Save and retrieve
        self.db_manager.save_to_cache(test_data)
        retrieved = self.db_manager.get_from_cache('test789', 'edge')
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.permissions, ['tabs', 'storage', 'history'])
    
    def test_log_search(self):
        """Test search logging"""
        self.db_manager.log_search(
            'test123',
            ['chrome', 'firefox'],
            '127.0.0.1',
            'Test User Agent'
        )
        
        # Get stats to verify logging
        stats = self.db_manager.get_stats()
        self.assertGreater(stats['searches_24h'], 0)
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        # Add some test data
        for i in range(5):
            data = ExtensionData(
                extension_id=f'test{i}',
                name=f'Test Extension {i}',
                store_source='chrome' if i % 2 == 0 else 'firefox',
                found=True
            )
            self.db_manager.save_to_cache(data)
        
        # Get stats
        stats = self.db_manager.get_stats()
        
        self.assertEqual(stats['total_cached'], 5)
        self.assertEqual(stats['unique_extensions'], 5)
        self.assertIn('chrome', stats['by_store'])
        self.assertIn('firefox', stats['by_store'])
        self.assertEqual(stats['by_store']['chrome'], 3)
        self.assertEqual(stats['by_store']['firefox'], 2)
    
    def test_cleanup_old_cache(self):
        """Test cleaning up old cache entries"""
        # Add test data
        test_data = ExtensionData(
            extension_id='old123',
            name='Old Extension',
            store_source='chrome',
            found=True
        )
        self.db_manager.save_to_cache(test_data)
        
        # Cleanup with 0 days (should remove everything)
        deleted = self.db_manager.cleanup_old_cache(days=0)
        
        self.assertEqual(deleted, 1)
        
        # Verify it's gone
        retrieved = self.db_manager.get_from_cache('old123', 'chrome')
        self.assertIsNone(retrieved)
    
    def test_unique_constraint(self):
        """Test unique constraint on extension_id + store"""
        # Create test data
        test_data1 = ExtensionData(
            extension_id='unique123',
            name='First Version',
            store_source='chrome',
            version='1.0.0',
            found=True
        )

        test_data2 = ExtensionData(
            extension_id='unique123',
            name='Updated Version',
            store_source='chrome',
            version='2.0.0',
            found=True
        )

        # Save first version
        self.db_manager.save_to_cache(test_data1)

        # Save second version (should update)
        self.db_manager.save_to_cache(test_data2)

        # Retrieve - should get updated version
        retrieved = self.db_manager.get_from_cache('unique123', 'chrome')
        self.assertEqual(retrieved.name, 'Updated Version')
        self.assertEqual(retrieved.version, '2.0.0')

        # Verify only one entry exists
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM extension_cache WHERE extension_id = ?',
                ('unique123',)
            )
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)

    def test_get_previous_found_entry(self):
        """Test get_previous_found_entry returns entry with found=True"""
        # Create test data with found=True
        test_data = ExtensionData(
            extension_id='prev123',
            name='Previously Found Extension',
            store_source='chrome',
            publisher='Test Publisher',
            version='1.0.0',
            found=True
        )

        # Save to database
        self.db_manager.save_to_cache(test_data)

        # Retrieve using get_previous_found_entry
        retrieved = self.db_manager.get_previous_found_entry('prev123', 'chrome')

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.extension_id, 'prev123')
        self.assertEqual(retrieved.name, 'Previously Found Extension')
        self.assertEqual(retrieved.publisher, 'Test Publisher')
        self.assertTrue(retrieved.found)

    def test_get_previous_found_entry_not_found(self):
        """Test get_previous_found_entry returns None when no previous found entry exists"""
        # Query for non-existent extension
        retrieved = self.db_manager.get_previous_found_entry('nonexistent', 'chrome')
        self.assertIsNone(retrieved)

        # Save extension with found=False
        test_data = ExtensionData(
            extension_id='notfound123',
            name='',
            store_source='firefox',
            found=False
        )
        self.db_manager.save_to_cache(test_data)

        # Should return None because found=False
        retrieved = self.db_manager.get_previous_found_entry('notfound123', 'firefox')
        self.assertIsNone(retrieved)

    def test_delisted_detection_flow(self):
        """Test full delisted detection flow"""
        # Step 1: Save an extension with found=True
        found_data = ExtensionData(
            extension_id='delisted123',
            name='Extension That Will Be Delisted',
            store_source='edge',
            publisher='Original Publisher',
            version='2.0.0',
            user_count='10,000+ users',
            found=True
        )
        self.db_manager.save_to_cache(found_data)

        # Step 2: Verify it's in cache and marked as found
        cached = self.db_manager.get_from_cache('delisted123', 'edge')
        self.assertIsNotNone(cached)
        self.assertTrue(cached.found)
        self.assertEqual(cached.name, 'Extension That Will Be Delisted')

        # Step 3: Get previous found entry BEFORE overwriting with not-found
        previous = self.db_manager.get_previous_found_entry('delisted123', 'edge')
        self.assertIsNotNone(previous)
        self.assertTrue(previous.found)
        self.assertEqual(previous.name, 'Extension That Will Be Delisted')
        self.assertEqual(previous.publisher, 'Original Publisher')

        # Step 4: Now save a not-found entry (simulating extension being removed)
        not_found_data = ExtensionData(
            extension_id='delisted123',
            name='',
            store_source='edge',
            found=False
        )
        self.db_manager.save_to_cache(not_found_data)

        # Step 5: Verify the cache now has found=False
        cached_after = self.db_manager.get_from_cache('delisted123', 'edge')
        self.assertIsNotNone(cached_after)
        self.assertFalse(cached_after.found)

        # Step 6: get_previous_found_entry should now return None (entry is found=False)
        previous_after = self.db_manager.get_previous_found_entry('delisted123', 'edge')
        self.assertIsNone(previous_after)

    def test_save_snapshot_creates_first(self):
        """Test that saving an extension creates the first snapshot"""
        # Create and save extension data
        test_data = ExtensionData(
            extension_id='snap123',
            name='Snapshot Test Extension',
            store_source='chrome',
            version='1.0.0',
            permissions=['tabs', 'storage'],
            found=True
        )
        self.db_manager.save_to_cache(test_data)

        # Verify snapshot was created
        history = self.db_manager.get_extension_history('snap123', 'chrome')
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['version'], '1.0.0')
        self.assertEqual(history[0]['name'], 'Snapshot Test Extension')
        self.assertEqual(sorted(history[0]['permissions']), ['storage', 'tabs'])

    def test_save_snapshot_no_change_no_dup(self):
        """Test that saving same data twice doesn't create duplicate snapshots"""
        # Create and save extension data
        test_data = ExtensionData(
            extension_id='nodup123',
            name='No Duplicate Test',
            store_source='firefox',
            version='2.0.0',
            permissions=['activeTab', 'cookies'],
            found=True
        )
        self.db_manager.save_to_cache(test_data)

        # Save the exact same data again
        self.db_manager.save_to_cache(test_data)

        # Verify still only 1 snapshot
        history = self.db_manager.get_extension_history('nodup123', 'firefox')
        self.assertEqual(len(history), 1)

    def test_save_snapshot_version_change(self):
        """Test that version changes create new snapshots"""
        # Create and save first version
        test_data_v1 = ExtensionData(
            extension_id='version123',
            name='Version Change Test',
            store_source='edge',
            version='1.0.0',
            permissions=['tabs'],
            found=True
        )
        self.db_manager.save_to_cache(test_data_v1)

        # Update version and save again
        test_data_v2 = ExtensionData(
            extension_id='version123',
            name='Version Change Test',
            store_source='edge',
            version='2.0.0',
            permissions=['tabs'],
            found=True
        )
        self.db_manager.save_to_cache(test_data_v2)

        # Verify 2 snapshots exist
        history = self.db_manager.get_extension_history('version123', 'edge')
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['version'], '1.0.0')
        self.assertEqual(history[1]['version'], '2.0.0')

    def test_save_snapshot_permission_change(self):
        """Test that permission changes create new snapshots"""
        # Create and save first version with initial permissions
        test_data_v1 = ExtensionData(
            extension_id='perm123',
            name='Permission Change Test',
            store_source='chrome',
            version='1.0.0',
            permissions=['tabs', 'storage'],
            found=True
        )
        self.db_manager.save_to_cache(test_data_v1)

        # Update permissions and save again
        test_data_v2 = ExtensionData(
            extension_id='perm123',
            name='Permission Change Test',
            store_source='chrome',
            version='1.0.0',
            permissions=['tabs', 'storage', 'cookies'],
            found=True
        )
        self.db_manager.save_to_cache(test_data_v2)

        # Verify 2 snapshots exist
        history = self.db_manager.get_extension_history('perm123', 'chrome')
        self.assertEqual(len(history), 2)
        self.assertEqual(sorted(history[0]['permissions']), ['storage', 'tabs'])
        self.assertEqual(sorted(history[1]['permissions']), ['cookies', 'storage', 'tabs'])

    def test_get_extension_history_order(self):
        """Test that history is returned in chronological order"""
        # Create and save multiple versions
        for i in range(3):
            test_data = ExtensionData(
                extension_id='order123',
                name=f'Version {i}',
                store_source='firefox',
                version=f'{i}.0.0',
                permissions=['tabs'],
                found=True
            )
            self.db_manager.save_to_cache(test_data)

        # Get history
        history = self.db_manager.get_extension_history('order123', 'firefox')

        # Verify chronological order
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]['version'], '0.0.0')
        self.assertEqual(history[1]['version'], '1.0.0')
        self.assertEqual(history[2]['version'], '2.0.0')

    def test_get_extension_history_empty(self):
        """Test that unknown extension returns empty list"""
        history = self.db_manager.get_extension_history('nonexistent', 'chrome')
        self.assertEqual(history, [])
        self.assertEqual(len(history), 0)

    def test_create_and_get_api_key(self):
        """Test creating and retrieving API key"""
        # Create API key
        key_hash = hashlib.sha256(b"test-key-123").hexdigest()
        key_id = self.db_manager.create_api_key(
            key_hash=key_hash,
            key_prefix="test_",
            name="Test API Key",
            description="Test description",
            created_by="admin@test.com",
            rate_limit_per_minute=60,
            rate_limit_per_hour=1000,
            permissions=["search", "bulk-search"],
        )

        self.assertIsNotNone(key_id)
        self.assertGreater(key_id, 0)

        # Retrieve by hash
        api_key = self.db_manager.get_api_key_by_hash(key_hash)
        self.assertIsNotNone(api_key)
        self.assertEqual(api_key.id, key_id)
        self.assertEqual(api_key.key_hash, key_hash)
        self.assertEqual(api_key.key_prefix, "test_")
        self.assertEqual(api_key.name, "Test API Key")
        self.assertEqual(api_key.description, "Test description")
        self.assertEqual(api_key.created_by, "admin@test.com")
        self.assertEqual(api_key.rate_limit_per_minute, 60)
        self.assertEqual(api_key.rate_limit_per_hour, 1000)
        self.assertTrue(api_key.is_active)
        self.assertEqual(api_key.permissions, ["search", "bulk-search"])
        self.assertIsNone(api_key.revoked_at)

        # Retrieve by ID
        api_key2 = self.db_manager.get_api_key(key_id)
        self.assertIsNotNone(api_key2)
        self.assertEqual(api_key2.id, key_id)
        self.assertEqual(api_key2.name, "Test API Key")

    def test_list_api_keys(self):
        """Test listing API keys"""
        # Create multiple keys
        key1_hash = hashlib.sha256(b"key1").hexdigest()
        key2_hash = hashlib.sha256(b"key2").hexdigest()
        key3_hash = hashlib.sha256(b"key3").hexdigest()

        id1 = self.db_manager.create_api_key(
            key_hash=key1_hash, key_prefix="k1_", name="Key 1"
        )
        id2 = self.db_manager.create_api_key(
            key_hash=key2_hash, key_prefix="k2_", name="Key 2"
        )
        id3 = self.db_manager.create_api_key(
            key_hash=key3_hash, key_prefix="k3_", name="Key 3"
        )

        # List all keys
        keys = self.db_manager.list_api_keys()
        self.assertEqual(len(keys), 3)

        # Verify all keys are present
        key_names = [k.name for k in keys]
        self.assertIn("Key 1", key_names)
        self.assertIn("Key 2", key_names)
        self.assertIn("Key 3", key_names)

        # Revoke one key
        self.db_manager.revoke_api_key(id2)

        # List should now exclude revoked key
        keys = self.db_manager.list_api_keys()
        self.assertEqual(len(keys), 2)
        key_names = [k.name for k in keys]
        self.assertIn("Key 1", key_names)
        self.assertIn("Key 3", key_names)
        self.assertNotIn("Key 2", key_names)

    def test_revoke_api_key(self):
        """Test revoking an API key"""
        # Create key
        key_hash = hashlib.sha256(b"revoke-test").hexdigest()
        key_id = self.db_manager.create_api_key(
            key_hash=key_hash, key_prefix="rev_", name="Revoke Test"
        )

        # Verify it's active
        api_key = self.db_manager.get_api_key(key_id)
        self.assertTrue(api_key.is_active)
        self.assertIsNone(api_key.revoked_at)

        # Revoke it
        self.db_manager.revoke_api_key(key_id)

        # Verify it's revoked
        api_key = self.db_manager.get_api_key(key_id)
        self.assertFalse(api_key.is_active)
        self.assertIsNotNone(api_key.revoked_at)

        # Verify it's not in list
        keys = self.db_manager.list_api_keys()
        self.assertEqual(len(keys), 0)

    def test_update_api_key(self):
        """Test updating API key"""
        # Create key
        key_hash = hashlib.sha256(b"update-test").hexdigest()
        key_id = self.db_manager.create_api_key(
            key_hash=key_hash,
            key_prefix="upd_",
            name="Original Name",
            description="Original Description",
            rate_limit_per_minute=30,
            rate_limit_per_hour=500,
        )

        # Update fields
        self.db_manager.update_api_key(
            key_id,
            name="Updated Name",
            description="Updated Description",
            rate_limit_per_minute=100,
            rate_limit_per_hour=2000,
            is_active=False,
            permissions=["search"],
        )

        # Verify updates
        api_key = self.db_manager.get_api_key(key_id)
        self.assertEqual(api_key.name, "Updated Name")
        self.assertEqual(api_key.description, "Updated Description")
        self.assertEqual(api_key.rate_limit_per_minute, 100)
        self.assertEqual(api_key.rate_limit_per_hour, 2000)
        self.assertFalse(api_key.is_active)
        self.assertEqual(api_key.permissions, ["search"])

    def test_log_and_get_usage(self):
        """Test logging API usage and retrieving stats"""
        # Create API key
        key_hash = hashlib.sha256(b"usage-test").hexdigest()
        key_id = self.db_manager.create_api_key(
            key_hash=key_hash, key_prefix="usg_", name="Usage Test"
        )

        # Log some usage
        self.db_manager.log_api_usage(
            api_key_id=key_id,
            endpoint="/api/search",
            method="POST",
            status_code=200,
            response_time_ms=150,
            ip_address="127.0.0.1",
            user_agent="Test Agent",
        )

        self.db_manager.log_api_usage(
            api_key_id=key_id,
            endpoint="/api/bulk-search",
            method="POST",
            status_code=200,
            response_time_ms=350,
        )

        self.db_manager.log_api_usage(
            api_key_id=key_id,
            endpoint="/api/search",
            method="POST",
            status_code=400,
            response_time_ms=50,
            error_message="Bad request",
        )

        # Log usage for another key (anonymous)
        self.db_manager.log_api_usage(
            api_key_id=None,
            endpoint="/api/health",
            method="GET",
            status_code=200,
        )

        # Get stats for the specific key
        stats = self.db_manager.get_usage_stats(key_id=key_id, period_hours=24)
        self.assertEqual(stats["total_requests"], 3)
        self.assertEqual(stats["by_endpoint"]["/api/search"], 2)
        self.assertEqual(stats["by_endpoint"]["/api/bulk-search"], 1)
        self.assertEqual(stats["by_status"]["200"], 2)
        self.assertEqual(stats["by_status"]["400"], 1)
        self.assertEqual(stats["period_hours"], 24)
        self.assertGreater(stats["avg_response_time_ms"], 0)

        # Get overall stats (all keys)
        overall_stats = self.db_manager.get_usage_stats(period_hours=24)
        self.assertEqual(overall_stats["total_requests"], 4)
        self.assertIn(str(key_id), overall_stats["by_key"])
        self.assertEqual(overall_stats["by_key"][str(key_id)], 3)
        self.assertEqual(overall_stats["by_key"]["anonymous"], 1)

        # Get 24h usage for key
        usage_24h = self.db_manager.get_key_usage_24h(key_id)
        self.assertEqual(usage_24h, 3)

    def test_bulk_job_lifecycle(self):
        """Test creating, updating, getting, and cleaning up bulk jobs"""
        import uuid

        # Create API key for the job
        key_hash = hashlib.sha256(b"bulk-test").hexdigest()
        key_id = self.db_manager.create_api_key(
            key_hash=key_hash, key_prefix="blk_", name="Bulk Test"
        )

        # Create bulk job
        job_id = str(uuid.uuid4())
        extension_ids = ["ext1", "ext2", "ext3"]
        stores = ["chrome", "firefox"]
        total_tasks = len(extension_ids) * len(stores)

        returned_id = self.db_manager.create_bulk_job(
            job_id=job_id,
            api_key_id=key_id,
            extension_ids=extension_ids,
            stores=stores,
            include_permissions=True,
            total_tasks=total_tasks,
        )

        self.assertEqual(returned_id, job_id)

        # Get the job
        job = self.db_manager.get_bulk_job(job_id)
        self.assertIsNotNone(job)
        self.assertEqual(job["id"], job_id)
        self.assertEqual(job["api_key_id"], key_id)
        self.assertEqual(job["status"], "pending")
        self.assertEqual(job["extension_ids"], extension_ids)
        self.assertEqual(job["stores"], stores)
        self.assertEqual(job["include_permissions"], True)
        self.assertEqual(job["total_tasks"], total_tasks)
        self.assertEqual(job["completed_tasks"], 0)
        self.assertEqual(job["failed_tasks"], 0)
        self.assertIsNone(job["results"])

        # Update job to running
        self.db_manager.update_bulk_job(
            job_id, status="running", started_at=datetime.now().isoformat()
        )

        job = self.db_manager.get_bulk_job(job_id)
        self.assertEqual(job["status"], "running")
        self.assertIsNotNone(job["started_at"])

        # Update job progress
        results = {"ext1": {"chrome": {"found": True}}}
        self.db_manager.update_bulk_job(
            job_id, completed_tasks=1, results=results
        )

        job = self.db_manager.get_bulk_job(job_id)
        self.assertEqual(job["completed_tasks"], 1)
        self.assertIsNotNone(job["results"])
        self.assertEqual(job["results"]["ext1"]["chrome"]["found"], True)

        # Complete the job
        final_results = {
            "ext1": {"chrome": {"found": True}, "firefox": {"found": False}},
            "ext2": {"chrome": {"found": True}, "firefox": {"found": True}},
            "ext3": {"chrome": {"found": False}, "firefox": {"found": False}},
        }
        self.db_manager.update_bulk_job(
            job_id,
            status="completed",
            completed_tasks=total_tasks,
            failed_tasks=0,
            results=final_results,
            completed_at=datetime.now().isoformat(),
        )

        job = self.db_manager.get_bulk_job(job_id)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["completed_tasks"], total_tasks)
        self.assertIsNotNone(job["completed_at"])
        self.assertEqual(len(job["results"]), 3)

        # Cleanup old jobs (should not delete this one yet as it's recent)
        deleted = self.db_manager.cleanup_old_bulk_jobs(hours=24)
        self.assertEqual(deleted, 0)

        # Verify job still exists
        job = self.db_manager.get_bulk_job(job_id)
        self.assertIsNotNone(job)

        # Cleanup with 0 hours (should delete completed jobs immediately)
        deleted = self.db_manager.cleanup_old_bulk_jobs(hours=0)
        self.assertEqual(deleted, 1)

        # Verify job is gone
        job = self.db_manager.get_bulk_job(job_id)
        self.assertIsNone(job)

    def test_bulk_job_cleanup(self):
        """Test bulk job cleanup removes only old completed/failed jobs"""
        import uuid

        # Create multiple jobs with different statuses
        job1_id = str(uuid.uuid4())
        job2_id = str(uuid.uuid4())
        job3_id = str(uuid.uuid4())

        # Create jobs
        self.db_manager.create_bulk_job(
            job_id=job1_id,
            api_key_id=None,
            extension_ids=["ext1"],
            stores=["chrome"],
            include_permissions=False,
            total_tasks=1,
        )

        self.db_manager.create_bulk_job(
            job_id=job2_id,
            api_key_id=None,
            extension_ids=["ext2"],
            stores=["firefox"],
            include_permissions=False,
            total_tasks=1,
        )

        self.db_manager.create_bulk_job(
            job_id=job3_id,
            api_key_id=None,
            extension_ids=["ext3"],
            stores=["edge"],
            include_permissions=False,
            total_tasks=1,
        )

        # Complete job1 and job2, leave job3 running
        self.db_manager.update_bulk_job(
            job1_id,
            status="completed",
            completed_at=datetime.now().isoformat(),
        )

        self.db_manager.update_bulk_job(
            job2_id,
            status="failed",
            completed_at=datetime.now().isoformat(),
        )

        self.db_manager.update_bulk_job(
            job3_id,
            status="running",
        )

        # Cleanup with 0 hours should delete job1 and job2 but not job3
        deleted = self.db_manager.cleanup_old_bulk_jobs(hours=0)
        self.assertEqual(deleted, 2)

        # Verify job3 still exists
        job3 = self.db_manager.get_bulk_job(job3_id)
        self.assertIsNotNone(job3)
        self.assertEqual(job3["status"], "running")

        # Verify job1 and job2 are gone
        self.assertIsNone(self.db_manager.get_bulk_job(job1_id))
        self.assertIsNone(self.db_manager.get_bulk_job(job2_id))


if __name__ == '__main__':
    unittest.main()
