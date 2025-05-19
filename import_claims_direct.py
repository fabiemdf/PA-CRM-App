#!/usr/bin/env python3
"""
Claims Data Import Utility (Direct Import)

Imports claims data from an Excel file directly into the claims table
"""

import os
import pandas as pd
import json
from datetime import datetime
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Source Excel file
EXCEL_FILE = r'C:\Users\mfabi\OneDrive\Desktop\app\PA_Claims_FPA_Claims_1747602640.xlsx'

# Database file
DB_FILE = 'monday_sync.db'

# Create SQLAlchemy engine and session
engine = create_engine(f'sqlite:///{DB_FILE}')
Session = sessionmaker(bind=engine)
Base = declarative_base()

def format_value(value, col_type):
    """Format a value based on its column type"""
    if pd.isna(value):
        return None
        
    try:
        if col_type == "date":
            # Skip date fields for now
            return None
        elif col_type == "number":
            if isinstance(value, (int, float)):
                return float(value)
            return None
        else:
            return str(value)
    except Exception as e:
        print(f"Error formatting value '{value}' of type {col_type}: {str(e)}")
        return None

def main():
    """Main entry point"""
    try:
        # Read Excel file
        print(f"Reading Excel file: {EXCEL_FILE}")
        # Read all columns from A to BG (1 to 59)
        df = pd.read_excel(EXCEL_FILE, header=4, usecols="A:BG")
        
        # Create session
        session = Session()
        
        # Clear existing claims
        print("Clearing existing claims...")
        session.execute(text("DELETE FROM claims"))
        session.commit()
        
        # Get all column names from the Excel file
        excel_columns = df.columns.tolist()
        
        # Map Excel columns to Claim model fields (excluding date fields)
        field_mapping = {
            'name': 'name',
            'claim_number': 'claim_number',
            'person': 'person',
            'claim_status': 'claim_status',
            'client': 'client',
            'email': 'email',
            'status': 'status',
            'file_number': 'file_number',
            'policy_number': 'policy_number',
            'dup_claim_number': 'dup_claim_number',
            'loss_type': 'loss_type',
            'claim_location': 'claim_location',
            'claim_address': 'claim_address',
            'insured_amount': 'insured_amount',
            'initial_offer': 'initial_offer',
            'final_settlement': 'final_settlement',
            'pa_fee_percent': 'pa_fee_percent',
            'pa_fee_amount': 'pa_fee_amount',
            'insurance_company': 'insurance_company',
            'insurance_adjuster': 'insurance_adjuster',
            'notes': 'notes',
            'loss_title': 'loss_title',
            'adjuster_initials': 'adjuster_initials',
            'claim_street': 'claim_street',
            'claim_city': 'claim_city',
            'loss_description': 'loss_description',
            'insurance_companies': 'insurance_companies',
            'insurance_representatives': 'insurance_representatives',
            'treaty_year': 'treaty_year',
            'treaty_type': 'treaty_type',
            'loss_prov_state': 'loss_prov_state',
            'reserve': 'reserve'
        }
        
        # Determine column types
        column_types = {}
        for col_name in excel_columns:
            col_id = col_name.lower().replace(" ", "_").replace(".", "_")
            col_type = "text"  # Default type
            
            # Determine column type based on content
            if "date" in col_name.lower() or "due" in col_name.lower():
                col_type = "date"
                print(f"Column '{col_name}' identified as date type - will be skipped")
            elif any(term in col_name.lower() for term in ["amount", "fee", "percent", "number"]):
                col_type = "number"
            
            column_types[col_id] = col_type
        
        # Import all rows
        total_rows = len(df)
        print(f"Importing {total_rows} rows...")
        
        for index, row in df.iterrows():
            try:
                # Create base claim data
                claim_data = {
                    'board_id': '8903072880',  # Claims board ID
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                # Add mapped fields, fill missing/empty with 'N/A'
                for excel_col in excel_columns:
                    col_id = excel_col.lower().replace(" ", "_").replace(".", "_")
                    if col_id in field_mapping:
                        value = row[excel_col]
                        col_type = column_types.get(col_id, "text")
                        print(f"\nProcessing column '{excel_col}' (type: {col_type})")
                        print(f"Raw value: {value}")
                        formatted_value = format_value(value, col_type)
                        print(f"Formatted value: {formatted_value}")
                        # If missing or empty, fill with 'N/A' for text fields
                        if formatted_value is None:
                            if col_type == "date":
                                formatted_value = None
                            else:
                                formatted_value = 'N/A'
                        claim_data[field_mapping[col_id]] = formatted_value
                
                # Store any unmapped columns in additional_data
                additional_data = {}
                for excel_col in excel_columns:
                    col_id = excel_col.lower().replace(" ", "_").replace(".", "_")
                    if col_id not in field_mapping:
                        value = row[excel_col]
                        if not pd.isna(value):
                            additional_data[col_id] = str(value)
                
                if additional_data:
                    claim_data['additional_data'] = json.dumps(additional_data)
                
                # After adding mapped fields, ensure all required fields are present
                for required_field in field_mapping.values():
                    if required_field not in claim_data:
                        claim_data[required_field] = 'N/A'
                
                # Create and add claim
                session.execute(text("""
                    INSERT INTO claims (
                        name, claim_number, person, claim_status, client, email, status,
                        file_number, policy_number, dup_claim_number,
                        loss_type, claim_location, claim_address, insured_amount, 
                        initial_offer, final_settlement, pa_fee_percent, pa_fee_amount, 
                        insurance_company, insurance_adjuster, notes, loss_title, 
                        adjuster_initials, claim_street, claim_city, loss_description, 
                        insurance_companies, insurance_representatives, treaty_year, 
                        treaty_type, loss_prov_state, reserve,
                        additional_data, board_id, created_at, updated_at
                    ) VALUES (
                        :name, :claim_number, :person, :claim_status, :client, :email, :status,
                        :file_number, :policy_number, :dup_claim_number,
                        :loss_type, :claim_location, :claim_address, :insured_amount,
                        :initial_offer, :final_settlement, :pa_fee_percent, :pa_fee_amount,
                        :insurance_company, :insurance_adjuster, :notes, :loss_title,
                        :adjuster_initials, :claim_street, :claim_city, :loss_description,
                        :insurance_companies, :insurance_representatives, :treaty_year,
                        :treaty_type, :loss_prov_state, :reserve,
                        :additional_data, :board_id, :created_at, :updated_at
                    )
                """), claim_data)
                
                print(f"Imported claim {index + 1}/{total_rows}: {claim_data.get('name', f'Claim {index+1}')}")
                
            except Exception as e:
                print(f"Error importing row {index}: {str(e)}")
                continue
        
        # Commit changes
        session.commit()
        print(f"Import completed successfully. Imported {total_rows} claims.")
        
    except Exception as e:
        print(f"Error during import: {str(e)}")
        sys.exit(1)
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main() 