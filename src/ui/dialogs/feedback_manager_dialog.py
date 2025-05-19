"""
Feedback manager dialog for viewing and managing feedback reports.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QWidget, QFormLayout, QMessageBox
)
from PySide6.QtGui import QIcon

# Get logger
logger = logging.getLogger("monday_uploader.feedback_manager")

class FeedbackManagerDialog(QDialog):
    """Dialog for managing feedback reports."""
    
    feedback_updated = Signal()  # Signal emitted when feedback is updated
    
    def __init__(self, feedback_controller, parent=None):
        """Initialize the feedback manager dialog."""
        super().__init__(parent)
        
        self.feedback_controller = feedback_controller
        self.current_feedback = None
        
        self.setWindowTitle("Feedback Manager")
        self.setMinimumSize(1000, 600)
        
        # Setup UI
        self._setup_ui()
        
        # Load feedback
        self._load_feedback()
        
        logger.info("Feedback manager dialog initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create filter bar
        filter_layout = QHBoxLayout()
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types", None)
        self.type_filter.addItems([
            "Bug Report", "Crash Report", "Feature Request",
            "Performance Issue", "UI/UX Feedback", "Compatibility Report",
            "Security Concern", "Localization Issue", "Documentation Feedback",
            "General Feedback"
        ])
        self.type_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.type_filter)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search feedback...")
        self.search_box.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_box)
        
        # Export button
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self._on_export)
        filter_layout.addWidget(self.export_button)
        
        main_layout.addLayout(filter_layout)
        
        # Create splitter for feedback list and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Create feedback list
        self.feedback_list = QTableWidget()
        self.feedback_list.setColumnCount(4)
        self.feedback_list.setHorizontalHeaderLabels(["Type", "Summary", "Date", "Status"])
        self.feedback_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.feedback_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.feedback_list.setSelectionMode(QTableWidget.SingleSelection)
        self.feedback_list.itemSelectionChanged.connect(self._on_feedback_selected)
        splitter.addWidget(self.feedback_list)
        
        # Create details panel
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        
        # Feedback details form
        form_layout = QFormLayout()
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["New", "In Progress", "Resolved", "Closed"])
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        form_layout.addRow("Status:", self.status_combo)
        
        self.response_text = QTextEdit()
        self.response_text.setPlaceholderText("Enter your response...")
        self.response_text.textChanged.connect(self._on_response_changed)
        form_layout.addRow("Response:", self.response_text)
        
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Internal notes...")
        self.notes_text.textChanged.connect(self._on_notes_changed)
        form_layout.addRow("Notes:", self.notes_text)
        
        details_layout.addLayout(form_layout)
        
        # Save button
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self._on_save)
        self.save_button.setEnabled(False)
        details_layout.addWidget(self.save_button)
        
        splitter.addWidget(details_panel)
        
        # Set splitter sizes
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
    
    def _load_feedback(self):
        """Load feedback from controller."""
        try:
            # Get feedback records
            feedback_records = self.feedback_controller.get_feedback()
            
            # Clear table
            self.feedback_list.setRowCount(0)
            
            # Add records to table
            for record in feedback_records:
                row = self.feedback_list.rowCount()
                self.feedback_list.insertRow(row)
                
                # Type
                self.feedback_list.setItem(row, 0, QTableWidgetItem(record["type"]))
                
                # Summary (use appropriate field based on type)
                summary = self._get_summary(record)
                self.feedback_list.setItem(row, 1, QTableWidgetItem(summary))
                
                # Date
                date = datetime.fromisoformat(record["timestamp"]).strftime("%Y-%m-%d %H:%M")
                self.feedback_list.setItem(row, 2, QTableWidgetItem(date))
                
                # Status
                status = record.get("status", "New")
                self.feedback_list.setItem(row, 3, QTableWidgetItem(status))
                
                # Store record data
                self.feedback_list.item(row, 0).setData(Qt.UserRole, record)
            
            logger.info(f"Loaded {len(feedback_records)} feedback records")
            
        except Exception as e:
            logger.error(f"Error loading feedback: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load feedback: {str(e)}"
            )
    
    def _get_summary(self, record: Dict[str, Any]) -> str:
        """Get summary text for feedback record."""
        feedback_type = record["type"]
        data = record["data"]
        
        if feedback_type == "Bug Report":
            return data.get("summary", "No summary")
        elif feedback_type == "Feature Request":
            return data.get("name", "No name")
        elif feedback_type == "UI/UX Feedback":
            return data.get("screen", "No screen specified")
        elif feedback_type == "General Feedback":
            return data.get("feedback", "No feedback")[:100] + "..."
        else:
            # For other types, try to find a suitable summary field
            for field in ["description", "issue", "topic", "text"]:
                if field in data:
                    return data[field][:100] + "..."
            return "No summary available"
    
    def _on_filter_changed(self):
        """Handle filter changes."""
        type_filter = self.type_filter.currentData()
        search_text = self.search_box.text().lower()
        
        # Show/hide rows based on filters
        for row in range(self.feedback_list.rowCount()):
            record = self.feedback_list.item(row, 0).data(Qt.UserRole)
            type_match = type_filter is None or record["type"] == type_filter
            text_match = not search_text or any(
                search_text in str(value).lower()
                for value in record.values()
            )
            self.feedback_list.setRowHidden(row, not (type_match and text_match))
    
    def _on_feedback_selected(self):
        """Handle feedback selection."""
        selected_items = self.feedback_list.selectedItems()
        if not selected_items:
            self.current_feedback = None
            self._clear_details()
            return
        
        # Get selected record
        row = selected_items[0].row()
        self.current_feedback = self.feedback_list.item(row, 0).data(Qt.UserRole)
        
        # Update details panel
        self.status_combo.setCurrentText(self.current_feedback.get("status", "New"))
        self.response_text.setText(self.current_feedback.get("response", ""))
        self.notes_text.setText(self.current_feedback.get("notes", ""))
    
    def _clear_details(self):
        """Clear details panel."""
        self.status_combo.setCurrentText("New")
        self.response_text.clear()
        self.notes_text.clear()
        self.save_button.setEnabled(False)
    
    def _on_status_changed(self):
        """Handle status change."""
        self.save_button.setEnabled(True)
    
    def _on_response_changed(self):
        """Handle response change."""
        self.save_button.setEnabled(True)
    
    def _on_notes_changed(self):
        """Handle notes change."""
        self.save_button.setEnabled(True)
    
    def _on_save(self):
        """Save feedback changes."""
        if not self.current_feedback:
            return
        
        try:
            # Update feedback record
            self.current_feedback.update({
                "status": self.status_combo.currentText(),
                "response": self.response_text.toPlainText(),
                "notes": self.notes_text.toPlainText(),
                "updated_at": datetime.now().isoformat()
            })
            
            # Save to database
            success = self.feedback_controller.update_feedback(self.current_feedback)
            
            if success:
                # Update table
                self._load_feedback()
                self.save_button.setEnabled(False)
                self.feedback_updated.emit()
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Feedback updated successfully"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to update feedback"
                )
            
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save feedback: {str(e)}"
            )
    
    def _on_export(self):
        """Export feedback to file."""
        try:
            # Get feedback type filter
            feedback_type = self.type_filter.currentData()
            
            # Get export file path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Feedback",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                # Export feedback
                success = self.feedback_controller.export_feedback(file_path, feedback_type)
                
                if success:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Feedback exported to {file_path}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to export feedback"
                    )
            
        except Exception as e:
            logger.error(f"Error exporting feedback: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export feedback: {str(e)}"
            ) 