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
EXCEL_FILE = r'C:\Users\mfabi\OneDrive\Desktop\PA_Claims_FPA_Claims_1747602640.xlsx'

# Database file
DB_FILE = 'monday_sync.db'

def generate_unique_id():
    """Generate a unique ID for database records"""
    return str(uuid.uuid4())

def main():
    """Main entry point"""
    print(f"Importing claims from: {EXCEL_FILE}")
    
    # Check if the file exists
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: Excel file not found at {EXCEL_FILE}")
        return
    
    # Load the Excel file
    try:
        df = pd.read_excel(EXCEL_FILE)
        print(f"Loaded {len(df)} rows from Excel file")
    except Exception as e:
        print(f"Error loading Excel file: {str(e)}")
        return
    
    # Print column names for reference
    print("\nColumns in Excel file:")
    for col in df.columns:
        print(f"- {col}")
    
    # Connect to database
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Create the Claims board if it doesn't exist
        board_id = "8903072880"  # Using the same ID as defined in the app
        board_name = "Claims"
        
        # Check if board exists
        cursor.execute("SELECT id FROM boards WHERE id = ?", (board_id,))
        existing_board = cursor.fetchone()
        
        if not existing_board:
            print(f"Creating '{board_name}' board in database...")
            cursor.execute(
                "INSERT INTO boards (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (board_id, board_name, "Claims board imported from Excel", datetime.now(), datetime.now())
            )
        else:
            print(f"'{board_name}' board already exists in database, updating...")
            cursor.execute(
                "UPDATE boards SET updated_at = ? WHERE id = ?",
                (datetime.now(), board_id)
            )
        
        # Define board columns (these need to match the Excel data)
        columns = [
            {"id": "name", "title": "Claim Name", "type": "text"},
            {"id": "status", "title": "Status", "type": "status"},
            {"id": "claim_number", "title": "Claim Number", "type": "text"},
            {"id": "insured", "title": "Insured", "type": "text"},
            {"id": "amount", "title": "Amount", "type": "number"},
            {"id": "created_at", "title": "Created At", "type": "date"}
        ]
        
        # Map Excel columns to board columns (adjust based on actual Excel structure)
        # We'll need to customize this mapping based on the actual Excel columns
        column_mapping = {
            "name": "Name",  # Adjust these based on actual Excel column names
            "status": "Status", 
            "claim_number": "Claim Number",
            "insured": "Insured Name",
            "amount": "Claim Amount"
        }
        
        # Create columns in database
        for column in columns:
            # Insert or replace board columns
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO board_columns (id, board_id, title, type, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (column["id"], board_id, column["title"], column["type"], datetime.now(), datetime.now())
                )
            except sqlite3.Error as e:
                print(f"Error creating column {column['id']}: {str(e)}")
                # Print the SQL statement for debugging
                print(f"SQL: INSERT OR REPLACE INTO board_columns (id, board_id, title, type, created_at, updated_at) VALUES ('{column['id']}', '{board_id}', '{column['title']}', '{column['type']}', datetime.now(), datetime.now())")
                continue
        
        # Clear existing items for this board (optional - comment out if you want to keep existing items)
        cursor.execute("DELETE FROM items WHERE board_id = ?", (board_id,))
        cursor.execute("DELETE FROM item_column_values WHERE board_id = ?", (board_id,))
        
        # Import data from Excel to database
        for index, row in df.iterrows():
            try:
                # Generate a unique item ID
                item_id = f"{board_id}_{index}"
                
                # Create item name - use a relevant field from Excel
                # Adjust based on actual Excel data structure
                item_name = str(row.get(column_mapping.get("name", ""), f"Claim {index+1}"))
                
                # Create the item record
                cursor.execute(
                    "INSERT INTO items (id, board_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (item_id, board_id, item_name, datetime.now(), datetime.now())
                )
                
                # Create column values for the item
                for col_id, excel_col in column_mapping.items():
                    if excel_col in row and not pd.isna(row[excel_col]):
                        value = row[excel_col]
                        
                        # Format value based on column type
                        if col_id == "amount" and isinstance(value, (int, float)):
                            value = f"{value:.2f}"
                        elif isinstance(value, (datetime, pd.Timestamp)):
                            value = value.strftime("%Y-%m-%d")
                        else:
                            value = str(value)
                        
                        # Insert column value
                        cursor.execute(
                            "INSERT INTO item_column_values (id, board_id, item_id, column_id, value, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (generate_unique_id(), board_id, item_id, col_id, value, datetime.now(), datetime.now())
                        )
                
                if (index + 1) % 10 == 0:
                    print(f"Imported {index + 1} items...")
            
            except Exception as e:
                print(f"Error importing row {index}: {str(e)}")
                continue
        
        # Commit the changes
        conn.commit()
        
        # Close the connection
        conn.close()
        
        print(f"\nSuccessfully imported {len(df)} claims into the database!")
        print("Please restart the application to see the imported data.")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {str(e)}")
        return
    except Exception as e:
        print(f"Error: {str(e)}")
        return

if __name__ == "__main__":
    main() 