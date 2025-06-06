#!/usr/bin/env python3
"""
Database Schema Checker

Shows the schema of all tables to debug import issues
"""

import sqlite3

# Database file
DB_FILE = 'monday_sync.db'

def main():
    """Main entry point"""
    print(f"Checking database schema: {DB_FILE}")
    
    # Connect to database
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get the schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            print(table[0])
        
        # Check item_column_values table specifically
        print("\n\nChecking ITEM_COLUMN_VALUES table specifically:")
        try:
            cursor.execute("SELECT * FROM item_column_values LIMIT 1")
            column_names = [description[0] for description in cursor.description]
            print(f"Column names: {column_names}")
        except sqlite3.Error as e:
            print(f"Error accessing item_column_values table: {e}")
            
        # Close the connection
        conn.close()
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return
    except Exception as e:
        print(f"Error: {e}")
        return

if __name__ == "__main__":
    main() 