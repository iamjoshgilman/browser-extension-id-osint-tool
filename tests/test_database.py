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


if __name__ == '__main__':
    unittest.main()
