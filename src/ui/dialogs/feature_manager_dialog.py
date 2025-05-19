"""
Feature Manager Dialog
Allows users to enable/disable application features
"""

import logging
from typing import Dict, Any, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QWidget, QTreeWidget, QTreeWidgetItem, QCheckBox,
    QGroupBox, QFormLayout, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

# Try different import paths for flexibility
try:
    from utils.logger import setup_logger, get_logger
    from utils.feature_flags import feature_flags
except ImportError:
    try:
        from src.utils.logger import setup_logger, get_logger
        from src.utils.feature_flags import feature_flags
    except ImportError:
        import logging
        logger = logging.getLogger(__name__)

# Get logger
logger = logging.getLogger("monday_uploader.feature_manager")

try:
    from PySide6.QtWidgets import QDialog
except ImportError:
    QDialog = object  # fallback to a dummy base class if import fails

class FeatureManagerDialog(QDialog):
    """Dialog for managing feature flags."""
    
    # Signal emitted when features are changed
    features_changed = Signal()
    
    def __init__(self, parent=None):
        """Initialize the feature manager dialog."""
        super().__init__(parent)
        
        # Set window properties
        self.setWindowTitle("Feature Manager")
        self.setMinimumSize(600, 500)
        
        # Initialize variables
        self.feature_states = {}
        self.changes_made = False
        
        # Setup UI
        self._setup_ui()
        
        # Load feature flags
        self._load_feature_flags()

    def _setup_ui(self):
        """Setup the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        
        # Create features tab
        features_tab = QWidget()
        features_layout = QVBoxLayout(features_tab)
        
        # Create tree widget for features
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Feature", "Status"])
        self.tree_widget.setColumnWidth(0, 400)
        features_layout.addWidget(self.tree_widget)
        
        # Add tab
        self.tab_widget.addTab(features_tab, "Features")
        
        # Add tabs to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Help label
        help_label = QLabel(
            "Enable or disable features by checking the boxes. "
            "Some changes may require restarting the application."
        )
        help_label.setStyleSheet("color: gray;")
        main_layout.addWidget(help_label)
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        # Save button
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_btn)
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.close_btn)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)

    def _load_feature_flags(self):
        """Load feature flags from the feature flags module."""
        try:
            if not feature_flags:
                self._show_error("Feature flags module not available")
                return
            
            # Clear tree widget
            self.tree_widget.clear()
            
            # Get all feature flags
            all_flags = feature_flags.get_all_flags()
            
            # Create category items
            categories = {
                "core": QTreeWidgetItem(["Core Features", ""]),
                "client": QTreeWidgetItem(["Client Management", ""]),
                "field": QTreeWidgetItem(["Field Operations", ""]),
                "regulatory": QTreeWidgetItem(["Regulatory & Compliance", ""]),
                "technical": QTreeWidgetItem(["Technical", ""])
            }
            
            # Add categories to tree
            for category in categories.values():
                self.tree_widget.addTopLevelItem(category)
            
            # Create feature items
            for feature_name, enabled in all_flags.items():
                # Determine category
                category_item = None
                if "settlement" in feature_name or "dashboard" in feature_name or "ocr" in feature_name:
                    category_item = categories["core"]
                elif "client" in feature_name or "onboarding" in feature_name:
                    category_item = categories["client"]
                elif "map" in feature_name or "mobile" in feature_name or "voice" in feature_name:
                    category_item = categories["field"]
                elif "compliance" in feature_name or "deadline" in feature_name:
                    category_item = categories["regulatory"]
                else:
                    category_item = categories["technical"]
                
                # Create item
                feature_item = QTreeWidgetItem(category_item)
                feature_item.setText(0, self._format_feature_name(feature_name))
                feature_item.setData(0, Qt.UserRole, feature_name)
                
                # Create checkbox
                checkbox = QCheckBox()
                checkbox.setChecked(enabled)
                checkbox.stateChanged.connect(lambda state, feature=feature_name: self._on_feature_changed(feature, state))
                self.tree_widget.setItemWidget(feature_item, 1, checkbox)
                
                # Store initial state
                self.feature_states[feature_name] = enabled
            
            # Expand all categories
            self.tree_widget.expandAll()
            
            logger.info("Loaded feature flags")
            
        except Exception as e:
            logger.error(f"Error loading feature flags: {str(e)}")
            self._show_error(f"Error loading feature flags: {str(e)}")

    def _format_feature_name(self, feature_name: str) -> str:
        """Format feature name for display."""
        # Remove '_enabled' suffix
        if feature_name.endswith("_enabled"):
            feature_name = feature_name[:-8]
        
        # Replace underscores with spaces and capitalize
        return feature_name.replace("_", " ").title()

    def _on_feature_changed(self, feature_name: str, state: int):
        """Handle feature checkbox state change."""
        try:
            # Update internal state
            is_enabled = state == Qt.Checked
            
            # Check if changed from initial state
            if self.feature_states.get(feature_name) != is_enabled:
                self.changes_made = True
                self.save_btn.setEnabled(True)
            else:
                # Check if any feature has changed
                self.changes_made = any(
                    self.feature_states.get(name) != self._get_feature_state(name)
                    for name in self.feature_states
                )
                self.save_btn.setEnabled(self.changes_made)
            
        except Exception as e:
            logger.error(f"Error handling feature change: {str(e)}")

    def _get_feature_state(self, feature_name: str) -> bool:
        """Get current state of a feature from the UI."""
        try:
            # Find the item with this feature name
            for i in range(self.tree_widget.topLevelItemCount()):
                category_item = self.tree_widget.topLevelItem(i)
                for j in range(category_item.childCount()):
                    feature_item = category_item.child(j)
                    if feature_item.data(0, Qt.UserRole) == feature_name:
                        checkbox = self.tree_widget.itemWidget(feature_item, 1)
                        if checkbox and isinstance(checkbox, QCheckBox):
                            return checkbox.isChecked()
            
            return False
            
        except Exception as e:
            logger.error(f"Error getting feature state: {str(e)}")
            return False

    def _on_save(self):
        """Save feature flag changes."""
        try:
            if not feature_flags:
                self._show_error("Feature flags module not available")
                return
            
            # Collect changes
            changes = {}
            for feature_name in self.feature_states:
                new_state = self._get_feature_state(feature_name)
                if self.feature_states[feature_name] != new_state:
                    changes[feature_name] = new_state
            
            # Update feature flags
            for feature_name, enabled in changes.items():
                feature_flags.set_feature_enabled(feature_name, enabled)
            
            # Save changes
            feature_flags.save_flags()
            
            # Update internal state
            for feature_name, enabled in changes.items():
                self.feature_states[feature_name] = enabled
            
            # Update UI
            self.changes_made = False
            self.save_btn.setEnabled(False)
            
            # Emit signal
            self.features_changed.emit()
            
            # Show success message
            QMessageBox.information(
                self,
                "Changes Saved",
                f"Feature flag changes have been saved ({len(changes)} changes)."
            )
            
            logger.info(f"Saved {len(changes)} feature flag changes")
            
            # Accept dialog
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving feature flags: {str(e)}")
            self._show_error(f"Error saving feature flags: {str(e)}")

    def _on_reset(self):
        """Reset feature flags to default values."""
        try:
            if not feature_flags:
                self._show_error("Feature flags module not available")
                return
            
            # Confirm reset
            result = QMessageBox.question(
                self,
                "Confirm Reset",
                "Are you sure you want to reset all features to their default values?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if result == QMessageBox.Yes:
                # Reset to defaults
                feature_flags.reset_to_defaults()
                
                # Reload UI
                self._load_feature_flags()
                
                # Update state
                self.changes_made = True
                self.save_btn.setEnabled(True)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Reset Complete",
                    "All features have been reset to their default values. Click Save to apply these changes."
                )
                
                logger.info("Reset feature flags to defaults")
            
        except Exception as e:
            logger.error(f"Error resetting feature flags: {str(e)}")
            self._show_error(f"Error resetting feature flags: {str(e)}")

    def _show_error(self, message: str):
        """Show error message."""
        QMessageBox.critical(
            self,
            "Error",
            message
        ) 