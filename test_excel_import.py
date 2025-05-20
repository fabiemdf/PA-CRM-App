#!/usr/bin/env python3
"""
Simple test script to verify Excel reading and database connection
"""
import os
import sys
import pandas as pd
import logging
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Excel file path
excel_path = r"C:\Users\mfabi\OneDrive\Desktop\app\PA_Claims_FPA_Claims_1747602640.xlsx"

def test_excel_read():
    """Test reading the Excel file"""
    try:
        # Check if file exists
        if not os.path.exists(excel_path):
            logger.error(f"Excel file not found at: {excel_path}")
            return False
            
        logger.info(f"Found Excel file at: {excel_path}")
        
        # Print the first 5 rows of the Excel file without setting a header
        logger.info("Reading first 5 rows to find the correct header row:")
        raw_df = pd.read_excel(excel_path, header=None)
        for i in range(5):
            logger.info(f"Row {i+1}: {raw_df.iloc[i].tolist()}")
        
        # Try different header options
        logger.info("\nReading with header=3 (row 4):")
        df3 = pd.read_excel(excel_path, header=3)
        logger.info(f"Column headers with header=3: {', '.join(df3.columns.tolist()[:10])}")
        
        logger.info("\nReading with header=4 (row 5):")
        df4 = pd.read_excel(excel_path, header=4)
        logger.info(f"Column headers with header=4: {', '.join(df4.columns.tolist()[:10])}")
        
        # Use the correct header
        df = pd.read_excel(excel_path, header=4)
        
        # Print basic info about the DataFrame
        logger.info(f"\nExcel file read successfully")
        logger.info(f"DataFrame shape: {df.shape} (rows, columns)")
        logger.info(f"Column headers: {', '.join(df.columns.tolist())}")
        
        # Print first 5 rows
        for i in range(min(5, len(df))):
            logger.info(f"Row {i+1}: {df.iloc[i].tolist()}")
            
        return True
    except Exception as e:
        logger.error(f"Error reading Excel file: {str(e)}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        # Create database engine
        db_path = 'monday_sync.db'
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Try to connect and create a session
        Session = sessionmaker(bind=engine)
        with Session() as session:
            # Test simple query
            result = session.execute(text("SELECT sqlite_version()")).fetchone()
            logger.info(f"Connected to SQLite database. Version: {result[0]}")
            
            # Test if tables exist
            tables = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            logger.info(f"Found {len(tables)} tables in database: {', '.join([t[0] for t in tables])}")
            
        return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False

def main():
    """Run tests"""
    logger.info("Starting Excel and database tests")
    
    # Test Excel reading
    logger.info("===== Testing Excel File Reading =====")
    excel_success = test_excel_read()
    
    # Test database connection
    logger.info("\n===== Testing Database Connection =====")
    db_success = test_database_connection()
    
    # Summary
    logger.info("\n===== Test Summary =====")
    logger.info(f"Excel reading: {'SUCCESS' if excel_success else 'FAILED'}")
    logger.info(f"Database connection: {'SUCCESS' if db_success else 'FAILED'}")
    
    if excel_success and db_success:
        logger.info("All tests PASSED. You should be able to import the Excel data.")
    else:
        logger.error("Some tests FAILED. Fix the issues before trying to import the data.")

if __name__ == "__main__":
    main() 