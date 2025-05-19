"""
Feedback dialog for collecting user feedback.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QTabWidget, QWidget,
    QFormLayout, QCheckBox, QGroupBox, QFileDialog
)
from PySide6.QtGui import QIcon

# Get logger
logger = logging.getLogger("monday_uploader.feedback_dialog")

class FeedbackDialog(QDialog):
    """Dialog for collecting user feedback."""
    
    def __init__(self, parent=None, feedback_controller=None):
        """Initialize the feedback dialog."""
        super().__init__(parent)
        self.feedback_controller = feedback_controller
        
        self.setWindowTitle("Send Feedback")
        self.setMinimumSize(600, 500)
        
        # Setup UI
        self._setup_ui()
        
        logger.info("Feedback dialog initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs for different feedback types
        self._create_bug_report_tab()
        self._create_crash_report_tab()
        self._create_feature_request_tab()
        self._create_performance_tab()
        self._create_ui_feedback_tab()
        self._create_compatibility_tab()
        self._create_security_tab()
        self._create_localization_tab()
        self._create_documentation_tab()
        self._create_general_feedback_tab()
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.submit_button = QPushButton("Submit Feedback")
        self.submit_button.clicked.connect(self._on_submit)
        button_layout.addWidget(self.submit_button)
        
        main_layout.addLayout(button_layout)
    
    def _create_bug_report_tab(self):
        """Create the bug report tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # What happened
        self.bug_summary = QLineEdit()
        layout.addRow("What happened?", self.bug_summary)
        
        # Steps to reproduce
        self.bug_steps = QTextEdit()
        layout.addRow("Steps to reproduce:", self.bug_steps)
        
        # Expected vs actual
        self.bug_expected = QTextEdit()
        layout.addRow("Expected behavior:", self.bug_expected)
        
        self.bug_actual = QTextEdit()
        layout.addRow("Actual behavior:", self.bug_actual)
        
        # Severity
        self.bug_severity = QComboBox()
        self.bug_severity.addItems(["Blocker", "Major", "Minor", "Cosmetic"])
        layout.addRow("Severity:", self.bug_severity)
        
        # Frequency
        self.bug_frequency = QComboBox()
        self.bug_frequency.addItems(["Always", "Sometimes", "Rare"])
        layout.addRow("Frequency:", self.bug_frequency)
        
        self.tab_widget.addTab(tab, "Bug Report")
    
    def _create_crash_report_tab(self):
        """Create the crash report tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Crash log
        self.crash_log = QTextEdit()
        layout.addRow("Crash log / stack trace:", self.crash_log)
        
        # Last action
        self.crash_last_action = QTextEdit()
        layout.addRow("Last action before crash:", self.crash_last_action)
        
        # Auto restart
        self.crash_auto_restart = QCheckBox("Application restarted automatically")
        layout.addRow("", self.crash_auto_restart)
        
        # System info
        self.crash_system_info = QTextEdit()
        layout.addRow("System information:", self.crash_system_info)
        
        self.tab_widget.addTab(tab, "Crash Report")
    
    def _create_feature_request_tab(self):
        """Create the feature request tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Feature name
        self.feature_name = QLineEdit()
        layout.addRow("Feature name:", self.feature_name)
        
        # Use case
        self.feature_use_case = QTextEdit()
        layout.addRow("Use case / benefit:", self.feature_use_case)
        
        # Priority
        self.feature_priority = QComboBox()
        self.feature_priority.addItems(["High", "Medium", "Low"])
        layout.addRow("Priority:", self.feature_priority)
        
        self.tab_widget.addTab(tab, "Feature Request")
    
    def _create_performance_tab(self):
        """Create the performance issue tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # What's slow
        self.perf_issue = QTextEdit()
        layout.addRow("What's slow or choppy?", self.perf_issue)
        
        # Timings
        self.perf_timings = QTextEdit()
        layout.addRow("Approximate timings:", self.perf_timings)
        
        # Environment
        self.perf_environment = QTextEdit()
        layout.addRow("Device / environment:", self.perf_environment)
        
        self.tab_widget.addTab(tab, "Performance Issue")
    
    def _create_ui_feedback_tab(self):
        """Create the UI/UX feedback tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Screen/flow
        self.ui_screen = QLineEdit()
        layout.addRow("Screen or flow:", self.ui_screen)
        
        # Issues
        self.ui_issues = QTextEdit()
        layout.addRow("What feels confusing or cluttered?", self.ui_issues)
        
        # Suggestions
        self.ui_suggestions = QTextEdit()
        layout.addRow("Suggestions:", self.ui_suggestions)
        
        # Screenshot
        screenshot_layout = QHBoxLayout()
        self.ui_screenshot_path = QLineEdit()
        self.ui_screenshot_path.setReadOnly(True)
        screenshot_layout.addWidget(self.ui_screenshot_path)
        
        self.ui_screenshot_btn = QPushButton("Browse...")
        self.ui_screenshot_btn.clicked.connect(self._on_browse_screenshot)
        screenshot_layout.addWidget(self.ui_screenshot_btn)
        
        layout.addRow("Screenshot:", screenshot_layout)
        
        self.tab_widget.addTab(tab, "UI/UX Feedback")
    
    def _create_compatibility_tab(self):
        """Create the compatibility report tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Platform
        self.comp_platform = QLineEdit()
        layout.addRow("Platform:", self.comp_platform)
        
        # Hardware
        self.comp_hardware = QTextEdit()
        layout.addRow("Hardware:", self.comp_hardware)
        
        # Browser
        self.comp_browser = QLineEdit()
        layout.addRow("Browser + version:", self.comp_browser)
        
        # Other apps
        self.comp_other_apps = QTextEdit()
        layout.addRow("Other running apps:", self.comp_other_apps)
        
        self.tab_widget.addTab(tab, "Compatibility Report")
    
    def _create_security_tab(self):
        """Create the security concern tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Description
        self.security_desc = QTextEdit()
        layout.addRow("Brief description:", self.security_desc)
        
        # Steps
        self.security_steps = QTextEdit()
        layout.addRow("Steps to demonstrate:", self.security_steps)
        
        # User data
        self.security_user_data = QTextEdit()
        layout.addRow("User data involved:", self.security_user_data)
        
        self.tab_widget.addTab(tab, "Security Concern")
    
    def _create_localization_tab(self):
        """Create the localization issue tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Language
        self.loc_language = QLineEdit()
        layout.addRow("Language:", self.loc_language)
        
        # Text
        self.loc_text = QTextEdit()
        layout.addRow("Exact text:", self.loc_text)
        
        # Fix
        self.loc_fix = QTextEdit()
        layout.addRow("Suggested fix:", self.loc_fix)
        
        self.tab_widget.addTab(tab, "Localization Issue")
    
    def _create_documentation_tab(self):
        """Create the documentation feedback tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Topic
        self.doc_topic = QLineEdit()
        layout.addRow("Documentation topic:", self.doc_topic)
        
        # Issues
        self.doc_issues = QTextEdit()
        layout.addRow("What's missing/unclear?", self.doc_issues)
        
        # Example
        self.doc_example = QTextEdit()
        layout.addRow("Expected example:", self.doc_example)
        
        self.tab_widget.addTab(tab, "Documentation Feedback")
    
    def _create_general_feedback_tab(self):
        """Create the general feedback tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Feedback
        self.general_feedback = QTextEdit()
        layout.addRow("Your feedback:", self.general_feedback)
        
        # Contact info
        self.general_contact = QLineEdit()
        layout.addRow("Contact info (optional):", self.general_contact)
        
        self.tab_widget.addTab(tab, "General Feedback")
    
    def _on_browse_screenshot(self):
        """Handle screenshot browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Screenshot",
            "",
            "Image Files (*.png *.jpg *.jpeg);;All Files (*)"
        )
        
        if file_path:
            self.ui_screenshot_path.setText(file_path)
    
    def _on_submit(self):
        """Handle submit button click."""
        try:
            # Get current tab
            current_tab = self.tab_widget.currentWidget()
            tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())
            
            # Collect feedback data
            feedback_data = {
                "type": tab_name,
                "timestamp": datetime.now().isoformat(),
                "app_version": "1.0.0",  # TODO: Get from app
                "user_id": None,  # TODO: Get from app if available
                "contact_info": self.general_contact.text() if hasattr(self, "general_contact") else None
            }
            
            # Add tab-specific data
            if tab_name == "Bug Report":
                feedback_data.update({
                    "summary": self.bug_summary.text(),
                    "steps": self.bug_steps.toPlainText(),
                    "expected": self.bug_expected.toPlainText(),
                    "actual": self.bug_actual.toPlainText(),
                    "severity": self.bug_severity.currentText(),
                    "frequency": self.bug_frequency.currentText()
                })
            elif tab_name == "Crash Report":
                feedback_data.update({
                    "crash_log": self.crash_log.toPlainText(),
                    "last_action": self.crash_last_action.toPlainText(),
                    "auto_restart": self.crash_auto_restart.isChecked(),
                    "system_info": self.crash_system_info.toPlainText()
                })
            elif tab_name == "Feature Request":
                feedback_data.update({
                    "name": self.feature_name.text(),
                    "use_case": self.feature_use_case.toPlainText(),
                    "priority": self.feature_priority.currentText()
                })
            elif tab_name == "Performance Issue":
                feedback_data.update({
                    "issue": self.perf_issue.toPlainText(),
                    "timings": self.perf_timings.toPlainText(),
                    "environment": self.perf_environment.toPlainText()
                })
            elif tab_name == "UI/UX Feedback":
                feedback_data.update({
                    "screen": self.ui_screen.text(),
                    "issues": self.ui_issues.toPlainText(),
                    "suggestions": self.ui_suggestions.toPlainText(),
                    "screenshot": self.ui_screenshot_path.text()
                })
            elif tab_name == "Compatibility Report":
                feedback_data.update({
                    "platform": self.comp_platform.text(),
                    "hardware": self.comp_hardware.toPlainText(),
                    "browser": self.comp_browser.text(),
                    "other_apps": self.comp_other_apps.toPlainText()
                })
            elif tab_name == "Security Concern":
                feedback_data.update({
                    "description": self.security_desc.toPlainText(),
                    "steps": self.security_steps.toPlainText(),
                    "user_data": self.security_user_data.toPlainText()
                })
            elif tab_name == "Localization Issue":
                feedback_data.update({
                    "language": self.loc_language.text(),
                    "text": self.loc_text.toPlainText(),
                    "fix": self.loc_fix.toPlainText()
                })
            elif tab_name == "Documentation Feedback":
                feedback_data.update({
                    "topic": self.doc_topic.text(),
                    "issues": self.doc_issues.toPlainText(),
                    "example": self.doc_example.toPlainText()
                })
            elif tab_name == "General Feedback":
                feedback_data.update({
                    "feedback": self.general_feedback.toPlainText()
                })
            
            # TODO: Send feedback data to controller
            if self.feedback_controller:
                success = self.feedback_controller.submit_feedback(feedback_data)
                if not success:
                    logger.error("Failed to save feedback.")
            else:
                logger.warning("No feedback controller provided; feedback not saved.")
            logger.info(f"Feedback submitted: {feedback_data}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            # TODO: Show error message 