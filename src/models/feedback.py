"""
Feedback database model.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

# Get logger
logger = logging.getLogger("monday_uploader.feedback")

# Create base class
Base = declarative_base()

class Feedback(Base):
    """Feedback database model."""
    
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    app_version = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    contact_info = Column(String, nullable=True)
    data = Column(JSON, nullable=False)
    status = Column(String, nullable=True)
    response = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    def __init__(self, type: str, timestamp: datetime, app_version: str,
                 user_id: Optional[str] = None, contact_info: Optional[str] = None,
                 data: Optional[Dict[str, Any]] = None, status: Optional[str] = None,
                 response: Optional[str] = None, notes: Optional[str] = None,
                 updated_at: Optional[datetime] = None):
        """
        Initialize feedback record.
        
        Args:
            type: Feedback type
            timestamp: Submission timestamp
            app_version: Application version
            user_id: Optional user ID
            contact_info: Optional contact information
            data: Feedback data dictionary
            status: Optional status
            response: Optional response
            notes: Optional notes
            updated_at: Optional update timestamp
        """
        self.type = type
        self.timestamp = timestamp
        self.app_version = app_version
        self.user_id = user_id
        self.contact_info = contact_info
        self.data = data or {}
        self.status = status
        self.response = response
        self.notes = notes
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert record to dictionary.
        
        Returns:
            Dictionary representation of record
        """
        return {
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "app_version": self.app_version,
            "user_id": self.user_id,
            "contact_info": self.contact_info,
            "data": self.data,
            "status": self.status,
            "response": self.response,
            "notes": self.notes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 