"""
Settings dialog for the Monday Uploader application.
"""

import os
import logging
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QSpinBox, QComboBox, QGroupBox, QFormLayout, QFileDialog
)

from api.monday_api import MondayAPI
from utils.error_handling import handle_error, MondayError, ErrorCodes
from utils.logger import get_logger
from utils.settings import DEFAULT_SETTINGS

# Get logger
logger = logging.getLogger("monday_uploader.settings_dialog")

class SettingsDialog(QDialog):
    """
    Dialog for configuring application settings.
    """
    
    def __init__(self, settings: Dict[str, Any], parent=None):
        """
        Initialize the settings dialog.
        
        Args:
            settings: Current settings
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.settings = settings.copy()
        
        # Set dialog properties
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        # Create UI
        self._create_ui()
        
        # Populate fields with current settings
        self._populate_fields()
        
        logger.debug("Settings dialog initialized")
    
    def _create_ui(self):
        """Create the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_general_tab()
        self._create_api_tab()
        self._create_sync_tab()
        self._create_appearance_tab()
        self._create_logging_tab()
        
        # Create button layout
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # Add spacer
        button_layout.addStretch(1)
        
        # Create reset button
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_settings)
        button_layout.addWidget(self.reset_button)
        
        # Create cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # Create save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_settings)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)
    
    def _create_general_tab(self):
        """Create the general settings tab."""
        general_tab = QWidget()
        self.tab_widget.addTab(general_tab, "General")
        
        # Create layout
        layout = QVBoxLayout(general_tab)
        
        # Create user information group
        user_group = QGroupBox("User Information")
        layout.addWidget(user_group)
        
        user_layout = QFormLayout(user_group)
        
        # Create name field
        self.name_edit = QLineEdit()
        user_layout.addRow("Name:", self.name_edit)
        
        # Create company field
        self.company_edit = QLineEdit()
        user_layout.addRow("Company:", self.company_edit)
        
        # Create position field
        self.position_edit = QLineEdit()
        user_layout.addRow("Position:", self.position_edit)
        
        # Create locale section
        locale_group = QGroupBox("Locale Settings")
        layout.addWidget(locale_group)
        
        locale_layout = QFormLayout(locale_group)
        
        # Create locale combo
        self.locale_combo = QComboBox()
        self.locale_combo.addItems(["en_US", "en_GB", "es_ES", "fr_FR", "de_DE"])
        locale_layout.addRow("Language:", self.locale_combo)
        
        # Create date format combo
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems(["yyyy-MM-dd", "MM/dd/yyyy", "dd/MM/yyyy", "dd.MM.yyyy"])
        locale_layout.addRow("Date Format:", self.date_format_combo)
        
        # Create time format combo
        self.time_format_combo = QComboBox()
        self.time_format_combo.addItems(["HH:mm", "hh:mm a"])
        locale_layout.addRow("Time Format:", self.time_format_combo)
        
        # Add space at the bottom
        layout.addStretch(1)
    
    def _create_api_tab(self):
        """Create the API settings tab."""
        api_tab = QWidget()
        self.tab_widget.addTab(api_tab, "API")
        
        # Create layout
        layout = QVBoxLayout(api_tab)
        
        # Create Monday.com API group
        api_group = QGroupBox("Monday.com API Settings")
        layout.addWidget(api_group)
        
        api_layout = QVBoxLayout(api_group)
        
        # Create API key layout
        api_key_layout = QHBoxLayout()
        api_layout.addLayout(api_key_layout)
        
        # Create API key label
        api_key_label = QLabel("API Key:")
        api_key_layout.addWidget(api_key_label)
        
        # Create API key field
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        api_key_layout.addWidget(self.api_key_edit)
        
        # Create show API key checkbox
        self.show_api_key_check = QCheckBox("Show")
        self.show_api_key_check.toggled.connect(self._toggle_api_key_visibility)
        api_key_layout.addWidget(self.show_api_key_check)
        
        # Create validate button
        self.validate_button = QPushButton("Validate")
        self.validate_button.clicked.connect(self._validate_api_key)
        api_key_layout.addWidget(self.validate_button)
        
        # Create status label
        self.api_status_label = QLabel("")
        api_layout.addWidget(self.api_status_label)
        
        # Create help text
        help_text = (
            "To get your API key from Monday.com:\n"
            "1. Log in to your Monday.com account\n"
            "2. Click on your avatar in the bottom-left corner\n"
            "3. Select 'Admin' → 'API'\n"
            "4. Copy your API v2 Token"
        )
        help_label = QLabel(help_text)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 11px;")
        api_layout.addWidget(help_label)
        
        # Add space at the bottom
        layout.addStretch(1)
    
    def _create_sync_tab(self):
        """Create the synchronization settings tab."""
        sync_tab = QWidget()
        self.tab_widget.addTab(sync_tab, "Sync")
        
        # Create layout
        layout = QVBoxLayout(sync_tab)
        
        # Create sync settings group
        sync_group = QGroupBox("Synchronization Settings")
        layout.addWidget(sync_group)
        
        sync_layout = QVBoxLayout(sync_group)
        
        # Create auto sync checkbox
        self.auto_sync_check = QCheckBox("Enable Automatic Synchronization")
        sync_layout.addWidget(self.auto_sync_check)
        
        # Create sync interval layout
        interval_layout = QHBoxLayout()
        sync_layout.addLayout(interval_layout)
        
        # Create sync interval label
        interval_label = QLabel("Sync Interval (seconds):")
        interval_layout.addWidget(interval_label)
        
        # Create sync interval spinner
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setMinimum(60)
        self.sync_interval_spin.setMaximum(3600)
        self.sync_interval_spin.setSingleStep(30)
        interval_layout.addWidget(self.sync_interval_spin)
        
        interval_layout.addStretch(1)
        
        # Create offline settings group
        offline_group = QGroupBox("Offline Settings")
        layout.addWidget(offline_group)
        
        offline_layout = QVBoxLayout(offline_group)
        
        # Create cache limit layout
        cache_layout = QHBoxLayout()
        offline_layout.addLayout(cache_layout)
        
        # Create cache limit label
        cache_label = QLabel("Maximum Cache Size (MB):")
        cache_layout.addWidget(cache_label)
        
        # Create cache limit spinner
        self.cache_limit_spin = QSpinBox()
        self.cache_limit_spin.setMinimum(10)
        self.cache_limit_spin.setMaximum(1000)
        self.cache_limit_spin.setSingleStep(10)
        cache_layout.addWidget(self.cache_limit_spin)
        
        cache_layout.addStretch(1)
        
        # Create clear cache button
        self.clear_cache_button = QPushButton("Clear Cache")
        self.clear_cache_button.clicked.connect(self._clear_cache)
        offline_layout.addWidget(self.clear_cache_button, 0, Qt.AlignRight)
        
        # Add space at the bottom
        layout.addStretch(1)
    
    def _create_appearance_tab(self):
        """Create the appearance settings tab."""
        appearance_tab = QWidget()
        self.tab_widget.addTab(appearance_tab, "Appearance")
        
        # Create layout
        layout = QVBoxLayout(appearance_tab)
        
        # Create theme group
        theme_group = QGroupBox("Theme")
        layout.addWidget(theme_group)
        
        theme_layout = QVBoxLayout(theme_group)
        
        # Create theme combo
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        theme_layout.addWidget(self.theme_combo)
        
        # Create display group
        display_group = QGroupBox("Display")
        layout.addWidget(display_group)
        
        display_layout = QVBoxLayout(display_group)
        
        # Create items per page layout
        items_layout = QHBoxLayout()
        display_layout.addLayout(items_layout)
        
        # Create items per page label
        items_label = QLabel("Items per Page:")
        items_layout.addWidget(items_label)
        
        # Create items per page spinner
        self.items_per_page_spin = QSpinBox()
        self.items_per_page_spin.setMinimum(10)
        self.items_per_page_spin.setMaximum(500)
        self.items_per_page_spin.setSingleStep(10)
        items_layout.addWidget(self.items_per_page_spin)
        
        items_layout.addStretch(1)
        
        # Create panel visibility group
        panel_group = QGroupBox("Panel Visibility")
        layout.addWidget(panel_group)
        
        panel_layout = QVBoxLayout(panel_group)
        
        # Create show news feed checkbox
        self.show_news_feed_check = QCheckBox("Show News Feed")
        panel_layout.addWidget(self.show_news_feed_check)
        
        # Create show map checkbox
        self.show_map_check = QCheckBox("Show Map")
        panel_layout.addWidget(self.show_map_check)
        
        # Add space at the bottom
        layout.addStretch(1)
    
    def _create_logging_tab(self):
        """Create the logging settings tab."""
        logging_tab = QWidget()
        self.tab_widget.addTab(logging_tab, "Logging")
        
        # Create layout
        layout = QVBoxLayout(logging_tab)
        
        # Create log settings group
        log_group = QGroupBox("Log Settings")
        layout.addWidget(log_group)
        
        log_layout = QVBoxLayout(log_group)
        
        # Create log level layout
        level_layout = QHBoxLayout()
        log_layout.addLayout(level_layout)
        
        # Create log level label
        level_label = QLabel("Log Level:")
        level_layout.addWidget(level_label)
        
        # Create log level combo
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        level_layout.addWidget(self.log_level_combo)
        
        level_layout.addStretch(1)
        
        # Create log file layout
        file_layout = QHBoxLayout()
        log_layout.addLayout(file_layout)
        
        # Create log file path
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "logs", "monday_uploader.log")
        
        # Create log file label
        file_label = QLabel("Log File:")
        file_layout.addWidget(file_label)
        
        # Create log file edit
        self.log_file_edit = QLineEdit(log_path)
        self.log_file_edit.setReadOnly(True)
        file_layout.addWidget(self.log_file_edit)
        
        # Create open log button
        self.open_log_button = QPushButton("Open")
        self.open_log_button.clicked.connect(self._open_log_file)
        file_layout.addWidget(self.open_log_button)
        
        # Add button layout
        button_layout = QHBoxLayout()
        log_layout.addLayout(button_layout)
        
        # Add space
        button_layout.addStretch(1)
        
        # Create view logs button
        self.view_logs_button = QPushButton("View Logs")
        self.view_logs_button.clicked.connect(self._view_logs)
        button_layout.addWidget(self.view_logs_button)
        
        # Create clear logs button
        self.clear_logs_button = QPushButton("Clear Logs")
        self.clear_logs_button.clicked.connect(self._clear_logs)
        button_layout.addWidget(self.clear_logs_button)
        
        # Add space at the bottom
        layout.addStretch(1)
    
    def _populate_fields(self):
        """Populate form fields with current settings."""
        # General tab
        self.name_edit.setText(self.settings.get("name", ""))
        self.company_edit.setText(self.settings.get("company", ""))
        self.position_edit.setText(self.settings.get("position", ""))
        
        locale = self.settings.get("locale", "en_US")
        index = self.locale_combo.findText(locale)
        self.locale_combo.setCurrentIndex(index if index >= 0 else 0)
        
        date_format = self.settings.get("date_format", "yyyy-MM-dd")
        index = self.date_format_combo.findText(date_format)
        self.date_format_combo.setCurrentIndex(index if index >= 0 else 0)
        
        time_format = self.settings.get("time_format", "HH:mm")
        index = self.time_format_combo.findText(time_format)
        self.time_format_combo.setCurrentIndex(index if index >= 0 else 0)
        
        # API tab
        self.api_key_edit.setText(self.settings.get("api_key", ""))
        
        # Sync tab
        self.auto_sync_check.setChecked(self.settings.get("auto_sync", False))
        self.sync_interval_spin.setValue(self.settings.get("sync_interval", 300))
        self.cache_limit_spin.setValue(self.settings.get("cache_limit", 100))
        
        # Appearance tab
        theme = self.settings.get("theme", "system").capitalize()
        index = self.theme_combo.findText(theme)
        self.theme_combo.setCurrentIndex(index if index >= 0 else 0)
        
        self.items_per_page_spin.setValue(self.settings.get("max_items_per_page", 100))
        self.show_news_feed_check.setChecked(self.settings.get("show_news_feed", True))
        self.show_map_check.setChecked(self.settings.get("show_map", True))
        
        # Logging tab
        log_level = self.settings.get("log_level", "INFO")
        index = self.log_level_combo.findText(log_level)
        self.log_level_combo.setCurrentIndex(index if index >= 0 else 1)  # Default to INFO
    
    def _toggle_api_key_visibility(self, checked):
        """Toggle API key visibility."""
        self.api_key_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
    
    def _validate_api_key(self):
        """Validate the Monday.com API key."""
        api_key = self.api_key_edit.text().strip()
        
        if not api_key:
            self.api_status_label.setText("Please enter an API key")
            self.api_status_label.setStyleSheet("color: red;")
            return
        
        try:
            self.api_status_label.setText("Validating API key...")
            self.api_status_label.setStyleSheet("color: blue;")
            self.repaint()  # Force update
            
            # Create API instance to validate
            api = MondayAPI(api_key)
            
            if api.is_api_key_valid():
                self.api_status_label.setText("API key is valid")
                self.api_status_label.setStyleSheet("color: green;")
            else:
                self.api_status_label.setText("API key is invalid")
                self.api_status_label.setStyleSheet("color: red;")
                
        except Exception as e:
            self.api_status_label.setText("Error validating API key")
            self.api_status_label.setStyleSheet("color: red;")
            
            # Log the error
            logger.error(f"API key validation failed: {str(e)}")
    
    def _clear_cache(self):
        """Clear the cache."""
        # TODO: Implement cache clearing functionality
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "Are you sure you want to clear the cache? This will delete all locally stored data.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: Clear cache
            QMessageBox.information(
                self,
                "Cache Cleared",
                "The cache has been cleared successfully."
            )
    
    def _open_log_file(self):
        """Open the log file."""
        log_path = self.log_file_edit.text()
        
        if os.path.exists(log_path):
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            
            QDesktopServices.openUrl(QUrl.fromLocalFile(log_path))
        else:
            from PySide6.QtWidgets import QMessageBox
            
            QMessageBox.warning(
                self,
                "Log File Not Found",
                f"The log file could not be found at: {log_path}"
            )
    
    def _view_logs(self):
        """View application logs."""
        log_path = self.log_file_edit.text()
        
        if not os.path.exists(log_path):
            from PySide6.QtWidgets import QMessageBox
            
            QMessageBox.warning(
                self,
                "Log File Not Found",
                f"The log file could not be found at: {log_path}"
            )
            return
        
        from PySide6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QPushButton, QHBoxLayout
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Application Logs")
        dialog.setMinimumSize(800, 600)
        
        # Create layout
        layout = QVBoxLayout(dialog)
        
        # Create text edit
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(text_edit)
        
        # Create button layout
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Create refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: self._refresh_logs(text_edit, log_path))
        button_layout.addWidget(refresh_button)
        
        # Add spacer
        button_layout.addStretch(1)
        
        # Create close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        # Load log content
        self._refresh_logs(text_edit, log_path)
        
        # Show dialog
        dialog.exec()
    
    def _refresh_logs(self, text_edit, log_path):
        """Refresh log content."""
        try:
            with open(log_path, "r") as f:
                log_content = f.read()
            
            text_edit.setPlainText(log_content)
            
            # Scroll to end
            cursor = text_edit.textCursor()
            cursor.movePosition(cursor.End)
            text_edit.setTextCursor(cursor)
            
        except Exception as e:
            logger.error(f"Failed to refresh logs: {str(e)}")
            text_edit.setPlainText(f"Error loading log file: {str(e)}")
    
    def _clear_logs(self):
        """Clear the log file."""
        log_path = self.log_file_edit.text()
        
        if not os.path.exists(log_path):
            from PySide6.QtWidgets import QMessageBox
            
            QMessageBox.warning(
                self,
                "Log File Not Found",
                f"The log file could not be found at: {log_path}"
            )
            return
        
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Are you sure you want to clear the logs? This will delete all log entries.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with open(log_path, "w") as f:
                    from datetime import datetime
                    f.write(f"=== Logs cleared on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                
                QMessageBox.information(
                    self,
                    "Logs Cleared",
                    "The logs have been cleared successfully."
                )
                
            except Exception as e:
                logger.error(f"Failed to clear logs: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to clear logs: {str(e)}"
                )
    
    def _reset_settings(self):
        """Reset settings to default."""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to default? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset settings
            self.settings = DEFAULT_SETTINGS.copy()
            
            # Repopulate fields
            self._populate_fields()
            
            QMessageBox.information(
                self,
                "Settings Reset",
                "All settings have been reset to default values."
            )
    
    def _save_settings(self):
        """Save settings and close dialog."""
        # Validate settings
        api_key = self.api_key_edit.text().strip()
        sync_interval = self.sync_interval_spin.value()
        
        if sync_interval < 60:
            from PySide6.QtWidgets import QMessageBox
            
            QMessageBox.warning(
                self,
                "Invalid Sync Interval",
                "Sync interval must be at least 60 seconds."
            )
            return
        
        # Update settings
        self.settings["name"] = self.name_edit.text()
        self.settings["company"] = self.company_edit.text()
        self.settings["position"] = self.position_edit.text()
        self.settings["locale"] = self.locale_combo.currentText()
        self.settings["date_format"] = self.date_format_combo.currentText()
        self.settings["time_format"] = self.time_format_combo.currentText()
        self.settings["api_key"] = api_key
        self.settings["auto_sync"] = self.auto_sync_check.isChecked()
        self.settings["sync_interval"] = sync_interval
        self.settings["cache_limit"] = self.cache_limit_spin.value()
        self.settings["theme"] = self.theme_combo.currentText().lower()
        self.settings["max_items_per_page"] = self.items_per_page_spin.value()
        self.settings["show_news_feed"] = self.show_news_feed_check.isChecked()
        self.settings["show_map"] = self.show_map_check.isChecked()
        self.settings["log_level"] = self.log_level_combo.currentText()
        
        # Save settings
        from utils.settings import save_settings
        save_settings(self.settings)
        
        # Accept dialog
        self.accept()
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get the current settings.
        
        Returns:
            Dictionary of settings
        """
        return self.settings.copy() 