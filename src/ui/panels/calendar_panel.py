"""
Calendar panel for displaying and managing events.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCalendarWidget, QToolBar, 
    QPushButton, QLabel, QListWidget, QListWidgetItem, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QDateTimeEdit, QCheckBox,
    QComboBox, QMenu, QMessageBox, QSplitter, QColorDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, Slot, QDate, QSize, QDateTime, QTime
from PySide6.QtGui import QColor, QFont, QIcon, QAction

# Get logger
logger = logging.getLogger("monday_uploader.calendar_panel")

class SimpleEventDialog(QDialog):
    """Simple dialog for creating and editing events."""
    
    def __init__(self, parent=None, event=None):
        super().__init__(parent)
        
        self.setWindowTitle("Create Event" if not event else "Edit Event")
        self.setMinimumWidth(400)
        
        self.event = event
        self.result_data = None
        
        # Create layout
        layout = QVBoxLayout()
        
        # Form layout
        form = QFormLayout()
        
        # Title
        self.title_edit = QLineEdit()
        form.addRow("Title:", self.title_edit)
        
        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        form.addRow("Description:", self.desc_edit)
        
        # Event type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Meeting", "Appointment", "Reminder", "Due Date", "Holiday", "Other"])
        form.addRow("Type:", self.type_combo)
        
        # Date fields
        self.start_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_edit.setCalendarPopup(True)
        form.addRow("Start:", self.start_edit)
        
        self.end_edit = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.end_edit.setCalendarPopup(True)
        form.addRow("End:", self.end_edit)
        
        layout.addLayout(form)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # If editing, populate fields
        if event:
            self._populate_fields()
    
    def _populate_fields(self):
        """Populate fields with event data."""
        if not self.event:
            return
            
        self.title_edit.setText(self.event.get("title", ""))
        self.desc_edit.setText(self.event.get("description", ""))
        
        event_type = self.event.get("event_type", "Meeting")
        index = self.type_combo.findText(event_type)
        self.type_combo.setCurrentIndex(max(0, index))
        
        # Handle start time
        start_time = self.event.get("start_time")
        if start_time:
            start_date = QDate(start_time.year, start_time.month, start_time.day)
            start_time_obj = QTime(start_time.hour, start_time.minute)
            self.start_edit.setDateTime(QDateTime(start_date, start_time_obj))
        
        # Handle end time
        end_time = self.event.get("end_time")
        if end_time:
            end_date = QDate(end_time.year, end_time.month, end_time.day)
            end_time_obj = QTime(end_time.hour, end_time.minute)
            self.end_edit.setDateTime(QDateTime(end_date, end_time_obj))
    
    def get_data(self):
        """Get the dialog data."""
        start_time = self.start_edit.dateTime().toPython()
        end_time = self.end_edit.dateTime().toPython()
        
        data = {
            "title": self.title_edit.text(),
            "description": self.desc_edit.toPlainText(),
            "event_type": self.type_combo.currentText(),
            "start_time": start_time,
            "end_time": end_time,
            "is_all_day": False,
            "color": "#3788d8"  # Default blue
        }
        
        # If editing, preserve ID
        if self.event and "id" in self.event:
            data["id"] = self.event["id"]
        
        return data

class CalendarPanel(QWidget):
    """
    Panel for displaying and managing calendar events.
    """
    
    def __init__(self, calendar_controller, parent=None):
        """
        Initialize the calendar panel.
        
        Args:
            calendar_controller: CalendarController instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.calendar_controller = calendar_controller
        self.current_events = []
        
        # Setup UI
        self._setup_ui()
        
        # Load initial events
        self._load_events()
        
        logger.info("Calendar panel initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # Add toolbar actions
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addSeparator()
        
        today_btn = QPushButton("Today")
        today_btn.clicked.connect(self._go_to_today)
        toolbar.addWidget(today_btn)
        
        toolbar.addSeparator()
        
        # Re-enable the New Event button
        new_event_btn = QPushButton("New Event")
        new_event_btn.clicked.connect(self._add_event)
        toolbar.addWidget(new_event_btn)
        
        toolbar.addSeparator()
        
        import_btn = QPushButton("Import Due Dates")
        import_btn.clicked.connect(self._import_due_dates)
        toolbar.addWidget(import_btn)
        
        layout.addWidget(toolbar)
        
        # Create splitter for calendar and events list
        splitter = QSplitter(Qt.Horizontal)
        
        # Create calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self._on_date_selected)
        splitter.addWidget(self.calendar)
        
        # Create events list widget
        self.events_list = QListWidget()
        self.events_list.setSelectionMode(QListWidget.SingleSelection)
        self.events_list.itemDoubleClicked.connect(self._on_event_double_clicked)
        self.events_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.events_list.customContextMenuRequested.connect(self._show_context_menu)
        self.events_list.setMinimumWidth(300)
        splitter.addWidget(self.events_list)
        
        # Set splitter sizes
        splitter.setSizes([400, 300])
        
        layout.addWidget(splitter, 1)
        
        self.setLayout(layout)
    
    def refresh(self):
        """Refresh the panel's content."""
        self._load_events()
    
    def _load_events(self):
        """Load events for the selected date range."""
        try:
            selected_date = self.calendar.selectedDate().toPython()
            start_date = datetime(selected_date.year, selected_date.month, 1)
            
            # Get the last day of the month
            if selected_date.month == 12:
                end_date = datetime(selected_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(selected_date.year, selected_date.month + 1, 1) - timedelta(days=1)
            
            # Load events from controller
            events = self.calendar_controller.get_events(start_date, end_date)
            
            # Store events
            self.current_events = events
            
            # Update days with events
            self._highlight_days_with_events(events, selected_date.month, selected_date.year)
            
            # Display events for selected day
            self._display_events_for_day(selected_date)
            
            logger.info(f"Loaded events for {start_date} to {end_date}")
        except Exception as e:
            logger.error(f"Error loading events: {str(e)}")
    
    def _highlight_days_with_events(self, events, month, year):
        """Highlight days with events in the calendar."""
        # TODO: Implement highlighting in the calendar widget
        # This would require custom formatting of calendar cells
        pass
    
    def _display_events_for_day(self, date):
        """Display events for the selected day."""
        try:
            # Clear list
            self.events_list.clear()
            
            # Get events for this day
            day_events = self.calendar_controller.get_events_by_day(date)
            
            if not day_events:
                # Add a "No events" item
                item = QListWidgetItem("No events for this day")
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                self.events_list.addItem(item)
                return
            
            # Sort events by start time
            day_events.sort(key=lambda e: e["start_time"])
            
            # Add events to list
            for event in day_events:
                # Format time
                if event["is_all_day"]:
                    time_str = "All day"
                else:
                    start_time = event["start_time"].strftime("%H:%M")
                    end_time = event["end_time"].strftime("%H:%M")
                    time_str = f"{start_time} - {end_time}"
                
                item = QListWidgetItem(f"{time_str}: {event['title']}")
                item.setData(Qt.UserRole, event["id"])
                
                # Set color indicator based on event color
                try:
                    color = QColor(event["color"])
                    item.setForeground(color)
                except:
                    pass
                
                self.events_list.addItem(item)
            
            logger.info(f"Displayed {len(day_events)} events for {date}")
        except Exception as e:
            logger.error(f"Error displaying events: {str(e)}")
    
    def _on_date_selected(self):
        """Handle date selection."""
        selected_date = self.calendar.selectedDate().toPython()
        logger.info(f"Selected date: {selected_date}")
        
        # Display events for the selected date
        self._display_events_for_day(selected_date)
    
    def _go_to_today(self):
        """Go to today's date."""
        self.calendar.setSelectedDate(QDate.currentDate())
    
    def _add_event(self):
        """Add a new event."""
        try:
            # Use the simple dialog to avoid crashes
            dialog = SimpleEventDialog(self)
            
            # Set initial date to current selection
            selected_date = self.calendar.selectedDate().toPython()
            now = datetime.now()
            
            # Create QDate and QTime objects and combine them
            date_obj = QDate(selected_date.year, selected_date.month, selected_date.day)
            start_time = QDateTime(date_obj, QTime(now.hour, now.minute))
            end_time = QDateTime(date_obj, QTime(now.hour, now.minute + 60 if now.minute <= 0 else now.minute, 0))
            
            dialog.start_edit.setDateTime(start_time)
            dialog.end_edit.setDateTime(end_time)
            
            if dialog.exec() == QDialog.Accepted:
                event_data = dialog.get_data()
                
                if event_data and event_data["title"]:
                    # Create event
                    logger.info(f"Creating event: {event_data['title']}")
                    event_id = self.calendar_controller.create_event(event_data)
                    
                    if event_id:
                        logger.info(f"Successfully created event with ID: {event_id}")
                        QMessageBox.information(self, "Success", "Event created successfully.")
                        self._load_events()
                    else:
                        logger.error("Failed to create event")
                        QMessageBox.warning(self, "Error", "Failed to create event.")
                else:
                    logger.warning("Event data missing or invalid")
                    QMessageBox.warning(self, "Error", "Please enter a title for the event.")
                
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            QMessageBox.critical(self, "Error", f"Could not create event: {str(e)}")
    
    def _edit_event(self, event_id):
        """Edit an existing event."""
        try:
            # Get event data
            event = self.calendar_controller.get_event(event_id)
            if not event:
                QMessageBox.warning(self, "Error", "Event not found.")
                return
            
            # Create dialog
            dialog = SimpleEventDialog(self, event)
            
            # Show dialog
            if dialog.exec() == QDialog.Accepted:
                # Get updated data
                updated_data = dialog.get_data()
                
                if updated_data and updated_data["title"]:
                    # Update event
                    if self.calendar_controller.update_event(event_id, updated_data):
                        QMessageBox.information(self, "Success", "Event updated successfully.")
                        self._load_events()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to update event.")
                else:
                    QMessageBox.warning(self, "Error", "Please enter a title for the event.")
                
        except Exception as e:
            logger.error(f"Error editing event: {str(e)}")
            QMessageBox.critical(self, "Error", f"Could not edit event: {str(e)}")
    
    def _delete_event(self, event_id):
        """Delete an event."""
        try:
            # Confirm deletion
            if QMessageBox.question(
                self, 
                "Confirm Deletion", 
                "Are you sure you want to delete this event?",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.No:
                return
            
            # Delete event
            if self.calendar_controller.delete_event(event_id):
                QMessageBox.information(self, "Success", "Event deleted successfully.")
                
                # Refresh events
                self._load_events()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete event.")
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error deleting event: {str(e)}")
    
    def _on_event_double_clicked(self, item):
        """Handle double-click on event item."""
        event_id = item.data(Qt.UserRole)
        if event_id:
            self._edit_event(event_id)
    
    def _show_context_menu(self, position):
        """Show context menu for events list."""
        try:
            item = self.events_list.itemAt(position)
            if not item:
                return
            
            event_id = item.data(Qt.UserRole)
            if not event_id:
                return
            
            # Create context menu
            menu = QMenu(self)
            
            edit_action = QAction("Edit", self)
            edit_action.triggered.connect(lambda: self._edit_event(event_id))
            menu.addAction(edit_action)
            
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self._delete_event(event_id))
            menu.addAction(delete_action)
            
            # Show menu
            menu.exec(self.events_list.mapToGlobal(position))
        except Exception as e:
            logger.error(f"Error showing context menu: {str(e)}")
    
    def _import_due_dates(self):
        """Import due dates from boards."""
        try:
            # Confirm import
            if QMessageBox.question(
                self, 
                "Import Due Dates", 
                "Import due dates from Tasks, Claims, and other boards?",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.No:
                return
            
            total_imported = 0
            
            # Get all board names with items that have due dates
            boards_with_due_dates = [
                "Tasks", 
                "Claims",
                "Leads"
                # Add other boards as needed
            ]
            
            # Get main window for data controller
            main_window = self.parent()
            if main_window and hasattr(main_window, "controllers") and "data" in main_window.controllers:
                data_controller = main_window.controllers["data"]
                board_controller = main_window.controllers["board"]
                
                for board_name in boards_with_due_dates:
                    # Get board ID
                    board_id = board_controller.get_board_id(board_name)
                    if not board_id:
                        continue
                    
                    # Get items
                    items = data_controller.load_board_items(board_id)
                    
                    # Import events
                    count = self.calendar_controller.import_events_from_items(items, board_name)
                    total_imported += count
            
            if total_imported > 0:
                QMessageBox.information(
                    self, 
                    "Import Complete", 
                    f"Successfully imported {total_imported} due dates as events."
                )
                
                # Refresh events
                self._load_events()
            else:
                QMessageBox.information(
                    self, 
                    "Import Complete", 
                    "No due dates found to import."
                )
        except Exception as e:
            logger.error(f"Error importing due dates: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error importing due dates: {str(e)}") 