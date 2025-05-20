#!/usr/bin/env python3
"""
Standalone script to import Claims data from Excel to the database.
"""
import os
import sys
import pandas as pd
import logging
import json
import sqlite3
from datetime import datetime

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Excel file path
EXCEL_PATH = r"C:\Users\mfabi\OneDrive\Desktop\app\PA_Claims_FPA_Claims_1747602640.xlsx"
DB_PATH = 'monday_sync.db'
BOARD_ID = "8903072880"
BOARD_NAME = "Claims"

def create_tables_if_not_exist(cursor):
    """Create necessary tables if they don't exist"""
    # Create BoardData table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS board_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        board_id TEXT NOT NULL,
        board_name TEXT NOT NULL,
        name TEXT NOT NULL,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create index for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_board_data_board_id ON board_data(board_id)')

def import_excel_to_db():
    """Read Excel file and import to database"""
    try:
        # Check if file exists
        if not os.path.exists(EXCEL_PATH):
            logger.error(f"Excel file not found at: {EXCEL_PATH}")
            return False
            
        logger.info(f"Found Excel file at: {EXCEL_PATH}")
        
        # Try to read the file with headers at row 5 (index 4)
        df = pd.read_excel(EXCEL_PATH, header=4)
        
        # Basic info about the DataFrame
        logger.info(f"Excel file read successfully")
        logger.info(f"DataFrame shape: {df.shape} (rows, columns)")
        logger.info(f"Column headers: {', '.join(df.columns.tolist())}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Ensure tables exist
        create_tables_if_not_exist(cursor)
        
        # Clear existing data for this board
        cursor.execute("DELETE FROM board_data WHERE board_id = ?", (BOARD_ID,))
        logger.info(f"Cleared existing records for board {BOARD_NAME}")
        
        # Get column headers
        headers = df.columns.tolist()
        
        # Convert Excel data to records
        records_imported = 0
        for i, row in df.iterrows():
            try:
                # Extract primary name field (first column)
                name = str(row['Name']) if not pd.isna(row['Name']) else f"{BOARD_NAME} Item {i+1}"
                
                # Create a dictionary for all fields
                row_data = {}
                for header in headers:
                    value = row[header]
                    # Convert NaN to empty string
                    if pd.isna(value):
                        value = ""
                    # Convert datetime objects to string
                    elif isinstance(value, pd.Timestamp):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    # Convert other values to string
                    else:
                        value = str(value)
                    
                    row_data[header] = value
                
                # Convert to JSON string
                json_data = json.dumps(row_data)
                
                # Insert into database
                cursor.execute(
                    "INSERT INTO board_data (board_id, board_name, name, data) VALUES (?, ?, ?, ?)",
                    (BOARD_ID, BOARD_NAME, name, json_data)
                )
                records_imported += 1
                
                # Log progress every 10 records
                if records_imported % 10 == 0:
                    logger.info(f"Imported {records_imported} records so far...")
                
            except Exception as e:
                logger.error(f"Error processing row {i}: {str(e)}")
                continue
        
        # Commit all changes
        conn.commit()
        logger.info(f"Successfully imported {records_imported} records into {BOARD_NAME} board")
        
        # Close connection
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error importing Excel data: {str(e)}")
        return False

def main():
    """Run the import process"""
    logger.info("Starting Excel import process")
    
    success = import_excel_to_db()
    
    if success:
        logger.info("Import completed successfully. The data should now be available in the application.")
    else:
        logger.error("Import failed. Please check the logs for details.")

if __name__ == "__main__":
    main() 