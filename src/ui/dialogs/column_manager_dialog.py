from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLabel, QLineEdit, QComboBox, QMessageBox, QInputDialog,
    QMenu, QWidget, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
import logging

from controllers.board_controller import BoardController
from utils.error_handling import handle_error, MondayError

logger = logging.getLogger(__name__)

class ColumnManagerDialog(QDialog):
    """Dialog for managing columns within a board."""
    
    column_updated = Signal(str)  # Signal emitted when columns are modified
    
    def __init__(self, board_controller: BoardController, board_id: str, parent=None):
        super().__init__(parent)
        self.board_controller = board_controller
        self.board_id = board_id
        self.setup_ui()
        self.load_columns()
        
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Column Manager")
        self.setMinimumSize(600, 400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Column list
        self.column_list = QListWidget()
        self.column_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.column_list.customContextMenuRequested.connect(self.show_column_context_menu)
        layout.addWidget(QLabel("Columns:"))
        layout.addWidget(self.column_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_column_btn = QPushButton("New Column")
        self.new_column_btn.clicked.connect(self.create_new_column)
        button_layout.addWidget(self.new_column_btn)
        
        self.edit_column_btn = QPushButton("Edit Column")
        self.edit_column_btn.clicked.connect(self.edit_selected_column)
        button_layout.addWidget(self.edit_column_btn)
        
        self.archive_column_btn = QPushButton("Archive Column")
        self.archive_column_btn.clicked.connect(self.archive_selected_column)
        button_layout.addWidget(self.archive_column_btn)
        
        self.delete_column_btn = QPushButton("Delete Column")
        self.delete_column_btn.clicked.connect(self.delete_selected_column)
        button_layout.addWidget(self.delete_column_btn)
        
        layout.addLayout(button_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_columns(self):
        """Load columns into the list widget."""
        try:
            self.column_list.clear()
            columns = self.board_controller.get_board_columns(self.board_id)
            for column in columns:
                self.column_list.addItem(
                    f"{column['title']} ({column['type']})"
                )
        except Exception as e:
            handle_error(e, self, "Error loading columns")
            
    def show_column_context_menu(self, position):
        """Show context menu for column operations."""
        menu = QMenu()
        
        edit_action = menu.addAction("Edit Column")
        edit_action.triggered.connect(self.edit_selected_column)
        
        archive_action = menu.addAction("Archive Column")
        archive_action.triggered.connect(self.archive_selected_column)
        
        delete_action = menu.addAction("Delete Column")
        delete_action.triggered.connect(self.delete_selected_column)
        
        menu.exec_(self.column_list.mapToGlobal(position))
        
    def create_new_column(self):
        """Create a new column."""
        try:
            # Create dialog for new column
            dialog = QDialog(self)
            dialog.setWindowTitle("New Column")
            layout = QFormLayout(dialog)
            
            name_edit = QLineEdit()
            layout.addRow("Column Name:", name_edit)
            
            type_combo = QComboBox()
            type_combo.addItems([
                "Text", "Number", "Date", "Checkbox", "Dropdown",
                "Person", "Status", "Long Text", "Link", "File"
            ])
            layout.addRow("Column Type:", type_combo)
            
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)
            
            if dialog.exec_() == QDialog.Accepted:
                name = name_edit.text()
                column_type = type_combo.currentText()
                
                if name:
                    column_id = self.board_controller.create_column(
                        self.board_id, name, column_type
                    )
                    if column_id:
                        self.load_columns()
                        self.column_updated.emit(self.board_id)
                        QMessageBox.information(
                            self, "Success",
                            f"Column '{name}' created successfully."
                        )
        except Exception as e:
            handle_error(e, self, "Error creating column")
            
    def edit_selected_column(self):
        """Edit the selected column."""
        try:
            current_item = self.column_list.currentItem()
            if not current_item:
                QMessageBox.warning(
                    self, "Warning", "Please select a column to edit."
                )
                return
                
            column_name = current_item.text().split(" (")[0]
            column_type = current_item.text().split("(")[1].rstrip(")")
            
            # Create dialog for editing column
            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Column")
            layout = QFormLayout(dialog)
            
            name_edit = QLineEdit(column_name)
            layout.addRow("Column Name:", name_edit)
            
            type_combo = QComboBox()
            type_combo.addItems([
                "Text", "Number", "Date", "Checkbox", "Dropdown",
                "Person", "Status", "Long Text", "Link", "File"
            ])
            type_combo.setCurrentText(column_type)
            layout.addRow("Column Type:", type_combo)
            
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)
            
            if dialog.exec_() == QDialog.Accepted:
                new_name = name_edit.text()
                new_type = type_combo.currentText()
                
                if new_name and (new_name != column_name or new_type != column_type):
                    column_id = current_item.data(Qt.UserRole)
                    if self.board_controller.update_column(
                        self.board_id, column_id, new_name, new_type
                    ):
                        self.load_columns()
                        self.column_updated.emit(self.board_id)
                        QMessageBox.information(
                            self, "Success",
                            f"Column updated successfully."
                        )
        except Exception as e:
            handle_error(e, self, "Error editing column")
            
    def archive_selected_column(self):
        """Archive the selected column."""
        try:
            current_item = self.column_list.currentItem()
            if not current_item:
                QMessageBox.warning(
                    self, "Warning", "Please select a column to archive."
                )
                return
                
            column_name = current_item.text().split(" (")[0]
            reply = QMessageBox.question(
                self, "Archive Column",
                f"Are you sure you want to archive '{column_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                column_id = current_item.data(Qt.UserRole)
                if self.board_controller.archive_column(self.board_id, column_id):
                    self.load_columns()
                    self.column_updated.emit(self.board_id)
                    QMessageBox.information(
                        self, "Success",
                        f"Column '{column_name}' archived successfully."
                    )
        except Exception as e:
            handle_error(e, self, "Error archiving column")
            
    def delete_selected_column(self):
        """Delete the selected column."""
        try:
            current_item = self.column_list.currentItem()
            if not current_item:
                QMessageBox.warning(
                    self, "Warning", "Please select a column to delete."
                )
                return
                
            column_name = current_item.text().split(" (")[0]
            reply = QMessageBox.warning(
                self, "Delete Column",
                f"Are you sure you want to delete '{column_name}'? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                column_id = current_item.data(Qt.UserRole)
                if self.board_controller.delete_column(self.board_id, column_id):
                    self.load_columns()
                    self.column_updated.emit(self.board_id)
                    QMessageBox.information(
                        self, "Success",
                        f"Column '{column_name}' deleted successfully."
                    )
        except Exception as e:
            handle_error(e, self, "Error deleting column") 