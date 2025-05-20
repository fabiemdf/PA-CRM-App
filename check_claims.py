#!/usr/bin/env python3
"""
Script to check the Claims data in the database
"""
import sqlite3
import logging
import json
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'monday_sync.db'
BOARD_ID = "8903072880"
BOARD_NAME = "Claims"

def check_claims_data():
    """Check the Claims data in the database"""
    try:
        # Check if database file exists
        if not os.path.exists(DB_PATH):
            logger.error(f"Database file not found: {DB_PATH}")
            return
            
        logger.info(f"Database file exists at: {os.path.abspath(DB_PATH)}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check BoardData table for Claims records
        cursor.execute("SELECT COUNT(*) FROM board_data WHERE board_id = ?", (BOARD_ID,))
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} records in board_data table for Claims board (ID: {BOARD_ID})")
        
        if count > 0:
            # Get sample records to verify data
            cursor.execute("SELECT id, name, data FROM board_data WHERE board_id = ? LIMIT 5", (BOARD_ID,))
            records = cursor.fetchall()
            
            logger.info("Sample Claims records:")
            for id, name, data in records:
                data_dict = json.loads(data)
                logger.info(f"  ID: {id}, Name: {name}")
                
                # Print key fields
                fields_to_show = ['Claim Number', 'Loss Type', 'Claim Status', 'Insurance Company']
                for field in fields_to_show:
                    if field in data_dict:
                        logger.info(f"    {field}: {data_dict[field]}")
            
            # Now try with SQLAlchemy to verify connection works that way
            logger.info("\nTesting SQLAlchemy connection:")
            engine = create_engine(f'sqlite:///{DB_PATH}')
            
            with Session(engine) as session:
                # Test that we can query the database
                result = session.execute(text("SELECT COUNT(*) FROM board_data WHERE board_id = :board_id"),
                                        {"board_id": BOARD_ID}).fetchone()
                logger.info(f"SQLAlchemy found {result[0]} Claims records")
                
                # Check a few records
                result = session.execute(text(
                    "SELECT id, name, data FROM board_data WHERE board_id = :board_id LIMIT 3"),
                    {"board_id": BOARD_ID}).fetchall()
                
                logger.info("Sample records via SQLAlchemy:")
                for id, name, data in result:
                    data_dict = json.loads(data)
                    logger.info(f"  ID: {id}, Name: {name}")
                    
                    if 'Claim Number' in data_dict:
                        logger.info(f"    Claim Number: {data_dict['Claim Number']}")
            
            # Export data to CSV for verification
            cursor.execute("SELECT name, data FROM board_data WHERE board_id = ?", (BOARD_ID,))
            records = cursor.fetchall()
            
            # Create a DataFrame
            rows = []
            for name, data in records:
                data_dict = json.loads(data)
                data_dict['Name'] = name  # Ensure name is included
                rows.append(data_dict)
            
            df = pd.DataFrame(rows)
            
            # Select key columns if they exist
            key_columns = ['Name', 'Claim Number', 'Loss Type', 'Claim Status', 'Insurance Company']
            columns_to_export = [col for col in key_columns if col in df.columns]
            
            # Export to CSV
            csv_path = 'claims_export.csv'
            df[columns_to_export].to_csv(csv_path, index=False)
            logger.info(f"Exported {len(df)} claims to {csv_path}")
            
        else:
            logger.warning("No Claims records found in the database!")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking claims data: {str(e)}")
        logger.exception("Detailed traceback:")

def main():
    """Run the claims check"""
    logger.info("Starting Claims data check")
    check_claims_data()
    logger.info("Claims data check complete")

if __name__ == "__main__":
    main() 