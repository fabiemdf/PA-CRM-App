#!/usr/bin/env python3
"""
Database Export Utility

Exports all tables from the Monday Uploader SQLite database to CSV files
"""

import os
import sqlite3
import csv
import sys
from datetime import datetime

# Database file
DB_FILE = 'monday_sync.db'

# Export directory
EXPORT_DIR = 'db_export'

def main():
    """Main entry point"""
    print(f"Exporting database: {DB_FILE}")
    
    # Create export directory if it doesn't exist
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
        print(f"Created export directory: {EXPORT_DIR}")

    # Connect to database
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
        
        print(f"Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            print(f"- {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            # Export table data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Write to CSV
            csv_file = os.path.join(EXPORT_DIR, f"{table_name}.csv")
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(column_names)  # Write header
                writer.writerows(rows)  # Write data
            
            print(f"  Exported {len(rows)} rows to {csv_file}")
        
        # Close the connection
        conn.close()
        
        print("\nExport completed successfully!")
        print(f"All data has been exported to: {os.path.abspath(EXPORT_DIR)}")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return
    except Exception as e:
        print(f"Error: {e}")
        return

if __name__ == "__main__":
    main() 