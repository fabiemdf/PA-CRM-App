"""
Items panel for displaying and managing board items.
"""

import logging
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView, QPushButton, 
    QToolBar, QHBoxLayout, QLabel, QComboBox, QMessageBox, QDialog,
    QLineEdit, QFormLayout, QDialogButtonBox, QMenu
)
from PySide6.QtCore import Qt, Signal, Slot, QModelIndex, QSize, QAbstractTableModel
from PySide6.QtGui import QIcon, QAction

# Get logger
logger = logging.getLogger("monday_uploader.items_panel")

class ItemsTableModel(QAbstractTableModel):
    """Table model for displaying board items."""
    
    def __init__(self, items=None):
        super().__init__()
        self.items = items or []
        self.columns = []
        self.update_columns()
    
    def update_columns(self):
        """Update column definitions based on items."""
        if not self.items:
            self.columns = []
            return
            
        # Get all unique keys from items
        all_keys = set()
        for item in self.items:
            all_keys.update(item.keys())
            
        # Always put these columns first if they exist
        preferred_columns = ["id", "name", "status", "created_at", "owner"]
        
        # Build columns list
        columns = []
        
        # First add the preferred columns
        for col in preferred_columns:
            if col in all_keys:
                columns.append(col)
                all_keys.remove(col)
                
        # Add any remaining columns
        columns.extend(sorted(all_keys))
        
        self.columns = columns
    
    def rowCount(self, parent=None):
        return len(self.items)
    
    def columnCount(self, parent=None):
        return len(self.columns)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.items)):
            return None
            
        item = self.items[index.row()]
        column = self.columns[index.column()]
        
        if role == Qt.DisplayRole:
            # Return string representation of the value
            value = item.get(column, "")
            return str(value)
            
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            # Convert column name to title case for display
            return self.columns[section].replace("_", " ").title()
            
        return super().headerData(section, orientation, role)
    
    def setItems(self, items):
        """Update items and refresh model."""
        self.beginResetModel()
        self.items = items
        self.update_columns()
        self.endResetModel()
        
