#!/usr/bin/env python3
"""
Update Claims Table Schema

Updates the claims table with the new schema including all columns from the Excel import
"""

import os
import sqlite3
from datetime import datetime

# Database file
DB_FILE = 'monday_sync.db'

def main():
    """Main entry point"""
    try:
        # Connect to database
        print(f"Connecting to database: {DB_FILE}")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Drop existing claims table
        print("Dropping existing claims table...")
        cursor.execute("DROP TABLE IF EXISTS claims")
        
        # Create new claims table with updated schema
        print("Creating new claims table...")
        cursor.execute("""
        CREATE TABLE claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            claim_number VARCHAR(50),
            person VARCHAR(255),
            claim_status VARCHAR(50),
            client VARCHAR(255),
            email VARCHAR(255),
            status VARCHAR(50),
            file_number VARCHAR(50),
            received_on TEXT,
            policy_number VARCHAR(50),
            dup_claim_number VARCHAR(50),
            loss_date TEXT,
            claim_filed_date TEXT,
            loss_type VARCHAR(100),
            claim_location VARCHAR(255),
            claim_address VARCHAR(255),
            insured_amount FLOAT,
            initial_offer FLOAT,
            final_settlement FLOAT,
            pa_fee_percent FLOAT,
            pa_fee_amount FLOAT,
            insurance_company VARCHAR(255),
            insurance_adjuster VARCHAR(255),
            notes TEXT,
            loss_title VARCHAR(255),
            last_activity TEXT,
            adjuster_initials VARCHAR(50),
            claim_street VARCHAR(255),
            claim_city VARCHAR(255),
            loss_description TEXT,
            deadline_date TEXT,
            insurance_companies VARCHAR(255),
            insurance_representatives VARCHAR(255),
            treaty_year VARCHAR(50),
            treaty_type VARCHAR(100),
            stat_limitation TEXT,
            loss_prov_state VARCHAR(50),
            reserve FLOAT,
            first_contact TEXT,
            next_rpt_due TEXT,
            additional_data TEXT,
            board_id VARCHAR(50),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Commit changes
        conn.commit()
        print("Claims table updated successfully")
        
    except Exception as e:
        print(f"Error during update: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 