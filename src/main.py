#!/usr/bin/env python3
"""
Monday-Uploader PySide Edition
Main application entry point
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import pandas as pd

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QMessageBox, 
    QFileDialog, QMenu, QTabWidget, QToolBar, 
    QStatusBar, QDialog, QStyle, QInputDialog
)
from PySide6.QtCore import Qt, QSettings, QSize, QPoint
from PySide6.QtGui import QIcon, QAction, QKeySequence, QCursor

try:
    # Application modules
    from src.ui.main_window import MainWindow
    from src.models.database import init_db, CalendarEvent
    from utils.logger import setup_logger
    from utils.error_handling import MondayError, handle_error
    from controllers.feedback_controller import FeedbackController
    from controllers.data_controller import DataController
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

def import_board_data(main_window):
    """Import data from Excel files into Monday boards."""
    try:
        # Let user select the Excel file
        file_dialog = QFileDialog(main_window)
        file_dialog.setWindowTitle("Select Excel File to Import")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Excel files (*.xlsx *.xls)")
        
        if not file_dialog.exec():
            return  # User canceled
            
        selected_files = file_dialog.selectedFiles()
        if not selected_files:
            return
            
        excel_path = selected_files[0]
        logger.info(f"Selected Excel file: {excel_path}")
        
        # Let user select which board to import to
        available_boards = list(DEFAULT_BOARDS.keys())
        # Create a menu with board options
        board_menu = QMenu(main_window)
        
        for board_name in available_boards:
            action = board_menu.addAction(board_name)
            action.setData(board_name)
        
        # Show the menu at the cursor position
        selected_action = board_menu.exec(QCursor.pos())
        
        if not selected_action:
            return  # User canceled
            
        selected_board = selected_action.data()
        logger.info(f"Selected board: {selected_board}")
        
        # Import the data
        if 'data' in main_window.controllers and main_window.controllers['data'].engine is not None:
            logger.info(f"Reading {selected_board} Excel file...")
            
            # Ask user which row contains headers
            header_row, ok = QInputDialog.getInt(
                main_window,
                "Header Row",
                f"Which row contains the column headers? (1-based)",
                5,  # Default to row 5
                1,  # Minimum value
                20  # Maximum value
            )
            
            if not ok:
                return  # User canceled
                
            # Convert to 0-based index for pandas
            header_index = header_row - 1
            
            # Read the Excel file
            df = pd.read_excel(excel_path, header=header_index)
            logger.info(f"Excel file read successfully. Found {len(df.columns)} columns and {len(df)} rows")
            logger.info(f"Column headers: {', '.join(df.columns.tolist())}")
            
            # Get the column headers
            headers = df.columns.tolist()
            
            # Extract data items
            data_items = df.values.tolist()
            logger.info(f"Extracted {len(data_items)} data rows")
            
            # Import the data
            data_controller = main_window.controllers['data']
            
            # Inject headers as the first row of data_items to match existing processing
            data_with_headers = [headers] + data_items
            success = data_controller.import_excel_data_for_board(selected_board, data_with_headers)
            
            if success:
                logger.info(f"Successfully imported {selected_board} data")
                
                # Refresh the board in the UI
                board_id = main_window.controllers['board'].get_board_id(selected_board)
                if board_id:
                    main_window._on_select_board(board_id)
                    logger.info(f"{selected_board} board refreshed in UI")
                
                # Show success message
                QMessageBox.information(
                    main_window,
                    "Import Successful",
                    f"Successfully imported {len(data_items)} {selected_board} records from Excel file."
                )
            else:
                logger.error(f"Failed to import {selected_board} data")
                QMessageBox.critical(
                    main_window,
                    "Import Error",
                    f"Failed to import {selected_board} data. Check the logs for details."
                )
    except Exception as e:
        logger.error(f"Error importing data: {str(e)}")
        QMessageBox.critical(
            main_window,
            "Import Error",
            f"Error importing data: {str(e)}"
        )

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
        engine = None
        try:
            from sqlalchemy import create_engine
            engine = create_engine(f'sqlite:///{db_path}')
            logger.info(f"Database engine created for: {db_path}")
        except Exception as e:
            logger.error(f"Database engine creation failed: {str(e)}")
            QMessageBox.critical(
                None, 
                "Database Error", 
                f"Failed to create database engine: {str(e)}"
            )
        
        # Path to the Excel files
        excel_files = {
            "Claims": r"C:\Users\mfabi\OneDrive\Desktop\app\PA_Claims_FPA_Claims_1747602640.xlsx"
        }

        # Initialize controllers
        feedback_controller = FeedbackController(engine)
        
        # Create main window
        main_window = MainWindow(engine, DEFAULT_BOARDS)
        main_window.show()

        # Select the first available board to show it initially
        try:
            if 'board' in main_window.controllers and main_window.controllers['board']:
                # Get the first board from the available boards
                boards = main_window.controllers['board'].get_boards()
                if boards:
                    first_board_name = next(iter(boards))
                    first_board_id = boards[first_board_name]
                    logger.info(f"Selecting initial board: {first_board_name} ({first_board_id})")
                    
                    # Tell the main window to select this board
                    main_window._on_board_selected(first_board_id)
                    
                    # Also select it in the boards panel
                    if "boards" in main_window.panels:
                        main_window.panels["boards"].select_board(first_board_id)
        except Exception as e:
            logger.error(f"Error selecting initial board: {str(e)}")
            # Non-critical error, we can continue

        # Process Claims Excel file
        claims_path = excel_files["Claims"]
        try:
            # Check if file exists
            if not os.path.exists(claims_path):
                logger.error(f"Claims Excel file not found at: {claims_path}")
                QMessageBox.warning(
                    main_window,
                    "File Not Found",
                    f"Claims Excel file not found at:\n{claims_path}"
                )
            else:
                logger.info(f"Found Claims Excel file at: {claims_path}")
                
                try:
                    # Read the Excel file - Note: Headers start at row 5
                    logger.info("Reading Claims Excel file...")
                    df = pd.read_excel(claims_path, header=4)  # header=4 means row 5 is the header
                    logger.info(f"Excel file read successfully. Found {len(df.columns)} columns and {len(df)} rows")
                    logger.info(f"Column headers: {', '.join(df.columns.tolist())}")
                    
                    # Get the column headers
                    headers = df.columns.tolist()
                    
                    # Extract data items (all rows, not including headers since they're already extracted)
                    data_items = df.values.tolist()
                    logger.info(f"Extracted {len(data_items)} data rows")
                    
                    # Import the data into the Claims board
                    if 'data' in main_window.controllers and engine is not None:
                        logger.info("Importing data into Claims board...")
                        data_controller = main_window.controllers['data']
                        
                        # Explicitly validate the database connection
                        if not hasattr(data_controller, 'engine') or data_controller.engine is None:
                            logger.error("Data controller has no valid database engine")
                            QMessageBox.critical(
                                main_window,
                                "Database Error",
                                "Database engine not initialized properly. Cannot import data."
                            )
                        else:
                            # Try to import the data
                            # Inject headers as the first row of data_items to match existing processing
                            data_with_headers = [headers] + data_items
                            success = data_controller.import_excel_data_for_board("Claims", data_with_headers)
                            if success:
                                logger.info("Successfully imported Claims data")
                                
                                # Refresh the Claims board in the UI
                                board_id = main_window.controllers['board'].get_board_id("Claims")
                                if board_id:
                                    main_window._on_select_board(board_id)
                                    logger.info("Claims board refreshed in UI")
                                    
                                    # Show success message
                                    QMessageBox.information(
                                        main_window,
                                        "Import Successful",
                                        f"Successfully imported {len(data_items)-1} Claims records from Excel file."
                                    )
                            else:
                                logger.error("Failed to import Claims data")
                                QMessageBox.critical(
                                    main_window,
                                    "Import Error",
                                    "Failed to import Claims data. Check the logs for details."
                                )
                    else:
                        logger.error("Data controller not found in main window controllers")
                        QMessageBox.critical(
                            main_window,
                            "Controller Error",
                            "Data controller not found in application. Cannot import data."
                        )
                except Exception as e:
                    logger.error(f"Error processing Excel file content: {str(e)}")
                    QMessageBox.critical(
                        main_window,
                        "Excel Processing Error",
                        f"Error processing Excel file content:\n\n{str(e)}"
                    )
                
        except Exception as e:
            logger.error(f"Error processing Claims Excel file: {str(e)}")
            QMessageBox.critical(
                main_window,
                "Excel Import Error",
                f"Error processing Claims Excel file:\n\n{str(e)}"
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

        # Add import data action to main window
        if hasattr(main_window, 'file_menu'):
            import_action = QAction("Import Board Data...", main_window)
            import_action.triggered.connect(lambda: import_board_data(main_window))
            main_window.file_menu.addAction(import_action)
        elif hasattr(main_window, 'menuBar'):
            # If there's a menu bar but no file_menu yet
            file_menu = main_window.menuBar().addMenu("&File")
            import_action = QAction("Import Board Data...", main_window)
            import_action.triggered.connect(lambda: import_board_data(main_window))
            file_menu.addAction(import_action)
            main_window.file_menu = file_menu
        else:
            # Create a toolbar button instead
            import_action = QAction("Import Data", main_window)
            import_action.triggered.connect(lambda: import_board_data(main_window))
            toolbar = QToolBar("Main Toolbar", main_window)
            toolbar.addAction(import_action)
            main_window.addToolBar(toolbar)

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