class CreateItemDialog(QDialog):
    """Dialog for creating a new item."""
    
    def __init__(self, board_name, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(f"Create New {board_name} Item")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Add name field
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        
        # Add status field
        self.status_combo = QComboBox()
        
        # Determine status options based on board type
        if board_name == "Clients":
            statuses = ["Active", "Inactive", "Lead", "Former"]
        elif board_name == "Tasks":
            statuses = ["Not Started", "In Progress", "Completed", "Blocked"]
        elif board_name == "Claims":
            statuses = ["New", "In Progress", "Approved", "Denied", "Closed"]
        else:
            statuses = ["New", "In Progress", "Completed"]
            
        self.status_combo.addItems(statuses)
        form_layout.addRow("Status:", self.status_combo)
        
        # Add custom fields based on board type
        if board_name == "Clients":
            self.company_edit = QLineEdit()
            form_layout.addRow("Company:", self.company_edit)
            
            self.email_edit = QLineEdit()
            form_layout.addRow("Email:", self.email_edit)
            
            self.phone_edit = QLineEdit()
            form_layout.addRow("Phone:", self.phone_edit)
            
        elif board_name == "Tasks":
            self.priority_combo = QComboBox()
            self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
            form_layout.addRow("Priority:", self.priority_combo)
            
        elif board_name == "Claims":
            self.claim_number_edit = QLineEdit()
            form_layout.addRow("Claim Number:", self.claim_number_edit)
            
            self.insured_edit = QLineEdit()
            form_layout.addRow("Insured:", self.insured_edit)
            
            self.amount_edit = QLineEdit()
            form_layout.addRow("Amount:", self.amount_edit)
        
        layout.addLayout(form_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Store board name
        self.board_name = board_name
    
    def get_item_data(self):
        """Get item data from form."""
        data = {
            "name": self.name_edit.text(),
            "status": self.status_combo.currentText(),
            "owner": "Current User"  # This would be the current user in a real app
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
        
        return data

class EditItemDialog(QDialog):
    """Dialog for editing an existing item."""
    
    def __init__(self, board_name, item_data, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(f"Edit {board_name} Item")
        self.setMinimumWidth(400)
        self.board_name = board_name
        self.item_data = item_data
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Add name field
        self.name_edit = QLineEdit(item_data.get("name", ""))
        form_layout.addRow("Name:", self.name_edit)
        
        # Add status field
        self.status_combo = QComboBox()
        
        # Determine status options based on board type
        if board_name == "Clients":
            statuses = ["Active", "Inactive", "Lead", "Former"]
        elif board_name == "Tasks":
            statuses = ["Not Started", "In Progress", "Completed", "Blocked"]
        elif board_name == "Claims":
            statuses = ["New", "In Progress", "Approved", "Denied", "Closed"]
        else:
            statuses = ["New", "In Progress", "Completed"]
            
        self.status_combo.addItems(statuses)
        current_status = item_data.get("status", "")
        if current_status in statuses:
            self.status_combo.setCurrentText(current_status)
            
        form_layout.addRow("Status:", self.status_combo)
        
        # Add custom fields based on board type
        if board_name == "Clients":
            self.company_edit = QLineEdit(item_data.get("company", ""))
            form_layout.addRow("Company:", self.company_edit)
            
            self.email_edit = QLineEdit(item_data.get("email", ""))
            form_layout.addRow("Email:", self.email_edit)
            
            self.phone_edit = QLineEdit(item_data.get("phone", ""))
            form_layout.addRow("Phone:", self.phone_edit)
            
        elif board_name == "Tasks":
            self.priority_combo = QComboBox()
            self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
            current_priority = item_data.get("priority", "")
            if current_priority in ["Low", "Medium", "High", "Critical"]:
                self.priority_combo.setCurrentText(current_priority)
            form_layout.addRow("Priority:", self.priority_combo)
            
        elif board_name == "Claims":
            self.claim_number_edit = QLineEdit(item_data.get("claim_number", ""))
            form_layout.addRow("Claim Number:", self.claim_number_edit)
            
            self.insured_edit = QLineEdit(item_data.get("insured", ""))
            form_layout.addRow("Insured:", self.insured_edit)
            
            self.amount_edit = QLineEdit(str(item_data.get("amount", "")))
            form_layout.addRow("Amount:", self.amount_edit)
        
        # Add any additional fields that are in the item_data but not covered above
        self.additional_edits = {}
        excluded_fields = ["id", "name", "status", "created_at", "owner", "company", "email", "phone", "priority", "claim_number", "insured", "amount"]
        for key, value in item_data.items():
            if key not in excluded_fields:
                edit = QLineEdit(str(value))
                form_layout.addRow(f"{key.replace('_', ' ').title()}:", edit)
                self.additional_edits[key] = edit
        
        layout.addLayout(form_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_item_data(self):
        """Get updated item data from form."""
        # Start with a copy of the original data to preserve any fields we don't edit
        data = dict(self.item_data)
        
        # Update common fields
        data["name"] = self.name_edit.text()
        data["status"] = self.status_combo.currentText()
        
        # Update custom fields based on board type
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
        
        # Update additional fields
        for key, edit in self.additional_edits.items():
            data[key] = edit.text()
        
        return data

class ItemsPanel(QWidget):
    """
    Panel for displaying and managing board items.
    """
    
    def __init__(self, data_controller, parent=None):
        """
        Initialize the items panel.
        
        Args:
            data_controller: DataController instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.data_controller = data_controller
        self.current_board_id = None
        self.current_board_name = None
        self.current_items = []
        
        # Setup UI
        self._setup_ui()
        
        logger.info("Items panel initialized")
    
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
        
        new_btn = QPushButton("New Item")
        new_btn.clicked.connect(self.create_new_item)
        toolbar.addWidget(new_btn)
        
        edit_btn = QPushButton("Edit Item")
        edit_btn.clicked.connect(self.edit_selected_item)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete Item")
        delete_btn.clicked.connect(self.delete_selected_item)
        toolbar.addWidget(delete_btn)
        
        layout.addWidget(toolbar)
        
        # Create header
        header_layout = QHBoxLayout()
        
        self.board_label = QLabel("No board selected")
        header_layout.addWidget(self.board_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Create table view
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.doubleClicked.connect(self.edit_selected_item)  # Add double-click to edit
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)  # Enable context menu
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)  # Connect context menu signal
        
        # Create table model
        self.table_model = ItemsTableModel()
        self.table_view.setModel(self.table_model)
        
        layout.addWidget(self.table_view, 1)
        
        self.setLayout(layout)
    
    def refresh(self):
        """Refresh the panel's content."""
        if self.current_board_id:
            self.load_board_items(self.current_board_id)
    
    def load_board_items(self, board_id: str):
        """
        Load items for a board.
        
        Args:
            board_id: Board ID
        """
        try:
            # Get board name
            board_name = "Unknown"
            for name, id in self.data_controller.board_controller.board_map.items():
                if id == board_id:
                    board_name = name
                    break
            
            # Update current board
            self.current_board_id = board_id
            self.current_board_name = board_name
            
            # Update header
            self.board_label.setText(f"Board: {board_name}")
            
            # Load items
            items = self.data_controller.load_board_items(board_id)
            
            # Store items
            self.current_items = items
            
            # Update table
            self.table_model.setItems(items)
            
            # Auto-resize columns to contents
            self.table_view.resizeColumnsToContents()
            
            logger.info(f"Loaded {len(items)} items for board {board_id}")
        except Exception as e:
            logger.error(f"Error loading board items: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load board items: {str(e)}"
            )
    
    def _show_context_menu(self, position):
        """Show context menu for table view."""
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return
            
        # Create context menu
        menu = QMenu(self)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_selected_item())
        menu.addAction(edit_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_selected_item())
        menu.addAction(delete_action)
        
        # Show menu
        menu.exec(self.table_view.mapToGlobal(position))
    
    def create_new_item(self):
        """Create a new item."""
        if not self.current_board_id or not self.current_board_name:
            QMessageBox.warning(
                self,
                "No Board Selected",
                "Please select a board first."
            )
            return
            
        # Open create dialog
        dialog = CreateItemDialog(self.current_board_name, self)
        if dialog.exec() == QDialog.Accepted:
            # Get item data
            item_data = dialog.get_item_data()
            
            # Create item
            new_item = self.data_controller.create_item(self.current_board_id, item_data)
            
            if new_item:
                # Add to table
                self.refresh()
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Item created successfully."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to create item."
                )
    
    def edit_selected_item(self):
        """Edit the selected item."""
        try:
            # Get selected index
            selected_indexes = self.table_view.selectionModel().selectedRows()
            if not selected_indexes:
                QMessageBox.warning(
                    self,
                    "No Item Selected",
                    "Please select an item to edit."
                )
                return
                
            # Get item data
            index = selected_indexes[0]
            item = self.current_items[index.row()]
            item_id = item.get("id")
            
            logger.info(f"Editing item with ID: {item_id}")
            
            # Open edit dialog
            dialog = EditItemDialog(self.current_board_name, item, self)
            if dialog.exec() == QDialog.Accepted:
                # Get updated item data
                updated_data = dialog.get_item_data()
                
                # Make sure we preserve the ID
                if "id" not in updated_data and item_id:
                    updated_data["id"] = item_id
                
                logger.info(f"Updated data: {updated_data}")
                
                # Update item in data controller
                result = self.data_controller.update_item(
                    self.current_board_id,
                    item_id,
                    updated_data
                )
                
                if result:
                    logger.info(f"Item updated successfully: {result}")
                    # Update local model with changes
                    self.current_items[index.row()] = updated_data
                    self.table_model.setItems(self.current_items)
                    
                    QMessageBox.information(
                        self,
                        "Success",
                        "Item updated successfully."
                    )
                else:
                    logger.error(f"Failed to update item with ID: {item_id}")
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to update item."
                    )
        except Exception as e:
            logger.error(f"Error editing item: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to edit item: {str(e)}"
            )
    
    def delete_selected_item(self):
        """Delete the selected item."""
        # Get selected index
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(
                self,
                "No Item Selected",
                "Please select an item to delete."
            )
            return
            
        # Confirm deletion
        if QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete the selected item?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.No:
            return
            
        # Get item ID
        index = selected_indexes[0]
        item = self.current_items[index.row()]
        item_id = item.get("id")
        
        if not item_id:
            QMessageBox.warning(
                self,
                "Error",
                "Item ID not found."
            )
            return
            
        # Delete item
        if self.data_controller.delete_item(self.current_board_id, item_id):
            # Remove from table
            self.refresh()
            
            QMessageBox.information(
                self,
                "Success",
                "Item deleted successfully."
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to delete item."
            )
    
    def _on_selection_changed(self):
        """Handle selection changes."""
        # This method could be used to update the UI based on selection
        # For example, enabling/disabling buttons
        pass 