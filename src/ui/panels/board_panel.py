"""
Board panel for displaying and selecting Monday.com boards.
"""

import logging
from typing import Dict, List, Any, Optional

from PySide6.QtCore import Qt, Signal, Slot, QSize
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
    
    def __init__(self, board_controller: BoardController, parent=None):
        """
        Initialize the board panel.
        
        Args:
            board_controller: Board controller instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.board_controller = board_controller
        self.boards: List[Dict[str, Any]] = []
        
        # Create UI
        self._create_ui()
        
        # Load boards
        self.load_boards()
        
        logger.debug("Board panel initialized")
    
    def _create_ui(self):
        """Create the user interface."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create search layout
        search_layout = QHBoxLayout()
        main_layout.addLayout(search_layout)
        
        # Create search field
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search boards...")
        self.search_edit.textChanged.connect(self._filter_boards)
        search_layout.addWidget(self.search_edit)
        
        # Create refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_boards)
        search_layout.addWidget(self.refresh_button)
        
        # Create list widget
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        main_layout.addWidget(self.list_widget)
        
        # Create status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.status_label)
    
    def load_boards(self):
        """Load boards from the controller."""
        try:
            # Update status
            self.status_label.setText("Loading boards...")
            self.status_label.setStyleSheet("color: blue;")
            self.refresh_button.setEnabled(False)
            
            # Clear list
            self.list_widget.clear()
            
            # Get boards from controller
            board_map = self.board_controller.get_boards()
            
            # Check if any boards were found
            if not board_map:
                self.status_label.setText("No boards found")
                self.status_label.setStyleSheet("color: gray;")
                self.refresh_button.setEnabled(True)
                return
            
            # Convert board_map to a list of board objects
            self.boards = []
            for name, board_id in board_map.items():
                self.boards.append({"name": name, "id": board_id})
            
            # Add boards to list
            for board in self.boards:
                item = QListWidgetItem(board["name"])
                item.setData(Qt.UserRole, board["id"])
                
                # Add state as tooltip
                if "state" in board:
                    item.setToolTip(f"State: {board['state']}")
                
                self.list_widget.addItem(item)
            
            # Update status
            self.status_label.setText(f"Loaded {len(self.boards)} boards")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            logger.error(f"Failed to load boards: {str(e)}")
            self.status_label.setText("Failed to load boards")
            self.status_label.setStyleSheet("color: red;")
            
            # Show error dialog
            handle_error(
                exception=e,
                parent=self,
                context={"module": "BoardPanel", "method": "load_boards"}
            )
            
        finally:
            # Enable refresh button
            self.refresh_button.setEnabled(True)
    
    def select_board(self, board_id: str):
        """
        Select a board by ID.
        
        Args:
            board_id: Board ID to select
        """
        # Find board in list
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == board_id:
                # Select item
                self.list_widget.setCurrentItem(item)
                
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
            for i in range(self.list_widget.count()):
                self.list_widget.item(i).setHidden(False)
            return
        
        # Hide boards that don't match the search text
        text = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            board_name = item.text().lower()
            
            item.setHidden(text not in board_name)
    
    def _show_context_menu(self, pos):
        """
        Show context menu for selected board.
        
        Args:
            pos: Mouse position
        """
        # Get selected item
        item = self.list_widget.itemAt(pos)
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
        menu.exec(self.list_widget.mapToGlobal(pos))
    
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
        Refresh a specific board.
        
        Args:
            board_id: Board ID to refresh
        """
        try:
            # Update status
            self.status_label.setText(f"Refreshing board {board_id}...")
            self.status_label.setStyleSheet("color: blue;")
            
            # Refresh board from API
            self.board_controller.refresh_board(board_id)
            
            # Reload boards
            self.load_boards()
            
            # Select the refreshed board
            self.select_board(board_id)
            
        except Exception as e:
            logger.error(f"Failed to refresh board {board_id}: {str(e)}")
            self.status_label.setText("Failed to refresh board")
            self.status_label.setStyleSheet("color: red;")
            
            # Show error dialog
            handle_error(
                exception=e,
                parent=self,
                context={"module": "BoardPanel", "method": "_refresh_board"}
            )
    
    def _open_in_browser(self, board_id: str):
        """
        Open board in web browser.
        
        Args:
            board_id: Board ID to open
        """
        try:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            
            # Get board URL
            url = f"https://monday.com/boards/{board_id}"
            
            # Open URL in browser
            QDesktopServices.openUrl(QUrl(url))
            
        except Exception as e:
            logger.error(f"Failed to open board in browser: {str(e)}")
            
            # Show error dialog
            handle_error(
                exception=e,
                parent=self,
                context={"module": "BoardPanel", "method": "_open_in_browser"}
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