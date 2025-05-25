from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QMenu, QWidget,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
import logging

from controllers.board_controller import BoardController
from utils.error_handling import handle_error, MondayError

logger = logging.getLogger(__name__)

class ItemManagerDialog(QDialog):
    """Dialog for managing items (rows) within a board."""
    
    item_updated = Signal(str)  # Signal emitted when items are modified
    
    def __init__(self, board_controller: BoardController, board_id: str, parent=None):
        super().__init__(parent)
        self.board_controller = board_controller
        self.board_id = board_id
        self.setup_ui()
        self.load_items()
        
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Item Manager")
        self.setMinimumSize(800, 600)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Items table
        self.items_table = QTableWidget()
        self.items_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.items_table.customContextMenuRequested.connect(self.show_item_context_menu)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("Items:"))
        layout.addWidget(self.items_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_item_btn = QPushButton("New Item")
        self.new_item_btn.clicked.connect(self.create_new_item)
        button_layout.addWidget(self.new_item_btn)
        
        self.edit_item_btn = QPushButton("Edit Item")
        self.edit_item_btn.clicked.connect(self.edit_selected_item)
        button_layout.addWidget(self.edit_item_btn)
        
        self.archive_item_btn = QPushButton("Archive Item")
        self.archive_item_btn.clicked.connect(self.archive_selected_items)
        button_layout.addWidget(self.archive_item_btn)
        
        self.delete_item_btn = QPushButton("Delete Item")
        self.delete_item_btn.clicked.connect(self.delete_selected_items)
        button_layout.addWidget(self.delete_item_btn)
        
        layout.addLayout(button_layout)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for common actions."""
        # Cut
        cut_action = QAction("Cut", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.cut_selected_items)
        self.addAction(cut_action)
        
        # Copy
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_selected_items)
        self.addAction(copy_action)
        
        # Paste
        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste_items)
        self.addAction(paste_action)
        
        # Delete
        delete_action = QAction("Delete", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self.delete_selected_items)
        self.addAction(delete_action)
        
    def load_items(self):
        """Load items into the table widget."""
        try:
            self.items_table.clear()
            items = self.board_controller.get_board_items(self.board_id)
            columns = self.board_controller.get_board_columns(self.board_id)
            
            # Setup table
            self.items_table.setRowCount(len(items))
            self.items_table.setColumnCount(len(columns))
            
            # Set headers
            headers = [col['title'] for col in columns]
            self.items_table.setHorizontalHeaderLabels(headers)
            
            # Fill data
            for row, item in enumerate(items):
                for col, column in enumerate(columns):
                    value = item.get(column['id'], '')
                    table_item = QTableWidgetItem(str(value))
                    table_item.setData(Qt.UserRole, item['id'])
                    self.items_table.setItem(row, col, table_item)
                    
        except Exception as e:
            handle_error(e, self, "Error loading items")
            
    def show_item_context_menu(self, position):
        """Show context menu for item operations."""
        menu = QMenu()
        
        edit_action = menu.addAction("Edit Item")
        edit_action.triggered.connect(self.edit_selected_item)
        
        menu.addSeparator()
        
        cut_action = menu.addAction("Cut")
        cut_action.triggered.connect(self.cut_selected_items)
        
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(self.copy_selected_items)
        
        paste_action = menu.addAction("Paste")
        paste_action.triggered.connect(self.paste_items)
        
        menu.addSeparator()
        
        archive_action = menu.addAction("Archive Item")
        archive_action.triggered.connect(self.archive_selected_items)
        
        delete_action = menu.addAction("Delete Item")
        delete_action.triggered.connect(self.delete_selected_items)
        
        menu.exec_(self.items_table.mapToGlobal(position))
        
    def get_selected_item_ids(self):
        """Get IDs of selected items."""
        selected_rows = set(item.row() for item in self.items_table.selectedItems())
        return [
            self.items_table.item(row, 0).data(Qt.UserRole)
            for row in selected_rows
        ]
        
    def create_new_item(self):
        """Create a new item."""
        try:
            # Create dialog for new item
            dialog = QDialog(self)
            dialog.setWindowTitle("New Item")
            layout = QVBoxLayout(dialog)
            
            # Add form fields based on columns
            columns = self.board_controller.get_board_columns(self.board_id)
            form_widget = QWidget()
            form_layout = QVBoxLayout(form_widget)
            
            for column in columns:
                field = self.create_field_for_column(column)
                if field:
                    form_layout.addWidget(field)
                    
            layout.addWidget(form_widget)
            
            # Add buttons
            buttons = QHBoxLayout()
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(dialog.accept)
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(dialog.reject)
            buttons.addWidget(ok_button)
            buttons.addWidget(cancel_button)
            layout.addLayout(buttons)
            
            if dialog.exec_() == QDialog.Accepted:
                # Collect values from form fields
                values = {}
                for i in range(form_layout.count()):
                    field = form_layout.itemAt(i).widget()
                    if hasattr(field, 'get_value'):
                        values[field.column_id] = field.get_value()
                        
                # Create item
                item_id = self.board_controller.create_item(self.board_id, values)
                if item_id:
                    self.load_items()
                    self.item_updated.emit(self.board_id)
                    QMessageBox.information(
                        self, "Success",
                        "Item created successfully."
                    )
        except Exception as e:
            handle_error(e, self, "Error creating item")
            
    def edit_selected_item(self):
        """Edit the selected item."""
        try:
            selected_ids = self.get_selected_item_ids()
            if not selected_ids:
                QMessageBox.warning(
                    self, "Warning", "Please select an item to edit."
                )
                return
                
            if len(selected_ids) > 1:
                QMessageBox.warning(
                    self, "Warning", "Please select only one item to edit."
                )
                return
                
            item_id = selected_ids[0]
            item = self.board_controller.get_item(self.board_id, item_id)
            
            # Create dialog for editing item
            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Item")
            layout = QVBoxLayout(dialog)
            
            # Add form fields based on columns
            columns = self.board_controller.get_board_columns(self.board_id)
            form_widget = QWidget()
            form_layout = QVBoxLayout(form_widget)
            
            for column in columns:
                field = self.create_field_for_column(column, item.get(column['id']))
                if field:
                    form_layout.addWidget(field)
                    
            layout.addWidget(form_widget)
            
            # Add buttons
            buttons = QHBoxLayout()
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(dialog.accept)
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(dialog.reject)
            buttons.addWidget(ok_button)
            buttons.addWidget(cancel_button)
            layout.addLayout(buttons)
            
            if dialog.exec_() == QDialog.Accepted:
                # Collect values from form fields
                values = {}
                for i in range(form_layout.count()):
                    field = form_layout.itemAt(i).widget()
                    if hasattr(field, 'get_value'):
                        values[field.column_id] = field.get_value()
                        
                # Update item
                if self.board_controller.update_item(self.board_id, item_id, values):
                    self.load_items()
                    self.item_updated.emit(self.board_id)
                    QMessageBox.information(
                        self, "Success",
                        "Item updated successfully."
                    )
        except Exception as e:
            handle_error(e, self, "Error editing item")
            
    def archive_selected_items(self):
        """Archive selected items."""
        try:
            selected_ids = self.get_selected_item_ids()
            if not selected_ids:
                QMessageBox.warning(
                    self, "Warning", "Please select items to archive."
                )
                return
                
            reply = QMessageBox.question(
                self, "Archive Items",
                f"Are you sure you want to archive {len(selected_ids)} item(s)?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                for item_id in selected_ids:
                    self.board_controller.archive_item(self.board_id, item_id)
                self.load_items()
                self.item_updated.emit(self.board_id)
                QMessageBox.information(
                    self, "Success",
                    f"{len(selected_ids)} item(s) archived successfully."
                )
        except Exception as e:
            handle_error(e, self, "Error archiving items")
            
    def delete_selected_items(self):
        """Delete selected items."""
        try:
            selected_ids = self.get_selected_item_ids()
            if not selected_ids:
                QMessageBox.warning(
                    self, "Warning", "Please select items to delete."
                )
                return
                
            reply = QMessageBox.warning(
                self, "Delete Items",
                f"Are you sure you want to delete {len(selected_ids)} item(s)? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                for item_id in selected_ids:
                    self.board_controller.delete_item(self.board_id, item_id)
                self.load_items()
                self.item_updated.emit(self.board_id)
                QMessageBox.information(
                    self, "Success",
                    f"{len(selected_ids)} item(s) deleted successfully."
                )
        except Exception as e:
            handle_error(e, self, "Error deleting items")
            
    def cut_selected_items(self):
        """Cut selected items to clipboard."""
        try:
            selected_ids = self.get_selected_item_ids()
            if not selected_ids:
                return
                
            # Copy items to clipboard
            self.copy_selected_items()
            
            # Delete items
            for item_id in selected_ids:
                self.board_controller.delete_item(self.board_id, item_id)
            self.load_items()
            self.item_updated.emit(self.board_id)
        except Exception as e:
            handle_error(e, self, "Error cutting items")
            
    def copy_selected_items(self):
        """Copy selected items to clipboard."""
        try:
            selected_ids = self.get_selected_item_ids()
            if not selected_ids:
                return
                
            # Get items data
            items_data = []
            for item_id in selected_ids:
                item = self.board_controller.get_item(self.board_id, item_id)
                items_data.append(item)
                
            # Store in clipboard
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(str(items_data))
        except Exception as e:
            handle_error(e, self, "Error copying items")
            
    def paste_items(self):
        """Paste items from clipboard."""
        try:
            # Get data from clipboard
            from PySide6.QtWidgets import QApplication
            clipboard_text = QApplication.clipboard().text()
            
            try:
                items_data = eval(clipboard_text)
            except:
                QMessageBox.warning(
                    self, "Warning",
                    "Invalid clipboard data."
                )
                return
                
            if not isinstance(items_data, list):
                QMessageBox.warning(
                    self, "Warning",
                    "Invalid clipboard data format."
                )
                return
                
            # Create new items
            for item_data in items_data:
                # Remove ID from data
                if 'id' in item_data:
                    del item_data['id']
                    
                # Create item
                self.board_controller.create_item(self.board_id, item_data)
                
            self.load_items()
            self.item_updated.emit(self.board_id)
            QMessageBox.information(
                self, "Success",
                f"{len(items_data)} item(s) pasted successfully."
            )
        except Exception as e:
            handle_error(e, self, "Error pasting items")
            
    def create_field_for_column(self, column, value=None):
        """Create appropriate input field for column type."""
        from PySide6.QtWidgets import QLineEdit, QSpinBox, QDateEdit, QCheckBox, QComboBox
        
        field = None
        
        if column['type'] == 'Text':
            field = QLineEdit()
            if value:
                field.setText(str(value))
        elif column['type'] == 'Number':
            field = QSpinBox()
            if value:
                field.setValue(int(value))
        elif column['type'] == 'Date':
            field = QDateEdit()
            if value:
                field.setDate(value)
        elif column['type'] == 'Checkbox':
            field = QCheckBox()
            if value:
                field.setChecked(bool(value))
        elif column['type'] == 'Dropdown':
            field = QComboBox()
            if 'settings' in column and 'labels' in column['settings']:
                field.addItems(column['settings']['labels'])
            if value:
                field.setCurrentText(str(value))
                
        if field:
            field.column_id = column['id']
            field.get_value = lambda: self.get_field_value(field, column['type'])
            
        return field
        
    def get_field_value(self, field, field_type):
        """Get value from field based on its type."""
        if field_type == 'Text':
            return field.text()
        elif field_type == 'Number':
            return field.value()
        elif field_type == 'Date':
            return field.date().toPython()
        elif field_type == 'Checkbox':
            return field.isChecked()
        elif field_type == 'Dropdown':
            return field.currentText()
        return None 