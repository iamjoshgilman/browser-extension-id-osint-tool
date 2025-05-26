#!/usr/bin/env python3
"""
Clear cache entries that have incomplete or incorrect data
"""
import sqlite3
import json
import sys
import os

def clear_cache(db_path):
    """Clear problematic cache entries"""
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, let's see what's in the cache
    cursor.execute("""
        SELECT extension_id, store, data, found 
        FROM extension_cache 
        ORDER BY scraped_at DESC
    """)
    
    rows = cursor.fetchall()
    print(f"Found {len(rows)} cache entries")
    
    # Count entries to remove
    to_remove = 0
    for row in rows:
        extension_id, store, data_json, found = row
        try:
            data = json.loads(data_json)
            # Remove entries where:
            # 1. found is False
            # 2. name is "Unknown Extension"
            # 3. Data is incomplete (no version, no users, etc.)
            if (not found or 
                data.get('name') == 'Unknown Extension' or
                (not data.get('version') and not data.get('user_count'))):
                to_remove += 1
                print(f"Will remove: {extension_id} from {store} - found={found}, name={data.get('name')}")
        except:
            pass
    
    if to_remove > 0:
        response = input(f"\nRemove {to_remove} problematic entries? (y/n): ")
        if response.lower() == 'y':
            # Delete entries where found is False or name is Unknown Extension
            cursor.execute("""
                DELETE FROM extension_cache 
                WHERE found = 0 
                OR data LIKE '%"name": "Unknown Extension"%'
                OR (data NOT LIKE '%"version":%' AND data NOT LIKE '%"user_count":%')
            """)
            
            deleted = cursor.rowcount
            conn.commit()
            print(f"Deleted {deleted} cache entries")
        else:
            print("Cancelled")
    else:
        print("No problematic entries found")
    
    # Show remaining entries
    cursor.execute("SELECT COUNT(*) FROM extension_cache")
    remaining = cursor.fetchone()[0]
    print(f"Remaining cache entries: {remaining}")
    
    conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/extensions_cache.db"
    clear_cache(db_path)
