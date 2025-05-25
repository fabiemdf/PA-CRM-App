"""
Items panel for displaying and managing board items.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView, QPushButton, 
    QToolBar, QHBoxLayout, QLabel, QComboBox, QMessageBox, QDialog,
    QLineEdit, QFormLayout, QDialogButtonBox, QMenu, QListWidget, QListWidgetItem,
    QScrollArea, QApplication
)
from PySide6.QtCore import Qt, Signal, Slot, QModelIndex, QSize, QAbstractTableModel
from PySide6.QtGui import QIcon, QAction, QColor, QBrush

from controllers.board_controller import BoardController
from controllers.data_controller import DataController
from utils.error_handling import handle_error, MondayError, ErrorCodes
from ui.dialogs.settlement_calculator_dialog import SettlementCalculatorDialog
from ui.dialogs.edit_item_dialog import EditItemDialog
from ui.dialogs.view_manager_dialog import ViewManagerDialog
import json

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
        if not index.isValid():
            return None
            
        if role == Qt.DisplayRole:
            item = self.items[index.row()]
            column = self.columns[index.column()]
            return str(item.get(column, ""))
            
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.columns[section].replace("_", " ").title()
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None
    
    def setItems(self, items):
        """Update the items and refresh the model."""
        self.beginResetModel()
        self.items = items
        self.update_columns()
        self.endResetModel()
    
    def sort(self, column, order):
        """Sort the items by the specified column."""
        if not self.items:
            return
            
        self.beginResetModel()
        
        # Get the column name
        column_name = self.columns[column]
        
        # Sort the items
        self.items.sort(
            key=lambda x: str(x.get(column_name, "")).lower(),
            reverse=(order == Qt.DescendingOrder)
        )
        
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

class ItemsPanel(QWidget):
    """
    Panel for displaying and managing board items.
    """
    
    # Signal emitted when an item is selected
    item_selected = Signal(str)
    
    def __init__(self, board_controller: BoardController, data_controller: DataController, parent=None):
        super().__init__(parent)
        
        # Store controllers
        self.board_controller = board_controller
        self.data_controller = data_controller
        
        # Store current state
        self.current_board_id = None
        self.current_board_name = None
        self.current_items = []
        self.current_view = None
        
        # Setup UI
        self._setup_ui()
        
        # Load boards
        self.refresh_boards()
        
        logger.info("Items panel initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(16, 16))
        
        # Add refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh)
        self.toolbar.addAction(refresh_action)
        
        # Add new item action
        new_action = QAction("New Item", self)
        new_action.triggered.connect(self.create_new_item)
        self.toolbar.addAction(new_action)
        
        # Add edit item action
        edit_action = QAction("Edit Item", self)
        edit_action.triggered.connect(self.edit_selected_item)
        self.toolbar.addAction(edit_action)
        
        # Add delete item action
        delete_action = QAction("Delete Item", self)
        delete_action.triggered.connect(self.delete_selected_item)
        self.toolbar.addAction(delete_action)
        
        # Add settlement calculator button (only for Claims board)
        self.settlement_action = QAction("Settlement Calculator", self)
        self.settlement_action.triggered.connect(self._open_settlement_calculator)
        self.settlement_action.setVisible(False)  # Hidden by default
        self.toolbar.addAction(self.settlement_action)
        
        layout.addWidget(self.toolbar)
        
        # Create header
        header_layout = QHBoxLayout()
        
        # Add board selector
        board_layout = QHBoxLayout()
        self.board_combo = QComboBox()
        self.board_combo.currentIndexChanged.connect(self._on_board_changed)
        board_layout.addWidget(QLabel("Board:"))
        board_layout.addWidget(self.board_combo)
        header_layout.addLayout(board_layout)
        
        # View management
        view_layout = QHBoxLayout()
        self.view_combo = QComboBox()
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        view_layout.addWidget(QLabel("View:"))
        view_layout.addWidget(self.view_combo)
        
        manage_view_btn = QPushButton("Manage Views")
        manage_view_btn.clicked.connect(self._manage_views)
        view_layout.addWidget(manage_view_btn)
        
        header_layout.addLayout(view_layout)
        layout.addLayout(header_layout)
        
        # Create filter bar
        filter_layout = QHBoxLayout()
        
        # Add search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.search_input)
        
        # Add column filter dropdown
        self.column_filter = QComboBox()
        self.column_filter.addItem("All Columns")
        self.column_filter.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.column_filter)
        
        # Add pagination controls
        pagination_layout = QHBoxLayout()
        
        self.page_size = QComboBox()
        self.page_size.addItems(["10", "25", "50", "100"])
        self.page_size.setCurrentText("25")
        self.page_size.currentTextChanged.connect(self._apply_filters)
        pagination_layout.addWidget(QLabel("Items per page:"))
        pagination_layout.addWidget(self.page_size)
        
        self.prev_page = QPushButton("Previous")
        self.prev_page.clicked.connect(self._previous_page)
        pagination_layout.addWidget(self.prev_page)
        
        self.page_label = QLabel("Page 1")
        pagination_layout.addWidget(self.page_label)
        
        self.next_page = QPushButton("Next")
        self.next_page.clicked.connect(self._next_page)
        pagination_layout.addWidget(self.next_page)
        
        filter_layout.addLayout(pagination_layout)
        
        layout.addLayout(filter_layout)
        
        # Create table view
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.doubleClicked.connect(self.edit_selected_item)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)
        
        # Set minimum and maximum column widths
        self.table_view.horizontalHeader().setMinimumSectionSize(100)
        self.table_view.horizontalHeader().setMaximumSectionSize(300)
        
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
            board_name = self.board_controller.get_board_name(board_id) or "Unknown"
            
            # Update current board
            self.current_board_id = board_id
            self.current_board_name = board_name
            
            # Update board combo box
            index = self.board_combo.findData(board_id)
            if index >= 0:
                self.board_combo.setCurrentIndex(index)
            
            # Show/hide settlement calculator button based on board type
            self.settlement_action.setVisible(self.current_board_name == "Claims")
            
            # Load items
            items = self.data_controller.load_board_items(board_id)
            
            # Store items
            self.current_items = items
            
            # Update column filter dropdown
            self.column_filter.clear()
            self.column_filter.addItem("All Columns")
            if items:
                for col in self.table_model.columns:
                    self.column_filter.addItem(col)
            
            # Load views
            self._load_views()
            
            # Reset pagination
            self.current_page = 1
            self._apply_filters()
            
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
    
    def _open_settlement_calculator(self):
        """Open the settlement calculator dialog."""
        # Get selected item
        selected_items = self.table_view.selectedIndexes()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Claim Selected",
                "Please select a claim to calculate settlement for."
            )
            return
        
        # Get item data
        index = selected_items[0]
        item = self.current_items[index.row()]
        
        # Get policy controller from parent window
        policy_controller = None
        if hasattr(self.parent(), "controllers") and "policy" in self.parent().controllers:
            policy_controller = self.parent().controllers["policy"]
        
        # Create and show settlement calculator dialog
        dialog = SettlementCalculatorDialog(policy_controller, item.get("id"), self)
        
        # Pre-fill policy data from claim
        if item:
            # Set policy number
            if "policy_number" in item:
                dialog.policy_number.setText(str(item["policy_number"]))
            
            # Set carrier
            if "insurance_company" in item:
                dialog.carrier.setText(str(item["insurance_company"]))
            
            # Set coverage values
            if "insured_amount" in item:
                dialog.coverage_a.setText(str(item["insured_amount"]))
            
            # Set deductible if available
            if "deductible" in item:
                dialog.deductible.setText(str(item["deductible"]))
            
            # Set initial offer if available
            if "initial_offer" in item:
                dialog.negotiation_adjustment.setValue(float(item["initial_offer"]))
        
        if dialog.exec():
            # Refresh items to show updated settlement data
            self.refresh()
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle item double click."""
        # Get item data
        item_data = item.data(Qt.UserRole)
        
        # Emit signal
        self.item_selected.emit(item_data["id"])
    
    def _apply_filters(self):
        """Apply current filters and update the table view."""
        if not self.current_items:
            return
            
        # Get filter text and column
        filter_text = self.search_input.text().lower()
        filter_column = self.column_filter.currentText()
        
        # Filter items
        filtered_items = []
        for item in self.current_items:
            if filter_text:
                if filter_column == "All Columns":
                    # Search in all columns
                    if any(str(value).lower().find(filter_text) != -1 
                          for value in item.values()):
                        filtered_items.append(item)
                else:
                    # Search in specific column
                    value = str(item.get(filter_column, "")).lower()
                    if value.find(filter_text) != -1:
                        filtered_items.append(item)
            else:
                filtered_items.append(item)
        
        # Get page size
        page_size = int(self.page_size.currentText())
        
        # Calculate total pages
        total_items = len(filtered_items)
        total_pages = (total_items + page_size - 1) // page_size
        
        # Ensure current page is valid
        if not hasattr(self, 'current_page'):
            self.current_page = 1
        self.current_page = max(1, min(self.current_page, total_pages))
        
        # Get items for current page
        start_idx = (self.current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        page_items = filtered_items[start_idx:end_idx]
        
        # Update table
        self.table_model.setItems(page_items)
        
        # Apply view settings if we have a current view
        if self.current_view:
            try:
                # Get column order and hidden columns from view
                column_order = json.loads(self.current_view.column_order or '[]')
                hidden_columns = json.loads(self.current_view.hidden_columns or '[]')
                
                # Hide columns that should be hidden
                for i in range(self.table_model.columnCount()):
                    column_name = self.table_model.columns[i]
                    if column_name in hidden_columns:
                        self.table_view.hideColumn(i)
                    else:
                        self.table_view.showColumn(i)
                
                # Reorder columns if we have a specific order
                if column_order:
                    # Create a mapping of column names to their current indices
                    column_indices = {name: i for i, name in enumerate(self.table_model.columns)}
                    
                    # Move columns to their new positions
                    for new_pos, col_name in enumerate(column_order):
                        if col_name in column_indices:
                            current_pos = column_indices[col_name]
                            if current_pos != new_pos:
                                self.table_view.horizontalHeader().moveSection(current_pos, new_pos)
            except Exception as e:
                logger.error(f"Error applying view settings: {str(e)}")
        
        # Update pagination controls
        self.page_label.setText(f"Page {self.current_page} of {total_pages}")
        self.prev_page.setEnabled(self.current_page > 1)
        self.next_page.setEnabled(self.current_page < total_pages)
        
        # Set column widths based on content
        self.table_view.resizeColumnsToContents()
        
        # Set minimum and maximum column widths
        for i in range(self.table_model.columnCount()):
            width = self.table_view.columnWidth(i)
            self.table_view.setColumnWidth(i, max(min(width, 300), 100))
    
    def _previous_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._apply_filters()
    
    def _next_page(self):
        """Go to next page."""
        page_size = int(self.page_size.currentText())
        total_items = len(self.current_items)
        total_pages = (total_items + page_size - 1) // page_size
        
        if self.current_page < total_pages:
            self.current_page += 1
            self._apply_filters()
    
    def _load_views(self):
        """Load available views for the current board."""
        try:
            views = self.data_controller.get_board_views(self.current_board_id)
            
            self.view_combo.clear()
            self.view_combo.addItem("Default View")
            
            for view in views:
                self.view_combo.addItem(view.name, view)
                
            # Select default view
            default_view = next((v for v in views if v.is_default), None)
            if default_view:
                index = self.view_combo.findText(default_view.name)
                if index >= 0:
                    self.view_combo.setCurrentIndex(index)
        except Exception as e:
            logger.error(f"Error loading views: {str(e)}")
            
    def _on_view_changed(self, index):
        """Handle view selection change."""
        if index <= 0:  # Default view
            self.current_view = None
            self._apply_filters()
            return
            
        view = self.view_combo.currentData()
        if view:
            self.current_view = view
            self._apply_filters()
            
    def _manage_views(self):
        """Open view management dialog."""
        # Get current columns from table model
        current_columns = self.table_model.columns if self.table_model else []
        
        dialog = ViewManagerDialog(
            self,
            self.current_board_id,
            current_columns,
            self.current_view
        )
        dialog.view_saved.connect(self._save_view)
        dialog.exec()
        
    def _save_view(self, view_config_json):
        """Save a new view configuration."""
        try:
            view_config = json.loads(view_config_json)
            
            # Create or update view
            if self.current_view:
                view = self.current_view
            else:
                view = self.data_controller.create_board_view(self.current_board_id)
                
            view.name = view_config['name']
            view.column_order = json.dumps(view_config['column_order'])
            view.hidden_columns = json.dumps(view_config['hidden_columns'])
            view.column_widths = json.dumps(view_config['column_widths'])
            
            self.data_controller.save_board_view(view)
            self._load_views()
            
            # Select the new/updated view
            index = self.view_combo.findText(view.name)
            if index >= 0:
                self.view_combo.setCurrentIndex(index)
                
        except Exception as e:
            logger.error(f"Error saving view: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save view: {str(e)}")
    
    def _on_board_changed(self, index):
        """Handle board selection change."""
        if index < 0:
            return
            
        board_id = self.board_combo.currentData()
        if board_id:
            self.load_board_items(board_id)
            
    def refresh_boards(self):
        """Refresh the boards list."""
        try:
            # Get boards from controller
            boards = self.board_controller.get_boards()
            
            # Update combo box
            self.board_combo.clear()
            for board in boards:
                self.board_combo.addItem(board['name'], board['id'])
                
            # Select current board if any
            if self.current_board_id:
                index = self.board_combo.findData(self.current_board_id)
                if index >= 0:
                    self.board_combo.setCurrentIndex(index)
                    
        except Exception as e:
            logger.error(f"Error refreshing boards: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to refresh boards: {str(e)}"
            ) 