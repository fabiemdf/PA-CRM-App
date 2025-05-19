"""
Database initialization module.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.feedback import Base as FeedbackBase
from src.models.settings import Base as SettingsBase

# Get logger
logger = logging.getLogger("monday_uploader.database")

def init_db(db_url: str):
    """
    Initialize database with required tables.
    
    Args:
        db_url: Database URL
    """
    try:
        # Create engine
        engine = create_engine(db_url)
        
        # Create all tables
        FeedbackBase.metadata.create_all(engine)
        SettingsBase.metadata.create_all(engine)
        
        # Create session factory
        Session = sessionmaker(bind=engine)
        
        logger.info("Database initialized successfully")
        return Session()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise 