from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class BoardView:
    id: Optional[int]
    board_id: str
    name: str
    description: Optional[str]
    columns: List[str]  # List of column IDs to show
    filters: Dict[str, Any]  # Filter criteria
    sort_by: Optional[str]  # Column ID to sort by
    sort_direction: str  # 'asc' or 'desc'
    created_at: datetime
    updated_at: datetime
    is_default: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'board_id': self.board_id,
            'name': self.name,
            'description': self.description,
            'columns': self.columns,
            'filters': self.filters,
            'sort_by': self.sort_by,
            'sort_direction': self.sort_direction,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_default': self.is_default
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoardView':
        return cls(
            id=data.get('id'),
            board_id=data['board_id'],
            name=data['name'],
            description=data.get('description'),
            columns=data['columns'],
            filters=data['filters'],
            sort_by=data.get('sort_by'),
            sort_direction=data.get('sort_direction', 'asc'),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            is_default=data.get('is_default', False)
        ) 