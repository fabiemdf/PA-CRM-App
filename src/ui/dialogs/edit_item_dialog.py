from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QDialogButtonBox, QComboBox,
    QScrollArea, QWidget
)
from PySide6.QtCore import Qt
import json

class EditItemDialog(QDialog):
    """Dialog for editing an existing item."""
    
    def __init__(self, board_name, item_data, parent=None):
        super().__init__(parent)
        self.board_name = board_name
        self.item_data = item_data
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(f"Edit {self.board_name} Item")
        self.setMinimumWidth(400)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create widget to hold form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Add name field
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.item_data.get("name", ""))
        form_layout.addRow("Name:", self.name_edit)
        
        # Add status field
        self.status_combo = QComboBox()
        
        # Determine status options based on board type
        if self.board_name == "Clients":
            statuses = ["Active", "Inactive", "Lead", "Former"]
        elif self.board_name == "Tasks":
            statuses = ["Not Started", "In Progress", "Completed", "Blocked"]
        elif self.board_name == "Claims":
            statuses = ["New", "In Progress", "Approved", "Denied", "Closed"]
        else:
            statuses = ["New", "In Progress", "Completed"]
            
        self.status_combo.addItems(statuses)
        current_status = self.item_data.get("status", "")
        if current_status in statuses:
            self.status_combo.setCurrentText(current_status)
        form_layout.addRow("Status:", self.status_combo)
        
        # Add custom fields based on board type
        if self.board_name == "Clients":
            self.company_edit = QLineEdit()
            self.company_edit.setText(self.item_data.get("company", ""))
            form_layout.addRow("Company:", self.company_edit)
            
            self.email_edit = QLineEdit()
            self.email_edit.setText(self.item_data.get("email", ""))
            form_layout.addRow("Email:", self.email_edit)
            
            self.phone_edit = QLineEdit()
            self.phone_edit.setText(self.item_data.get("phone", ""))
            form_layout.addRow("Phone:", self.phone_edit)
            
        elif self.board_name == "Tasks":
            self.priority_combo = QComboBox()
            self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
            current_priority = self.item_data.get("priority", "")
            if current_priority in ["Low", "Medium", "High", "Critical"]:
                self.priority_combo.setCurrentText(current_priority)
            form_layout.addRow("Priority:", self.priority_combo)
            
        elif self.board_name == "Claims":
            self.claim_number_edit = QLineEdit()
            self.claim_number_edit.setText(self.item_data.get("claim_number", ""))
            form_layout.addRow("Claim Number:", self.claim_number_edit)
            
            self.insured_edit = QLineEdit()
            self.insured_edit.setText(self.item_data.get("insured", ""))
            form_layout.addRow("Insured:", self.insured_edit)
            
            self.amount_edit = QLineEdit()
            self.amount_edit.setText(str(self.item_data.get("amount", "")))
            form_layout.addRow("Amount:", self.amount_edit)
        
        # Add any additional fields from item_data
        for key, value in self.item_data.items():
            if key not in ["id", "name", "status", "created_at", "company", "email", "phone", 
                          "priority", "claim_number", "insured", "amount"]:
                field_edit = QLineEdit()
                field_edit.setText(str(value))
                form_layout.addRow(f"{key.replace('_', ' ').title()}:", field_edit)
                setattr(self, f"{key}_edit", field_edit)
        
        # Set the form widget as the scroll area's widget
        scroll.setWidget(form_widget)
        main_layout.addWidget(scroll)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def get_item_data(self):
        """Get item data from form."""
        data = {
            "name": self.name_edit.text(),
            "status": self.status_combo.currentText()
        }
        
        # Add custom fields based on board type
        if self.board_name == "Clients":
            data["company"] = self.company_edit.text()
            data["email"] = self.email_edit.text()
            data["phone"] = self.phone_edit.text()
            
        elif self.board_name == "Tasks":
            data["priority"] = self.priority_combo.currentText()
            
        elif self.board_name == "Claims":
            data["claim_number"] = self.claim_number_edit.text()
            data["insured"] = self.insured_edit.text()
            data["amount"] = self.amount_edit.text()
        
        # Add any additional fields
        for key in self.item_data.keys():
            if key not in ["id", "name", "status", "created_at", "company", "email", "phone", 
                          "priority", "claim_number", "insured", "amount"]:
                field_edit = getattr(self, f"{key}_edit", None)
                if field_edit:
                    data[key] = field_edit.text()
        
        return data 