"""
Board panel for displaying and selecting Monday.com boards.
"""

import logging
from typing import Dict, List, Any, Optional

from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QLineEdit, QMenu, QMessageBox
)
from PySide6.QtGui import QIcon, QAction

from controllers.board_controller import BoardController
from utils.error_handling import handle_error, MondayError, ErrorCodes

# Get logger
logger = logging.getLogger("monday_uploader.board_panel")

class BoardPanel(QWidget):
    """
    Panel for displaying and selecting Monday.com boards.
    """
    
    # Signals
    board_selected = Signal(str)  # Emits board ID when a board is selected
    
    def __init__(self, parent=None, board_controller=None):
        """
        Initialize the board panel.
        
        Args:
            parent: Parent widget
            board_controller: Board controller instance
        """
        super().__init__(parent)
        
        if not board_controller:
            raise ValueError("Board controller is required")
        self.board_controller = board_controller
        self.boards: List[Dict[str, Any]] = []
        
        # Create UI
        self.setup_ui()
        
        # Load boards
        self.load_boards()
        
        logger.debug("Board panel initialized")
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create search layout
        search_layout = QHBoxLayout()
        layout.addLayout(search_layout)
        
        # Create search field
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search boards...")
        self.search_edit.textChanged.connect(self._filter_boards)
        search_layout.addWidget(self.search_edit)
        
        # Create refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_boards)
        search_layout.addWidget(self.refresh_button)
        
        # Create board list
        self.board_list = QListWidget()
        self.board_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.board_list.customContextMenuRequested.connect(self._show_context_menu)
        self.board_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.board_list)
        
        # Create status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
    
    def load_boards(self):
        """Load boards from the controller."""
        try:
            # Get boards from controller
            boards = self.board_controller.get_boards()
            if not boards:
                logger.warning("No boards found")
                self.status_label.setText("No boards found")
                return
                
            # Clear existing items
            self.board_list.clear()
            
            # Add boards to list
            for board in boards:
                item = QListWidgetItem(board['name'])
                item.setData(Qt.UserRole, board['id'])
                
                # Add state as tooltip
                if "state" in board:
                    item.setToolTip(f"State: {board['state']}")
                
                self.board_list.addItem(item)
            
            logger.info(f"Loaded {len(boards)} boards")
            self.status_label.setText(f"Loaded {len(boards)} boards")
            
        except Exception as e:
            logger.error(f"Failed to load boards: {str(e)}")
            self.status_label.setText("Failed to load boards")
            handle_error(e)
            
            # Show error dialog
            handle_error(
                exception=e,
                parent=self,
                context={"module": "BoardPanel", "method": "load_boards"}
            )
    
    def select_board(self, board_id: str):
        """
        Select a board by ID.
        
        Args:
            board_id: Board ID to select
        """
        # Find board in list
        for i in range(self.board_list.count()):
            item = self.board_list.item(i)
            if item.data(Qt.UserRole) == board_id:
                # Select item
                self.board_list.setCurrentItem(item)
                
                # Emit signal
                self.board_selected.emit(board_id)
                return
        
        # Board not found
        logger.warning(f"Board not found: {board_id}")
    
    def _filter_boards(self, text: str):
        """
        Filter boards based on search text.
        
        Args:
            text: Search text
        """
        # If no search text, show all boards
        if not text.strip():
            for i in range(self.board_list.count()):
                self.board_list.item(i).setHidden(False)
            return
        
        # Hide boards that don't match the search text
        text = text.strip().lower()
        for i in range(self.board_list.count()):
            item = self.board_list.item(i)
            board_name = item.text().lower()
            
            item.setHidden(text not in board_name)
    
    def _show_context_menu(self, pos):
        """
        Show context menu for selected board.
        
        Args:
            pos: Mouse position
        """
        # Get selected item
        item = self.board_list.itemAt(pos)
        if not item:
            return
        
        # Get board ID
        board_id = item.data(Qt.UserRole)
        
        # Create menu
        menu = QMenu(self)
        
        # Add actions
        open_action = QAction("Open Board", self)
        open_action.triggered.connect(lambda: self._open_board(board_id))
        menu.addAction(open_action)
        
        refresh_action = QAction("Refresh Board", self)
        refresh_action.triggered.connect(lambda: self._refresh_board(board_id))
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        open_browser_action = QAction("Open in Browser", self)
        open_browser_action.triggered.connect(lambda: self._open_in_browser(board_id))
        menu.addAction(open_browser_action)
        
        menu.addSeparator()
        
        properties_action = QAction("Properties", self)
        properties_action.triggered.connect(lambda: self._show_properties(board_id))
        menu.addAction(properties_action)
        
        # Show menu
        menu.exec(self.board_list.mapToGlobal(pos))
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """
        Handle item double click.
        
        Args:
            item: Selected item
        """
        # Get board ID
        board_id = item.data(Qt.UserRole)
        
        # Emit signal
        self.board_selected.emit(board_id)
    
    def _open_board(self, board_id: str):
        """
        Open a board.
        
        Args:
            board_id: Board ID to open
        """
        # Emit signal
        self.board_selected.emit(board_id)
    
    def _refresh_board(self, board_id: str):
        """
        Refresh a board.
        
        Args:
            board_id: Board ID to refresh
        """
        try:
            # Refresh board in controller
            if self.board_controller.refresh_board(board_id):
                # Reload boards
                self.load_boards()
                
                # Show success message
                self.status_label.setText("Board refreshed", 3000)
            else:
                # Show error message
                QMessageBox.warning(
                    self,
                    "Refresh Failed",
                    "Failed to refresh board."
                )
        except Exception as e:
            logger.error(f"Failed to refresh board: {str(e)}")
            handle_error(
                exception=e,
                parent=self,
                context={"module": "BoardPanel", "method": "_refresh_board"}
            )
    
    def _open_in_browser(self, board_id: str):
        """
        Open board in browser.
        
        Args:
            board_id: Board ID to open
        """
        # TODO: Implement browser opening
        QMessageBox.information(
            self,
            "Not Implemented",
            "Opening in browser is not yet implemented."
        )
    
    def _show_properties(self, board_id: str):
        """
        Show board properties.
        
        Args:
            board_id: Board ID to show properties for
        """
        try:
            # Get board details
            board = self.board_controller.get_board(board_id)
            
            if not board:
                QMessageBox.warning(
                    self,
                    "Board Not Found",
                    f"Board with ID {board_id} not found."
                )
                return
            
            # Create message
            message = f"Board Name: {board.get('name', 'N/A')}\n"
            message += f"Board ID: {board_id}\n"
            message += f"State: {board.get('state', 'N/A')}\n"
            
            # Add description if available
            if "description" in board and board["description"]:
                message += f"\nDescription:\n{board['description']}\n"
            
            # Add column count if available
            if "columns" in board:
                message += f"\nColumns: {len(board['columns'])}\n"
            
            # Add group count if available
            if "groups" in board:
                message += f"\nGroups: {len(board['groups'])}\n"
            
            # Show message box
            QMessageBox.information(
                self,
                "Board Properties",
                message
            )
            
        except Exception as e:
            logger.error(f"Failed to show board properties: {str(e)}")
            
            # Show error dialog
            handle_error(
                exception=e,
                parent=self,
                context={"module": "BoardPanel", "method": "_show_properties"}
            )
    
    def show_message(self, message: str, duration: int = 3000):
        """
        Show a message to the user.
        
        Args:
            message: Message to display
            duration: Duration in milliseconds (default: 3000)
        """
        QMessageBox.information(self, "Information", message)
        self.status_label.setText(message)
        if duration > 0:
            QTimer.singleShot(duration, lambda: self.status_label.setText("Ready")) 