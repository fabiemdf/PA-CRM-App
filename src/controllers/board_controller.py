"""
Board controller for managing local boards.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from models.database import Board, BoardColumn, BoardItem, Session
from utils.error_handling import handle_error

# Get logger
logger = logging.getLogger("monday_uploader.board_controller")

class BoardController:
    """
    Controller for managing local boards.
    """
    
    def __init__(self, session=None, default_boards=None):
        """
        Initialize the board controller.
        
        Args:
            session: SQLAlchemy session
            default_boards: Default boards mapping
        """
        self.session = session or Session()
        self.default_boards = default_boards or {}
        self.board_map = self.default_boards
        self._board_details = {}
        
        # Initialize boards in database if needed
        self._init_boards()
        
    def _init_boards(self):
        """Initialize boards in the database."""
        try:
            # Get existing boards
            existing_boards = self.session.query(Board).all()
            existing_board_ids = {board.id for board in existing_boards}
            
            # Add any missing boards from default_boards
            for name, board_id in self.default_boards.items():
                if board_id not in existing_board_ids:
                    board = Board(
                        id=board_id,
                        name=name,
                        archived=False
                    )
                    self.session.add(board)
            
            # Commit changes
            self.session.commit()
        except Exception as e:
            logger.error(f"Error initializing boards: {str(e)}")
            self.session.rollback()
        
    def get_boards(self) -> List[Dict[str, Any]]:
        """Get all active boards."""
        try:
            boards = self.session.query(Board).filter_by(archived=False).all()
            return [
                {
                    'id': board.id,
                    'name': board.name,
                    'created_at': board.created_at,
                    'updated_at': board.updated_at
                }
                for board in boards
            ]
        except Exception as e:
            logger.error(f"Error getting boards: {str(e)}")
            return []
            
    def get_board(self, board_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific board by ID."""
        try:
            board = self.session.query(Board).get(board_id)
            if board:
                return {
                    'id': board.id,
                    'name': board.name,
                    'created_at': board.created_at,
                    'updated_at': board.updated_at
                }
            return None
        except Exception as e:
            handle_error(e, "Error getting board")
            return None
            
    def create_board(self, name: str) -> Optional[str]:
        """Create a new board."""
        try:
            board = Board(name=name)
            self.session.add(board)
            self.session.commit()
            return board.id
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error creating board")
            return None
            
    def update_board(self, board_id: str, name: str) -> bool:
        """Update a board's name."""
        try:
            board = self.session.query(Board).get(board_id)
            if board:
                board.name = name
                board.updated_at = datetime.utcnow()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error updating board")
            return False
            
    def archive_board(self, board_id: str) -> bool:
        """Archive a board."""
        try:
            board = self.session.query(Board).get(board_id)
            if board:
                board.archived = True
                board.updated_at = datetime.utcnow()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error archiving board")
            return False
            
    def delete_board(self, board_id: str) -> bool:
        """Delete a board and all its contents."""
        try:
            board = self.session.query(Board).get(board_id)
            if board:
                # Delete all items
                self.session.query(BoardItem).filter_by(board_id=board_id).delete()
                # Delete all columns
                self.session.query(BoardColumn).filter_by(board_id=board_id).delete()
                # Delete board
                self.session.delete(board)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error deleting board")
            return False
            
    def get_board_columns(self, board_id: str) -> List[Dict[str, Any]]:
        """Get all columns for a board."""
        try:
            columns = self.session.query(BoardColumn).filter_by(
                board_id=board_id, archived=False
            ).all()
            return [
                {
                    'id': column.id,
                    'title': column.title,
                    'type': column.type,
                    'settings': column.settings,
                    'created_at': column.created_at,
                    'updated_at': column.updated_at
                }
                for column in columns
            ]
        except Exception as e:
            handle_error(e, "Error getting board columns")
            return []
            
    def create_column(self, board_id: str, title: str, type: str, settings: Dict = None) -> Optional[str]:
        """Create a new column in a board."""
        try:
            column = BoardColumn(
                board_id=board_id,
                title=title,
                type=type,
                settings=settings or {}
            )
            self.session.add(column)
            self.session.commit()
            return column.id
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error creating column")
            return None
            
    def update_column(self, board_id: str, column_id: str, title: str, type: str, settings: Dict = None) -> bool:
        """Update a column's properties."""
        try:
            column = self.session.query(BoardColumn).get(column_id)
            if column and column.board_id == board_id:
                column.title = title
                column.type = type
                if settings is not None:
                    column.settings = settings
                column.updated_at = datetime.utcnow()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error updating column")
            return False
            
    def archive_column(self, board_id: str, column_id: str) -> bool:
        """Archive a column."""
        try:
            column = self.session.query(BoardColumn).get(column_id)
            if column and column.board_id == board_id:
                column.archived = True
                column.updated_at = datetime.utcnow()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error archiving column")
            return False
            
    def delete_column(self, board_id: str, column_id: str) -> bool:
        """Delete a column and its data."""
        try:
            column = self.session.query(BoardColumn).get(column_id)
            if column and column.board_id == board_id:
                # Delete column data from items
                items = self.session.query(BoardItem).filter_by(board_id=board_id).all()
                for item in items:
                    if column_id in item.data:
                        del item.data[column_id]
                        item.updated_at = datetime.utcnow()
                # Delete column
                self.session.delete(column)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error deleting column")
            return False
            
    def get_board_items(self, board_id: str) -> List[Dict[str, Any]]:
        """Get all items for a board."""
        try:
            items = self.session.query(BoardItem).filter_by(
                board_id=board_id, archived=False
            ).all()
            return [
                {
                    'id': item.id,
                    'data': item.data,
                    'created_at': item.created_at,
                    'updated_at': item.updated_at
                }
                for item in items
            ]
        except Exception as e:
            handle_error(e, "Error getting board items")
            return []
            
    def get_item(self, board_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific item by ID."""
        try:
            item = self.session.query(BoardItem).get(item_id)
            if item and item.board_id == board_id:
                return {
                    'id': item.id,
                    'data': item.data,
                    'created_at': item.created_at,
                    'updated_at': item.updated_at
                }
            return None
        except Exception as e:
            handle_error(e, "Error getting item")
            return None
            
    def create_item(self, board_id: str, data: Dict[str, Any]) -> Optional[str]:
        """Create a new item in a board."""
        try:
            item = BoardItem(board_id=board_id, data=data)
            self.session.add(item)
            self.session.commit()
            return item.id
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error creating item")
            return None
            
    def update_item(self, board_id: str, item_id: str, data: Dict[str, Any]) -> bool:
        """Update an item's data."""
        try:
            item = self.session.query(BoardItem).get(item_id)
            if item and item.board_id == board_id:
                item.data.update(data)
                item.updated_at = datetime.utcnow()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error updating item")
            return False
            
    def archive_item(self, board_id: str, item_id: str) -> bool:
        """Archive an item."""
        try:
            item = self.session.query(BoardItem).get(item_id)
            if item and item.board_id == board_id:
                item.archived = True
                item.updated_at = datetime.utcnow()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error archiving item")
            return False
            
    def delete_item(self, board_id: str, item_id: str) -> bool:
        """Delete an item."""
        try:
            item = self.session.query(BoardItem).get(item_id)
            if item and item.board_id == board_id:
                self.session.delete(item)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            handle_error(e, "Error deleting item")
            return False
    
    def get_board_id(self, board_name: str) -> Optional[str]:
        """
        Get board ID by name.
        
        Args:
            board_name: Board name
            
        Returns:
            Board ID or None if not found
        """
        return self.board_map.get(board_name)
    
    def get_board_name(self, board_id: str) -> Optional[str]:
        """
        Get board name by ID.
        
        Args:
            board_id: Board ID
            
        Returns:
            Board name or None if not found
        """
        for name, id in self.board_map.items():
            if id == board_id:
                return name
        return None
    
    def get_board(self, board_id: str) -> Optional[Dict[str, Any]]:
        """
        Get board details by ID.
        
        Args:
            board_id: Board ID
            
        Returns:
            Board details or None if not found
        """
        # Check if we have details cached
        if board_id in self._board_details:
            return self._board_details[board_id]
        
        # Get board name
        board_name = self.get_board_name(board_id)
        if not board_name:
            return None
        
        # Create basic board details
        board_details = {
            "id": board_id,
            "name": board_name,
            "state": "active",
            "description": f"This is the {board_name} board",
            "columns": [
                {"id": "name", "title": "Name", "type": "text"},
                {"id": "status", "title": "Status", "type": "status"},
                {"id": "created_at", "title": "Created At", "type": "date"},
                {"id": "owner", "title": "Owner", "type": "person"}
            ],
            "groups": [
                {"id": "group1", "title": "Group 1"},
                {"id": "group2", "title": "Group 2"}
            ]
        }
        
        # Add board-specific columns
        if board_name == "Clients":
            board_details["columns"].extend([
                {"id": "company", "title": "Company", "type": "text"},
                {"id": "email", "title": "Email", "type": "email"},
                {"id": "phone", "title": "Phone", "type": "phone"}
            ])
        elif board_name == "Tasks":
            board_details["columns"].extend([
                {"id": "due_date", "title": "Due Date", "type": "date"},
                {"id": "priority", "title": "Priority", "type": "dropdown"}
            ])
        elif board_name == "Claims":
            board_details["columns"].extend([
                {"id": "claim_number", "title": "Claim Number", "type": "text"},
                {"id": "insured", "title": "Insured", "type": "text"},
                {"id": "amount", "title": "Amount", "type": "number"}
            ])
        
        # Cache board details
        self._board_details[board_id] = board_details
        
        return board_details 