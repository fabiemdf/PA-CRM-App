#!/usr/bin/env python3
"""
Database Export Utility (JSON)

Exports all tables from the Monday Uploader SQLite database to a JSON file
"""

import os
import sqlite3
import json
import sys
from datetime import datetime

# Database file
DB_FILE = 'monday_sync.db'

# Export file
EXPORT_FILE = 'db_export/monday_data.json'

def main():
    """Main entry point"""
    print(f"Exporting database: {DB_FILE}")
    
    # Create export directory if it doesn't exist
    export_dir = os.path.dirname(EXPORT_FILE)
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
        print(f"Created export directory: {export_dir}")

    # Connect to database
    try:
        conn = sqlite3.connect(DB_FILE)
        # Enable row factory to get dictionaries instead of tuples
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        if not tables:
            print("No tables found in the database.")
            return
        
        print(f"Found {len(tables)} tables:")
        
        # Create a dictionary to hold all data
        db_data = {
            "export_date": datetime.now().isoformat(),
            "tables": {}
        }
        
        # Process each table
        for table_name in tables:
            print(f"- {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Get column information
            column_info = []
            for column in columns:
                column_info.append({
                    "name": column[1],
                    "type": column[2],
                    "notnull": bool(column[3]),
                    "default_value": column[4],
                    "is_primary_key": bool(column[5])
                })
            
            # Export table data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            table_data = []
            for row in rows:
                table_data.append({key: row[key] for key in row.keys()})
            
            # Add to main data structure
            db_data["tables"][table_name] = {
                "schema": column_info,
                "rows": table_data
            }
            
            print(f"  Exported {len(rows)} rows")
        
        # Close the connection
        conn.close()
        
        # Write to JSON file
        with open(EXPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, indent=2)
        
        print("\nExport completed successfully!")
        print(f"All data has been exported to: {os.path.abspath(EXPORT_FILE)}")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return
    except Exception as e:
        print(f"Error: {e}")
        return

if __name__ == "__main__":
    main() 