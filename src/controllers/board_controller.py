"""
Board controller for managing Monday.com boards.
"""

import logging
from typing import Dict, List, Any, Optional

# Get logger
logger = logging.getLogger("monday_uploader.board_controller")

class BoardController:
    """
    Controller for managing Monday.com boards.
    """
    
    def __init__(self, monday_api, session, default_boards: Dict[str, str]):
        """
        Initialize the board controller.
        
        Args:
            monday_api: MondayAPI instance
            session: SQLAlchemy session
            default_boards: Default boards mapping
        """
        self.monday_api = monday_api
        self.session = session
        self.default_boards = default_boards
        self.board_map = default_boards.copy()
        
        # Store board details cache
        self._board_details = {}
        
        logger.info("Board controller initialized")
    
    def set_api(self, monday_api):
        """Update the API instance."""
        self.monday_api = monday_api
        
    def get_boards(self) -> Dict[str, str]:
        """
        Get all available boards.
        
        Returns:
            Dict of board name to board ID
        """
        return self.board_map
    
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
    
    def refresh_board(self, board_id: str) -> bool:
        """
        Refresh a specific board from Monday.com.
        
        Args:
            board_id: Board ID to refresh
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # In a real implementation, this would fetch the latest board data from Monday.com
            # For now, we just clear the cached board details to force a refresh
            if board_id in self._board_details:
                del self._board_details[board_id]
            
            logger.info(f"Refreshed board {board_id}")
            return True
        except Exception as e:
            logger.error(f"Error refreshing board {board_id}: {str(e)}")
            return False
    
    def sync_boards(self) -> bool:
        """
        Synchronize boards from Monday.com.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # For now, just use default boards
            # In a real implementation, you would fetch boards from Monday.com API
            return True
        except Exception as e:
            logger.error(f"Error syncing boards: {str(e)}")
            return False 