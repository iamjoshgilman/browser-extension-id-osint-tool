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


if __name__ == '__main__':
    unittest.main()
