"""
Feature flag management dialog.
Allows administrators to enable/disable features at runtime.
"""

import logging
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QCheckBox, QMessageBox,
    QGroupBox, QFormLayout, QComboBox, QHeaderView, QTabWidget
)

from utils.feature_flags import feature_flags

logger = logging.getLogger("monday_uploader.feature_manager")

# Feature categories for organization
FEATURE_CATEGORIES = {
    "Core": [
        "settlement_calculator_enabled",
        "analytics_dashboard_enabled",
        "document_ocr_enabled",
        "timeline_visualization_enabled",
    ],
    "Client Management": [
        "client_portal_enabled",
        "client_updates_enabled",
        "client_onboarding_enabled",
    ],
    "Field Operations": [
        "map_integration_enabled",
        "voice_notes_enabled",
    ],
    "Regulatory": [
        "policy_analysis_enabled",
        "compliance_checklist_enabled",
        "deadline_tracker_enabled",
    ],
    "Technical": [
        "cloud_sync_enabled",
        "ai_assistant_enabled",
        "weather_tracking_enabled",
    ]
}

# Human-readable names for features
FEATURE_NAMES = {
    "settlement_calculator_enabled": "Settlement Calculator",
    "analytics_dashboard_enabled": "Analytics Dashboard",
    "document_ocr_enabled": "Document OCR & Classification",
    "timeline_visualization_enabled": "Claim Timeline Visualization",
    "client_portal_enabled": "Client Portal",
    "client_updates_enabled": "Automated Client Updates",
    "client_onboarding_enabled": "Client Onboarding Workflow",
    "map_integration_enabled": "Map Integration & Geolocation",
    "voice_notes_enabled": "Voice Notes Transcription",
    "policy_analysis_enabled": "Policy Analysis & Coverage Matching",
    "compliance_checklist_enabled": "Compliance Checklist Generator",
    "deadline_tracker_enabled": "Statute of Limitations Tracker",
    "cloud_sync_enabled": "Cloud Synchronization",
    "ai_assistant_enabled": "AI Assistant for Claims",
    "weather_tracking_enabled": "Weather & Catastrophe Tracking"
}

