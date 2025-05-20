#!/usr/bin/env python3
"""
Simple script to view Claims data from the database in a simple UI
"""
import sys
import os
import json
import sqlite3
from PySide6.QtWidgets import (QApplication, QMainWindow, QTableWidget, 
                              QTableWidgetItem, QVBoxLayout, QWidget,
                              QLabel, QPushButton, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt

# Database path
DB_PATH = 'monday_sync.db'
BOARD_ID = "8903072880"
BOARD_NAME = "Claims"

class ClaimsViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Claims Viewer")
        self.resize(1200, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add header
        header = QLabel("Claims Data Viewer")
        header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(header)
        
        # Create table widget
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        # Add refresh button
        refresh_button = QPushButton("Refresh Data")
        refresh_button.clicked.connect(self.load_claims)
        layout.addWidget(refresh_button)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Load claims
        self.load_claims()
    
    def load_claims(self):
        """Load claims from the database"""
        try:
            # Reset table
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            
            self.status_label.setText("Loading data...")
            QApplication.processEvents()
            
            # Check if database file exists
            if not os.path.exists(DB_PATH):
                self.status_label.setText(f"Database file not found: {DB_PATH}")
                return
            
            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get claims data
            cursor.execute("SELECT id, name, data FROM board_data WHERE board_id = ?", (BOARD_ID,))
            records = cursor.fetchall()
            
            if not records:
                self.status_label.setText("No claims found in database")
                return
            
            # Define columns to display
            columns = ["Name", "Claim Number", "Loss Type", "Claim Status", 
                       "Insurance Company", "PA Fee %", "Final Settlemet"]
            
            # Set up table
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            self.table.setRowCount(len(records))
            
            # Populate table
            for row, (id, name, data_json) in enumerate(records):
                try:
                    data = json.loads(data_json)
                    
                    # Set name (first column)
                    self.table.setItem(row, 0, QTableWidgetItem(name))
                    
                    # Set other columns from data
                    for col, column in enumerate(columns[1:], 1):
                        if column in data:
                            value = data[column]
                            self.table.setItem(row, col, QTableWidgetItem(str(value)))
                
                except Exception as e:
                    print(f"Error processing row {row}: {str(e)}")
            
            # Resize columns to content
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            
            # Close connection
            conn.close()
            
            self.status_label.setText(f"Loaded {len(records)} claims")
            
        except Exception as e:
            self.status_label.setText(f"Error loading claims: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load claims: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = ClaimsViewer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 