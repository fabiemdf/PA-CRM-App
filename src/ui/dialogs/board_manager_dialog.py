from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLabel, QLineEdit, QComboBox, QMessageBox, QInputDialog,
    QMenu, QWidget, QFormLayout
)
from PySide6.QtCore import Qt, Signal
import logging

from controllers.board_controller import BoardController
from utils.error_handling import handle_error, MondayError

logger = logging.getLogger(__name__)

class BoardManagerDialog(QDialog):
    """Dialog for managing boards and their columns."""
    
    board_updated = Signal(str)  # Signal emitted when a board is modified
    
    def __init__(self, board_controller: BoardController, parent=None):
        super().__init__(parent)
        self.board_controller = board_controller
        self.setup_ui()
        self.load_boards()
        
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Board Manager")
        self.setMinimumSize(600, 400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Board list
        self.board_list = QListWidget()
        self.board_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.board_list.customContextMenuRequested.connect(self.show_board_context_menu)
        layout.addWidget(QLabel("Boards:"))
        layout.addWidget(self.board_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_board_btn = QPushButton("New Board")
        self.new_board_btn.clicked.connect(self.create_new_board)
        button_layout.addWidget(self.new_board_btn)
        
        self.edit_board_btn = QPushButton("Edit Board")
        self.edit_board_btn.clicked.connect(self.edit_selected_board)
        button_layout.addWidget(self.edit_board_btn)
        
        self.archive_board_btn = QPushButton("Archive Board")
        self.archive_board_btn.clicked.connect(self.archive_selected_board)
        button_layout.addWidget(self.archive_board_btn)
        
        self.delete_board_btn = QPushButton("Delete Board")
        self.delete_board_btn.clicked.connect(self.delete_selected_board)
        button_layout.addWidget(self.delete_board_btn)
        
        layout.addLayout(button_layout)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
    def load_boards(self):
        """Load boards into the list widget."""
        try:
            self.board_list.clear()
            boards = self.board_controller.get_boards()
            for board_name, board_id in boards.items():
                self.board_list.addItem(f"{board_name} ({board_id})")
        except Exception as e:
            handle_error(e, self, "Error loading boards")
            
    def show_board_context_menu(self, position):
        """Show context menu for board operations."""
        menu = QMenu()
        
        edit_action = menu.addAction("Edit Board")
        edit_action.triggered.connect(self.edit_selected_board)
        
        archive_action = menu.addAction("Archive Board")
        archive_action.triggered.connect(self.archive_selected_board)
        
        delete_action = menu.addAction("Delete Board")
        delete_action.triggered.connect(self.delete_selected_board)
        
        menu.exec_(self.board_list.mapToGlobal(position))
        
    def create_new_board(self):
        """Create a new board."""
        try:
            name, ok = QInputDialog.getText(
                self, "New Board", "Enter board name:"
            )
            if ok and name:
                board_id = self.board_controller.create_board(name)
                if board_id:
                    self.load_boards()
                    self.board_updated.emit(board_id)
                    QMessageBox.information(
                        self, "Success", f"Board '{name}' created successfully."
                    )
        except Exception as e:
            handle_error(e, self, "Error creating board")
            
    def edit_selected_board(self):
        """Edit the selected board."""
        try:
            current_item = self.board_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Warning", "Please select a board to edit.")
                return
                
            board_name = current_item.text().split(" (")[0]
            new_name, ok = QInputDialog.getText(
                self, "Edit Board", "Enter new board name:", text=board_name
            )
            
            if ok and new_name and new_name != board_name:
                board_id = current_item.text().split("(")[1].rstrip(")")
                if self.board_controller.rename_board(board_id, new_name):
                    self.load_boards()
                    self.board_updated.emit(board_id)
                    QMessageBox.information(
                        self, "Success", f"Board renamed to '{new_name}' successfully."
                    )
        except Exception as e:
            handle_error(e, self, "Error editing board")
            
    def archive_selected_board(self):
        """Archive the selected board."""
        try:
            current_item = self.board_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Warning", "Please select a board to archive.")
                return
                
            board_name = current_item.text().split(" (")[0]
            reply = QMessageBox.question(
                self, "Archive Board",
                f"Are you sure you want to archive '{board_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                board_id = current_item.text().split("(")[1].rstrip(")")
                if self.board_controller.archive_board(board_id):
                    self.load_boards()
                    self.board_updated.emit(board_id)
                    QMessageBox.information(
                        self, "Success", f"Board '{board_name}' archived successfully."
                    )
        except Exception as e:
            handle_error(e, self, "Error archiving board")
            
    def delete_selected_board(self):
        """Delete the selected board."""
        try:
            current_item = self.board_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Warning", "Please select a board to delete.")
                return
                
            board_name = current_item.text().split(" (")[0]
            reply = QMessageBox.warning(
                self, "Delete Board",
                f"Are you sure you want to delete '{board_name}'? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                board_id = current_item.text().split("(")[1].rstrip(")")
                if self.board_controller.delete_board(board_id):
                    self.load_boards()
                    self.board_updated.emit(board_id)
                    QMessageBox.information(
                        self, "Success", f"Board '{board_name}' deleted successfully."
                    )
        except Exception as e:
            handle_error(e, self, "Error deleting board") 