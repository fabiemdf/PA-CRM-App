"""
Feedback controller for managing user feedback.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, func
from sqlalchemy.exc import SQLAlchemyError

from src.models.feedback import Feedback

# Get logger
logger = logging.getLogger("monday_uploader.feedback")

class FeedbackController:
    """Controller for handling user feedback."""
    
    def __init__(self, session: Session):
        """
        Initialize the feedback controller.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
        logger.info("Feedback controller initialized")
    
    def submit_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """
        Submit user feedback.
        
        Args:
            feedback_data: Feedback data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create feedback record
            feedback = Feedback(
                type=feedback_data["type"],
                timestamp=datetime.fromisoformat(feedback_data["timestamp"]),
                app_version=feedback_data["app_version"],
                user_id=feedback_data.get("user_id"),
                contact_info=feedback_data.get("contact_info"),
                data=feedback_data
            )
            
            # Add to session
            self.session.add(feedback)
            self.session.commit()
            
            logger.info(f"Feedback submitted: {feedback_data['type']}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            self.session.rollback()
            return False
    
    def get_feedback(self, feedback_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get feedback records.
        
        Args:
            feedback_type: Optional feedback type filter
            
        Returns:
            List of feedback records
        """
        try:
            # Build query
            query = self.session.query(Feedback)
            
            # Add type filter if specified
            if feedback_type:
                query = query.filter(Feedback.type == feedback_type)
            
            # Get records
            feedback_records = query.all()
            
            # Convert to dictionaries
            return [record.to_dict() for record in feedback_records]
            
        except Exception as e:
            logger.error(f"Error getting feedback: {str(e)}")
            return []
    
    def export_feedback(self, file_path: str, feedback_type: Optional[str] = None) -> bool:
        """
        Export feedback to a JSON file.
        
        Args:
            file_path: Path to export file
            feedback_type: Optional feedback type filter
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get feedback records
            feedback_records = self.get_feedback(feedback_type)
            
            # Write to file
            with open(file_path, "w") as f:
                json.dump(feedback_records, f, indent=2, default=str)
            
            logger.info(f"Feedback exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting feedback: {str(e)}")
            return False
    
    def update_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """
        Update feedback record.
        
        Args:
            feedback_data: Updated feedback data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get feedback record
            feedback = self.session.query(Feedback).get(feedback_data["id"])
            if not feedback:
                logger.error(f"Feedback record not found: {feedback_data['id']}")
                return False
            
            # Update fields
            feedback.status = feedback_data.get("status")
            feedback.response = feedback_data.get("response")
            feedback.notes = feedback_data.get("notes")
            feedback.updated_at = datetime.fromisoformat(feedback_data["updated_at"])
            
            # Update data
            feedback.data.update(feedback_data)
            
            # Commit changes
            self.session.commit()
            
            logger.info(f"Feedback updated: {feedback_data['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating feedback: {str(e)}")
            self.session.rollback()
            return False 