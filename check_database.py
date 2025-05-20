#!/usr/bin/env python3
"""
Script to check the database contents
"""
import sqlite3
import logging
import json
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'monday_sync.db'

def check_database():
    """Check the database contents"""
    try:
        # Check if database file exists
        if not os.path.exists(DB_PATH):
            logger.error(f"Database file not found: {DB_PATH}")
            return
            
        logger.info(f"Database file exists at: {os.path.abspath(DB_PATH)}")
        logger.info(f"Database file size: {os.path.getsize(DB_PATH) / 1024:.2f} KB")
        
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        tables = [t[0] for t in tables]
        logger.info(f"Database contains {len(tables)} tables: {', '.join(tables)}")
        
        # Check if board_data table exists
        if 'board_data' not in tables:
            logger.error("board_data table does not exist in the database!")
            return
        
        # Check BoardData table
        cursor.execute("SELECT COUNT(*) FROM board_data WHERE board_id = '8903072880'")
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} records in board_data table for Claims board (ID: 8903072880)")
        
        # Get some sample records
        if count > 0:
            cursor.execute("SELECT id, name, data FROM board_data WHERE board_id = '8903072880' LIMIT 5")
            records = cursor.fetchall()
            logger.info("Sample records:")
            for id, name, data in records:
                data_dict = json.loads(data)
                logger.info(f"  ID: {id}, Name: {name}, Fields: {len(data_dict)}")
                
                # Print a few fields for the first record
                if id == records[0][0]:
                    logger.info("  Sample fields from first record:")
                    fields_to_show = ["Name", "Claim Number", "Loss Type", "Claim Status", "Insurance Company"]
                    for field in fields_to_show:
                        if field in data_dict:
                            logger.info(f"    {field}: {data_dict[field]}")
        
        # Check for SQLAlchemy models in database
        model_tables = ['claims', 'clients', 'public_adjusters', 'employees', 'notes', 'board_data']
        for table in model_tables:
            if table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logger.info(f"Table '{table}' contains {count} records")
                except Exception as e:
                    logger.error(f"Error querying table '{table}': {str(e)}")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")

def main():
    """Run the database check"""
    logger.info("Starting database check")
    check_database()
    logger.info("Database check complete")

if __name__ == "__main__":
    main() 