class FeatureManagerDialog(QDialog):
    """Dialog for managing feature flags."""
    
    features_changed = Signal()  # Signal emitted when feature flags are changed
    
    def __init__(self, parent=None):
        """Initialize the feature manager dialog."""
        super().__init__(parent)
        
        self.setWindowTitle("Feature Manager")
        self.setMinimumSize(700, 500)
        
        # Store original flag states for comparison
        self.original_flags = feature_flags.flags.copy()
        
        # Setup UI
        self._setup_ui()
        
        # Load current feature flag states
        self._load_features()
        
        logger.info("Feature manager dialog initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Tab 1: Feature Toggles
        features_tab = QWidget()
        features_layout = QVBoxLayout(features_tab)
        
        # Instructions
        features_layout.addWidget(QLabel(
            "Enable or disable features by checking the boxes below. "
            "Changes will take effect after application restart."
        ))
        
        # Create tree widget for feature flags
        self.feature_tree = QTreeWidget()
        self.feature_tree.setHeaderLabels(["Feature", "Status"])
        self.feature_tree.setColumnWidth(0, 300)
        self.feature_tree.setAlternatingRowColors(True)
        features_layout.addWidget(self.feature_tree)
        
        # Create bottom button layout
        button_layout = QHBoxLayout()
        
        # Enable all button
        self.enable_all_btn = QPushButton("Enable All")
        self.enable_all_btn.clicked.connect(self._on_enable_all)
        button_layout.addWidget(self.enable_all_btn)
        
        # Disable non-essential button
        self.disable_nonessential_btn = QPushButton("Disable Non-Essential")
        self.disable_nonessential_btn.clicked.connect(self._on_disable_nonessential)
        button_layout.addWidget(self.disable_nonessential_btn)
        
        # Reset to defaults button
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self._on_reset_defaults)
        button_layout.addWidget(self.reset_btn)
        
        features_layout.addLayout(button_layout)
        
        self.tab_widget.addTab(features_tab, "Feature Toggles")
        
        # Tab 2: Rollback Management
        rollback_tab = QWidget()
        rollback_layout = QVBoxLayout(rollback_tab)
        
        rollback_layout.addWidget(QLabel(
            "Manage feature rollbacks in case of issues. "
            "Use these tools to quickly disable problematic features."
        ))
        
        # Create rollback presets group
        rollback_group = QGroupBox("Emergency Rollback Presets")
        rollback_form = QFormLayout(rollback_group)
        
        # Rollback presets combo
        self.rollback_preset = QComboBox()
        self.rollback_preset.addItems([
            "Essential Features Only",
            "Stable Features Only (v1.0)",
            "Disable New Features",
            "Minimum Functionality",
            "Custom Configuration"
        ])
        rollback_form.addRow("Rollback Preset:", self.rollback_preset)
        
        # Apply preset button
        self.apply_preset_btn = QPushButton("Apply Preset")
        self.apply_preset_btn.clicked.connect(self._on_apply_preset)
        rollback_form.addRow("", self.apply_preset_btn)
        
        rollback_layout.addWidget(rollback_group)
        
        # Create issue tracker group
        issue_group = QGroupBox("Issue Tracking")
        issue_form = QFormLayout(issue_group)
        
        # Issue tracking combo
        self.issue_feature = QComboBox()
        for feature_name in sorted(FEATURE_NAMES.keys()):
            self.issue_feature.addItem(FEATURE_NAMES[feature_name], feature_name)
        issue_form.addRow("Problematic Feature:", self.issue_feature)
        
        # Disable feature button
        self.disable_feature_btn = QPushButton("Disable Feature & Log Issue")
        self.disable_feature_btn.clicked.connect(self._on_disable_feature)
        issue_form.addRow("", self.disable_feature_btn)
        
        rollback_layout.addWidget(issue_group)
        
        self.tab_widget.addTab(rollback_tab, "Rollback Management")
        
        main_layout.addWidget(self.tab_widget)
        
        # Create bottom buttons
        final_button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        final_button_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.clicked.connect(self._on_apply)
        final_button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(final_button_layout)
    
    def _load_features(self):
        """Load current feature flag states into tree widget."""
        self.feature_tree.clear()
        
        # Create category items
        category_items = {}
        for category_name in FEATURE_CATEGORIES:
            category_item = QTreeWidgetItem(self.feature_tree, [category_name, ""])
            category_item.setFlags(category_item.flags() | Qt.ItemIsAutoTristate)
            category_items[category_name] = category_item
        
        # Add features to categories
        for category_name, feature_flags_list in FEATURE_CATEGORIES.items():
            category_item = category_items[category_name]
            
            for feature_flag in feature_flags_list:
                # Get human-readable name and status
                display_name = FEATURE_NAMES.get(feature_flag, feature_flag)
                enabled = feature_flags.is_enabled(feature_flag)
                status = "Enabled" if enabled else "Disabled"
                
                # Create item
                feature_item = QTreeWidgetItem(category_item, [display_name, status])
                feature_item.setFlags(feature_item.flags() | Qt.ItemIsUserCheckable)
                feature_item.setCheckState(0, Qt.Checked if enabled else Qt.Unchecked)
                feature_item.setData(0, Qt.UserRole, feature_flag)
                
                # Set status color
                feature_item.setForeground(1, Qt.green if enabled else Qt.red)
        
        # Expand all categories
        self.feature_tree.expandAll()
    
    def _on_enable_all(self):
        """Enable all features."""
        for i in range(self.feature_tree.topLevelItemCount()):
            category_item = self.feature_tree.topLevelItem(i)
            
            for j in range(category_item.childCount()):
                feature_item = category_item.child(j)
                feature_item.setCheckState(0, Qt.Checked)
                feature_item.setText(1, "Enabled")
                feature_item.setForeground(1, Qt.green)
    
    def _on_disable_nonessential(self):
        """Disable non-essential features."""
        # Essential features that should remain enabled
        essential_features = [
            "settlement_calculator_enabled",
            "weather_tracking_enabled"
        ]
        
        for i in range(self.feature_tree.topLevelItemCount()):
            category_item = self.feature_tree.topLevelItem(i)
            
            for j in range(category_item.childCount()):
                feature_item = category_item.child(j)
                feature_flag = feature_item.data(0, Qt.UserRole)
                
                if feature_flag not in essential_features:
                    feature_item.setCheckState(0, Qt.Unchecked)
                    feature_item.setText(1, "Disabled")
                    feature_item.setForeground(1, Qt.red)
    
    def _on_reset_defaults(self):
        """Reset to default feature flag configuration."""
        for i in range(self.feature_tree.topLevelItemCount()):
            category_item = self.feature_tree.topLevelItem(i)
            
            for j in range(category_item.childCount()):
                feature_item = category_item.child(j)
                feature_flag = feature_item.data(0, Qt.UserRole)
                
                # Get default value
                default_enabled = feature_flags.DEFAULT_FLAGS.get(feature_flag, False)
                
                feature_item.setCheckState(0, Qt.Checked if default_enabled else Qt.Unchecked)
                feature_item.setText(1, "Enabled" if default_enabled else "Disabled")
                feature_item.setForeground(1, Qt.green if default_enabled else Qt.red)
    
    def _on_apply_preset(self):
        """Apply the selected rollback preset."""
        preset = self.rollback_preset.currentText()
        
        if preset == "Essential Features Only":
            # Enable only the most essential features
            essential_features = [
                "settlement_calculator_enabled",
                "weather_tracking_enabled"
            ]
            
            for feature_flag in feature_flags.flags:
                feature_flags.set_enabled(feature_flag, feature_flag in essential_features)
            
        elif preset == "Stable Features Only (v1.0)":
            # Enable only features that were in v1.0
            v1_features = [
                "weather_tracking_enabled"
            ]
            
            for feature_flag in feature_flags.flags:
                feature_flags.set_enabled(feature_flag, feature_flag in v1_features)
            
        elif preset == "Disable New Features":
            # Disable any features not in the original release
            stable_features = [
                "weather_tracking_enabled"
            ]
            
            for feature_flag in feature_flags.flags:
                if feature_flag not in stable_features:
                    feature_flags.set_enabled(feature_flag, False)
            
        elif preset == "Minimum Functionality":
            # Disable all features
            for feature_flag in feature_flags.flags:
                feature_flags.set_enabled(feature_flag, False)
        
        # Reload the feature list
        self._load_features()
        
        # Notify about changes
        QMessageBox.information(
            self,
            "Preset Applied",
            f"Applied preset '{preset}'. Changes will take effect after restart."
        )
    
    def _on_disable_feature(self):
        """Disable the selected problematic feature and log an issue."""
        feature_flag = self.issue_feature.currentData()
        feature_name = self.issue_feature.currentText()
        
        if feature_flag:
            # Disable the feature
            feature_flags.set_enabled(feature_flag, False)
            
            # Log the issue
            logger.warning(f"Feature '{feature_name}' disabled due to reported issues")
            
            # Reload the feature list
            self._load_features()
            
            # Notify about changes
            QMessageBox.information(
                self,
                "Feature Disabled",
                f"The feature '{feature_name}' has been disabled and the issue has been logged."
            )
    
    def _on_apply(self):
        """Apply changes to feature flags."""
        # Collect enabled features from tree
        enabled_features = set()
        
        for i in range(self.feature_tree.topLevelItemCount()):
            category_item = self.feature_tree.topLevelItem(i)
            
            for j in range(category_item.childCount()):
                feature_item = category_item.child(j)
                feature_flag = feature_item.data(0, Qt.UserRole)
                enabled = feature_item.checkState(0) == Qt.Checked
                
                if enabled:
                    enabled_features.add(feature_flag)
        
        # Update feature flags
        for feature_flag in feature_flags.flags:
            feature_flags.set_enabled(feature_flag, feature_flag in enabled_features)
        
        # Check if flags changed
        flags_changed = self.original_flags != feature_flags.flags
        
        if flags_changed:
            # Emit signal
            self.features_changed.emit()
            
            # Notify about restart
            QMessageBox.information(
                self,
                "Changes Applied",
                "Feature flag changes have been applied. Some changes may require an application restart."
            )
        
        # Accept dialog
        self.accept() 