#!/usr/bin/env python3
"""
Monday-Uploader PySide Edition
Main application entry point
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional
import json
import pandas as pd

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QMessageBox, 
    QFileDialog, QMenu, QTabWidget, QToolBar, 
    QStatusBar, QDialog, QStyle
)
from PySide6.QtCore import Qt, QSettings, QSize, QPoint
from PySide6.QtGui import QIcon, QAction, QKeySequence

try:
    # Application modules
    from ui.main_window import MainWindow
    from models.database import init_db
    from utils.logger import setup_logger
    from utils.error_handling import MondayError, handle_error
    from controllers.feedback_controller import FeedbackController
except ImportError as e:
    print(f"Error importing application modules: {str(e)}")
    QMessageBox.critical(
        None, 
        "Import Error", 
        f"Failed to import required modules: {str(e)}\n\nPlease ensure all dependencies are installed."
    )
    sys.exit(1)

# Configure logging
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Setup logger
logger = setup_logger()

# Application constants
APP_NAME = "Monday Uploader"
APP_VERSION = "1.0.0"
CONFIG_FILE = "config.json"
SETTINGS_FILE = "settings.json"

# Default boards for offline mode
DEFAULT_BOARDS = {
    "Claims": "8903072880",
    "Clients": "8768750185",
    "Public Adjusters": "9000027904",
    "Employees": "9000122678",
    "Notes": "8968042746",
    "Documents": "8769212922",
    "Damage Estimates": "8769684040",
    "Communications": "8769967973",
    "Leads": "8778422410",
    "Tasks": "8792210214",
    "Insurance Companies": "8792259332",
    "Contacts": "8792441338",
    "Marketing Activities": "8792459115",
    "Insurance Representatives": "8876787198",
    "Police Report": "8884671005",
    "Weather Reports": "9123456789"
}

def create_sample_calendar_events(main_window):
    """Create sample calendar events for demonstration."""
    try:
        if 'calendar' in main_window.controllers:
            calendar_controller = main_window.controllers['calendar']
            
            # Clear existing events
            # This is just for demo purposes to avoid duplicate events on restart
            from sqlalchemy import delete
            from models.database import CalendarEvent
            main_window.session.execute(delete(CalendarEvent))
            main_window.session.commit()
            
            # Current date for reference
            now = datetime.now()
            today = datetime(now.year, now.month, now.day)
            
            # Create sample events
            events = [
                {
                    "title": "Team Meeting",
                    "description": "Weekly team status meeting",
                    "start_time": today + timedelta(days=1, hours=10),
                    "end_time": today + timedelta(days=1, hours=11),
                    "is_all_day": False,
                    "color": "#3788d8",  # Blue
                    "location": "Conference Room A",
                    "event_type": "Meeting"
                },
                {
                    "title": "Client Review",
                    "description": "Review claim status with client",
                    "start_time": today + timedelta(days=2, hours=14),
                    "end_time": today + timedelta(days=2, hours=15, minutes=30),
                    "is_all_day": False,
                    "color": "#38b262",  # Green
                    "location": "Online Zoom Meeting",
                    "event_type": "Appointment"
                },
                {
                    "title": "Insurance Filing Deadline",
                    "description": "Final day to submit insurance claim documents",
                    "start_time": today + timedelta(days=5),
                    "end_time": today + timedelta(days=5),
                    "is_all_day": True,
                    "color": "#ff9900",  # Orange
                    "event_type": "Due Date"
                },
                {
                    "title": "Staff Training",
                    "description": "New software training session",
                    "start_time": today - timedelta(days=1, hours=13),
                    "end_time": today - timedelta(days=1, hours=16),
                    "is_all_day": False,
                    "color": "#9c31f9",  # Purple
                    "location": "Training Room",
                    "event_type": "Training"
                },
                {
                    "title": "Monthly Report Due",
                    "description": "Submit monthly activity report",
                    "start_time": today + timedelta(days=10),
                    "end_time": today + timedelta(days=10),
                    "is_all_day": True,
                    "color": "#e53935",  # Red
                    "event_type": "Due Date"
                }
            ]
            
            # Create each event
            for event_data in events:
                calendar_controller.create_event(event_data)
                
            logger.info(f"Created {len(events)} sample calendar events")
            
            # Refresh calendar panel if it exists
            if "calendar" in main_window.panels:
                main_window.panels["calendar"].refresh()
                
    except Exception as e:
        logger.error(f"Error creating sample calendar events: {str(e)}")

def main():
    """Application entry point"""
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        
        # Optional: Set app style
        try:
            import qdarkstyle
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
        except ImportError:
            logger.warning("QDarkStyle not found, using default style")
        
        # Initialize database
        db_path = 'monday_sync.db'
        try:
            engine = init_db(db_path)
            logger.info(f"Database initialized: {db_path}")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            QMessageBox.critical(
                None, 
                "Database Error", 
                f"Failed to initialize database: {str(e)}"
            )
            return 1
        
        # Path to the Excel files
        excel_files = {
            "Claims": "data/excel/PA_Claims_FPA_Claims.xlsx",
            "Clients": "data/excel/Clients_FPA_Clients.xlsx",
            "Public Adjusters": "data/excel/Public_Adjusters_FPA.xlsx",
            "Employees": "data/excel/Employees_Group_Title.xlsx",
            "Notes": "data/excel/Notes_Monday_Notes.xlsx",
            "Insurance Representatives": "data/excel/Insurance_Representatives_Fraser.xlsx",
            "Police Report": "data/excel/Police_Report_Group_Title.xlsx",
            "Damage Estimates": "data/excel/Damage_Estimates_Fraser.xlsx",
            "Communications": "data/excel/Communications_Fraser.xlsx",
            "Leads": "data/excel/Leads_Group_Title.xlsx",
            "Documents": "data/excel/Documents_Fraser.xlsx",
            "Tasks": "data/excel/Tasks_Group_Title.xlsx",
            "Insurance Companies": "data/excel/Insurance_Companies_Fraser.xlsx",
            "Contacts": "data/excel/Contacts_Business_Contacts.xlsx",
            "Marketing Activities": "data/excel/Marketing_Activities_This_week.xlsx"
        }

        # Initialize controllers
        feedback_controller = FeedbackController(engine)
        
        # Create main window
        main_window = MainWindow(engine, DEFAULT_BOARDS)
        main_window.show()

        # Process all Excel files
        for board_name, excel_path in excel_files.items():
            try:
                # Check if file exists
                if not os.path.exists(excel_path):
                    logger.warning(f"Excel file not found: {excel_path}")
                    continue

                # Read the Excel file
                df = pd.read_excel(excel_path)
                
                # Extract board name from first cell or use the key as default
                board_name_from_excel = df.iloc[0, 0] if not pd.isna(df.iloc[0, 0]) else board_name
                logger.info(f"Processing {board_name} board from {excel_path}")
                
                # Extract data items - skip any metadata rows
                data_items = df.values.tolist()
                
                # Import the data into the board
                if 'data' in main_window.controllers:
                    success = main_window.controllers['data'].import_excel_data_for_board(board_name, data_items)
                    if success:
                        logger.info(f"Successfully imported Excel data into {board_name} board")
                        
                        # Refresh the board in the UI
                        board_id = main_window.controllers['board'].get_board_id(board_name)
                        if board_id:
                            # Only select the Claims board by default
                            if board_name == "Claims":
                                main_window._on_select_board(board_id)
                    else:
                        logger.error(f"Failed to import Excel data into {board_name} board")
                    
            except Exception as e:
                logger.error(f"Error processing {board_name} Excel file: {str(e)}")
                QMessageBox.warning(
                    main_window,
                    "Excel Import Warning",
                    f"Could not process {board_name} Excel file: {str(e)}\n\nPlease ensure the file exists at: {excel_path}"
                )

        # Initialize weather feeds
        try:
            if 'data' in main_window.controllers:
                weather_board_id = main_window.controllers['board'].get_board_id("Weather Reports")
                if weather_board_id:
                    # Fetch and store weather feeds
                    print("Fetching weather feeds...")
                    weather_feeds = main_window.controllers['data'].fetch_and_store_weather_feeds()
                    if weather_feeds:
                        print(f"Successfully fetched {len(weather_feeds)} weather feeds")
                        # Display a notification to the user
                        QMessageBox.information(
                            main_window,
                            "Weather Reports",
                            f"Successfully loaded {len(weather_feeds)} weather alerts and reports from NOAA, NHC, and weather.gov"
                        )
                    else:
                        print("No weather feeds were fetched")
        except Exception as e:
            print(f"Error fetching weather feeds: {str(e)}")
            logger.error(f"Error fetching weather feeds: {str(e)}")

        # Create sample calendar events
        create_sample_calendar_events(main_window)

        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}")
        if 'app' in locals():
            QMessageBox.critical(
                None, 
                "Startup Error", 
                f"Application failed to start: {str(e)}"
            )
        return 1

if __name__ == "__main__":
    sys.exit(main()) 