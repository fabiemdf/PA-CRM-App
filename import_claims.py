#!/usr/bin/env python3
"""
Claims Data Import Utility

Imports claims data from an Excel file into the Monday Uploader database
"""

import os
import sqlite3
import pandas as pd
import json
from datetime import datetime
import uuid
import sys

# Source Excel file
EXCEL_FILE = r'C:\Users\mfabi\OneDrive\Desktop\app\PA_Claims_FPA_Claims_1747602640.xlsx'

# Database file
DB_FILE = 'monday_sync.db'

def generate_unique_id():
    """Generate a unique ID for database records"""
    return str(uuid.uuid4())

def format_value(value, col_type):
    """Format a value based on its column type"""
    if pd.isna(value):
        return None
        
    try:
        if col_type == "date":
            if isinstance(value, (datetime, pd.Timestamp)):
                return value.strftime("%Y-%m-%d")
            return str(value)
        elif col_type == "number":
            if isinstance(value, (int, float)):
                return f"{value:.2f}"
            return str(value)
        else:
            return str(value)
    except:
        return str(value)

def main():
    """Main entry point"""
    try:
        # Read Excel file
        print(f"Reading Excel file: {EXCEL_FILE}")
        # Read all columns from A to BG (1 to 59)
        df = pd.read_excel(EXCEL_FILE, header=4, usecols="A:BG")
        
        # Connect to database
        print(f"Connecting to database: {DB_FILE}")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get or create board ID for claims
        board_id = "8903072880"  # Updated to match the app's DEFAULT_BOARDS
        cursor.execute("SELECT id FROM boards WHERE id = ?", (board_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO boards (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (board_id, "Claims", datetime.now(), datetime.now())
            )
        
        # Clear existing items and column values for this board
        print("Clearing existing items...")
        cursor.execute("SELECT id FROM items WHERE board_id = ?", (board_id,))
        item_ids = [row[0] for row in cursor.fetchall()]
        if item_ids:
            # Delete from item_column_values for these item_ids
            cursor.executemany("DELETE FROM item_column_values WHERE item_id = ?", [(item_id,) for item_id in item_ids])
        cursor.execute("DELETE FROM items WHERE board_id = ?", (board_id,))
        
        # Get all column names from the Excel file
        excel_columns = df.columns.tolist()
        
        # Create columns in database based on Excel headers
        column_types = {}
        for col_name in excel_columns:
            col_id = col_name.lower().replace(" ", "_").replace(".", "_")
            col_type = "text"  # Default type
            
            # Determine column type based on content
            if "date" in col_name.lower() or "due" in col_name.lower():
                col_type = "date"
            elif any(term in col_name.lower() for term in ["amount", "fee", "percent", "number"]):
                col_type = "number"
            
            column_types[col_id] = col_type
            
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO board_columns (id, board_id, title, type, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (col_id, board_id, col_name, col_type, datetime.now(), datetime.now())
                )
            except sqlite3.Error as e:
                print(f"Error creating column {col_id}: {str(e)}")
                continue
        
        # Import data from Excel to database
        total_rows = len(df)
        print(f"Importing {total_rows} rows...")
        
        for index, row in df.iterrows():
            try:
                # Generate a unique item ID
                item_id = f"{board_id}_{index}"
                
                # Create item name from the first column or use a default
                item_name = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else f"Claim {index+1}"
                
                # Create the item record
                cursor.execute(
                    "INSERT INTO items (id, board_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (item_id, board_id, item_name, datetime.now(), datetime.now())
                )
                
                # Create column values for the item
                for col_name in excel_columns:
                    col_id = col_name.lower().replace(" ", "_").replace(".", "_")
                    value = row[col_name]
                    col_type = column_types.get(col_id, "text")
                    
                    formatted_value = format_value(value, col_type)
                    if formatted_value is not None:
                        try:
                            cursor.execute(
                                "INSERT INTO item_column_values (item_id, column_id, value, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                                (item_id, col_id, formatted_value, datetime.now(), datetime.now())
                            )
                        except sqlite3.Error as e:
                            print(f"Error inserting value for {col_id} in row {index}: {str(e)}")
                            continue
                
                print(f"Imported claim {index + 1}/{total_rows}: {item_name}")
                
            except Exception as e:
                print(f"Error importing row {index}: {str(e)}")
                continue
        
        # Commit changes
        conn.commit()
        print(f"Import completed successfully. Imported {total_rows} claims.")
        
    except Exception as e:
        print(f"Error during import: {str(e)}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 