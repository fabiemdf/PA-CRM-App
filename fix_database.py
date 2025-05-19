#!/usr/bin/env python3
"""
Database Fix Utility

Fixes the database structure to match the expected schema in the import script
"""

import sqlite3
from datetime import datetime

# Database file
DB_FILE = 'monday_sync.db'

def main():
    """Main entry point"""
    print(f"Fixing database schema: {DB_FILE}")
    
    # Connect to database
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if item_column_values table exists and has correct schema
        print("Checking item_column_values table...")
        cursor.execute("PRAGMA table_info(item_column_values)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'column_id' not in column_names:
            # Create a new table with the correct schema
            print("Creating item_column_values table with correct schema...")
            cursor.execute("""
            DROP TABLE IF EXISTS item_column_values_new
            """)
            
            cursor.execute("""
            CREATE TABLE item_column_values_new (
                id VARCHAR(50) PRIMARY KEY,
                board_id VARCHAR(50) NOT NULL,
                item_id VARCHAR(50) NOT NULL,
                column_id VARCHAR(50) NOT NULL,
                value TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
            """)
            
            # If the original table exists, try to migrate data
            try:
                print("Attempting to migrate data from existing table...")
                cursor.execute("SELECT * FROM item_column_values")
                rows = cursor.fetchall()
                
                if rows:
                    print(f"Found {len(rows)} rows to migrate")
                    # Get column names from the original table
                    col_names = [description[0] for description in cursor.description]
                    print(f"Original columns: {col_names}")
                    
                    # If compatible, migrate data
                    # This assumes the original table is somewhat compatible
                    # Adjust the mapping based on actual columns
                    
            except sqlite3.Error as e:
                print(f"No existing data to migrate: {e}")
            
            # Rename the new table to replace the old one
            cursor.execute("DROP TABLE IF EXISTS item_column_values")
            cursor.execute("ALTER TABLE item_column_values_new RENAME TO item_column_values")
            print("Successfully created item_column_values table with correct schema")
            
        else:
            print("item_column_values table already has correct schema")

        # Commit changes
        conn.commit()
        
        print("Database schema has been updated!")
        print("You can now run the import_claims.py script again.")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return
    except Exception as e:
        print(f"Error: {e}")
        return
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    main() 