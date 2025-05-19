"""
Sync controller for synchronizing with Monday.com.
"""

import logging
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

# Get logger
logger = logging.getLogger("monday_uploader.sync_controller")

class SyncController:
    """
    Controller for synchronizing with Monday.com.
    """
    
    def __init__(self, monday_api, session):
        """
        Initialize the sync controller.
        
        Args:
            monday_api: MondayAPI instance
            session: SQLAlchemy session
        """
        self.monday_api = monday_api
        self.session = session
        self.last_sync_time = None
        self.is_offline_mode = False
        
        logger.info("Sync controller initialized")
    
    def set_api(self, monday_api):
        """Update the API instance."""
        self.monday_api = monday_api
    
    def set_offline_mode(self, offline: bool):
        """Set offline mode."""
        self.is_offline_mode = offline
        logger.info(f"Offline mode set to: {offline}")
    
    def force_sync(self) -> bool:
        """
        Force synchronization with Monday.com.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            start_time = time.time()
            
            if self.is_offline_mode:
                # In offline mode, simulate a successful sync with a slight delay
                logger.info("Syncing in offline mode")
                time.sleep(random.uniform(0.5, 1.5))  # Simulate network delay
                self.last_sync_time = datetime.now()
                return True
                
            # In a real implementation, this would sync data with Monday.com API
            logger.info("Starting sync with Monday.com")
            
            # For now, just simulate a successful sync with a delay
            time.sleep(random.uniform(1.0, 2.0))  # Simulate network delay
            
            self.last_sync_time = datetime.now()
            
            end_time = time.time()
            logger.info(f"Sync completed in {round(end_time - start_time, 2)} seconds")
            
            return True
        except Exception as e:
            logger.error(f"Error during sync: {str(e)}")
            
            # If an error occurs, automatically switch to offline mode
            self.is_offline_mode = True
            logger.warning("Switched to offline mode due to sync error")
            
            return False
    
    def get_last_sync_time(self) -> Optional[datetime]:
        """Get the last successful sync time."""
        return self.last_sync_time
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get the current sync status."""
        status = {
            "is_offline": self.is_offline_mode,
            "last_sync": self.last_sync_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_sync_time else "Never",
            "api_available": not self.is_offline_mode
        }
        
        return status 