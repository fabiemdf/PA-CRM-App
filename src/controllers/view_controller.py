import json
from typing import List, Optional
from datetime import datetime
from src.models.board_view import BoardView
from src.database.database_manager import DatabaseManager

class ViewController:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_board_views(self, board_id: str) -> List[BoardView]:
        """Get all views for a board"""
        try:
            results = self.db_manager.query(
                "SELECT * FROM board_views WHERE board_id = ? ORDER BY name",
                (board_id,)
            )
            
            views = []
            for data in results:
                view_data = {
                    'id': data['id'],
                    'board_id': data['board_id'],
                    'name': data['name'],
                    'description': data['description'],
                    'columns': json.loads(data['columns']),
                    'filters': json.loads(data['filters']),
                    'sort_by': data['sort_by'],
                    'sort_direction': data['sort_direction'],
                    'created_at': data['created_at'],
                    'updated_at': data['updated_at'],
                    'is_default': bool(data['is_default'])
                }
                views.append(BoardView.from_dict(view_data))
            
            return views
        except Exception as e:
            print(f"Error getting board views: {str(e)}")
            return []

    def save_view(self, view: BoardView) -> bool:
        """Save a board view"""
        try:
            view_dict = view.to_dict()
            view_dict['columns'] = json.dumps(view_dict['columns'])
            view_dict['filters'] = json.dumps(view_dict['filters'])
            
            if view.id is None:
                # Insert new view
                self.db_manager.insert('board_views', view_dict)
            else:
                # Update existing view
                self.db_manager.update(
                    'board_views',
                    view_dict,
                    {'id': view.id}
                )
            return True
        except Exception as e:
            print(f"Error saving board view: {str(e)}")
            return False

    def delete_view(self, view_id: int) -> bool:
        """Delete a board view"""
        try:
            self.db_manager.delete('board_views', {'id': view_id})
            return True
        except Exception as e:
            print(f"Error deleting board view: {str(e)}")
            return False

    def get_default_view(self, board_id: str) -> Optional[BoardView]:
        """Get the default view for a board"""
        try:
            result = self.db_manager.query(
                "SELECT * FROM board_views WHERE board_id = ? AND is_default = 1",
                (board_id,)
            )
            
            if not result:
                return None
                
            data = result[0]
            view_data = {
                'id': data['id'],
                'board_id': data['board_id'],
                'name': data['name'],
                'description': data['description'],
                'columns': json.loads(data['columns']),
                'filters': json.loads(data['filters']),
                'sort_by': data['sort_by'],
                'sort_direction': data['sort_direction'],
                'created_at': data['created_at'],
                'updated_at': data['updated_at'],
                'is_default': bool(data['is_default'])
            }
            return BoardView.from_dict(view_data)
        except Exception as e:
            print(f"Error getting default view: {str(e)}")
            return None 