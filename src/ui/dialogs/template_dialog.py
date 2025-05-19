"""
Template dialog for creating and managing templates.
"""

import logging
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QComboBox, QDialogButtonBox
)
from PySide6.QtCore import Qt

# Get logger
logger = logging.getLogger("monday_uploader.template_dialog")

class TemplateDialog(QDialog):
    """
    Dialog for creating and managing templates.
    """
    
    def __init__(self, session, parent=None):
        """
        Initialize the template dialog.
        
        Args:
            session: SQLAlchemy session
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.session = session
        
        # Setup UI
        self._setup_ui()
        
        logger.info("Template dialog initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Set window properties
        self.setWindowTitle("Template Creator")
        self.setMinimumSize(600, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create template name section
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Template Name:"))
        
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        
        layout.addLayout(name_layout)
        
        # Create template type section
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Template Type:"))
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Email", "Document", "Note"])
        type_layout.addWidget(self.type_combo)
        
        layout.addLayout(type_layout)
        
        # Create template content section
        layout.addWidget(QLabel("Template Content:"))
        
        self.content_edit = QTextEdit()
        layout.addWidget(self.content_edit)
        
        # Create buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def accept(self):
        """Handle dialog acceptance."""
        try:
            # Get values
            name = self.name_edit.text()
            template_type = self.type_combo.currentText()
            content = self.content_edit.toPlainText()
            
            if not name or not content:
                # Show error message
                logger.warning("Template name and content are required")
                return
            
            # In a real implementation, this would save the template to the database
            logger.info(f"Saving template: {name} ({template_type})")
            
            super().accept()
        except Exception as e:
            logger.error(f"Error saving template: {str(e)}")
    
    def reject(self):
        """Handle dialog rejection."""
        logger.info("Template dialog canceled")
        super().reject() 