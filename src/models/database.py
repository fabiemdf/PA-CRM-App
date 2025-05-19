"""
Database initialization and model definitions.
"""

import os
import logging
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

# Get logger
logger = logging.getLogger("monday_uploader.database")

# Create the declarative base class
Base = declarative_base()

# Model definitions
class Board(Base):
    """Monday.com board representation."""
    
    __tablename__ = 'boards'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    columns = relationship('BoardColumn', back_populates='board', cascade='all, delete-orphan')
    items = relationship('Item', back_populates='board', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Board(id={self.id}, name='{self.name}')>"

class BoardColumn(Base):
    """Monday.com board column representation."""
    
    __tablename__ = 'board_columns'
    
    id = Column(String(50), primary_key=True)
    board_id = Column(String(50), ForeignKey('boards.id'), nullable=False)
    title = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    settings = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    board = relationship('Board', back_populates='columns')
    
    def __repr__(self):
        return f"<BoardColumn(id={self.id}, title='{self.title}', type='{self.type}')>"

class Item(Base):
    """Monday.com item representation."""
    
    __tablename__ = 'items'
    
    id = Column(String(50), primary_key=True)
    board_id = Column(String(50), ForeignKey('boards.id'), nullable=False)
    name = Column(String(255), nullable=False)
    group = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    board = relationship('Board', back_populates='items')
    column_values = relationship('ItemColumnValue', back_populates='item', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}')>"

class ItemColumnValue(Base):
    """Monday.com item column value representation."""
    
    __tablename__ = 'item_column_values'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String(50), ForeignKey('items.id'), nullable=False)
    column_id = Column(String(50), nullable=False)
    value = Column(Text, nullable=True)
    text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    item = relationship('Item', back_populates='column_values')
    
    def __repr__(self):
        return f"<ItemColumnValue(id={self.id}, column_id='{self.column_id}')>"

class SyncLog(Base):
    """Synchronization log entry."""
    
    __tablename__ = 'sync_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    board_id = Column(String(50), nullable=True)
    item_id = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<SyncLog(id={self.id}, action='{self.action}', status='{self.status}')>"

class Template(Base):
    """User-defined template."""
    
    __tablename__ = 'templates'
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    columns = Column(Text, nullable=True)  # JSON-encoded column configuration
    settings = Column(Text, nullable=True)  # JSON-encoded template settings
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}')>"

class CalendarEvent(Base):
    """Calendar event model."""
    
    __tablename__ = 'calendar_events'
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_all_day = Column(Boolean, default=False)
    color = Column(String(50), default='#3788d8')
    location = Column(String(255), nullable=True)
    event_type = Column(String(50), nullable=True)
    monday_item_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    reminders = relationship('EventReminder', back_populates='event', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title='{self.title}')>"

class EventReminder(Base):
    """Event reminder model."""
    
    __tablename__ = 'event_reminders'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String(50), ForeignKey('calendar_events.id'), nullable=False)
    reminder_time = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    event = relationship('CalendarEvent', back_populates='reminders')
    
    def __repr__(self):
        return f"<EventReminder(id={self.id}, event_id={self.event_id})>"

class MapLocation(Base):
    """Location for map visualization."""
    
    __tablename__ = 'map_locations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String(50), nullable=True)
    board_id = Column(String(50), nullable=True)
    address = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    color = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<MapLocation(id={self.id}, address='{self.address}')>"

class WeatherFeed(Base):
    """Weather news feed including NOAA, hurricane, storm and weather reports."""
    
    __tablename__ = 'weather_feeds'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)  # NOAA, NHC, Weather Channel, etc.
    feed_type = Column(String(50), nullable=False)  # Hurricane, Storm, General Weather, etc.
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    url = Column(String(255), nullable=True)
    pub_date = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)  # Geographic area affected
    severity = Column(String(50), nullable=True)  # Warning, Watch, Advisory, etc.
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<WeatherFeed(id={self.id}, source='{self.source}', title='{self.title}')>"

class Claim(Base):
    """Claims data from Excel import."""
    
    __tablename__ = 'claims'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    claim_number = Column(String(50), nullable=True)
    person = Column(String(255), nullable=True)
    claim_status = Column(String(50), nullable=True)
    client = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    file_number = Column(String(50), nullable=True)
    # Store any additional columns as JSON
    additional_data = Column(Text, nullable=True)
    board_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Claim(id={self.id}, name='{self.name}', claim_number='{self.claim_number}')>"

class Client(Base):
    """Clients data from Excel import."""
    
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    contact_person = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    # Store any additional columns as JSON
    additional_data = Column(Text, nullable=True)
    board_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', company='{self.company}')>"

class PublicAdjuster(Base):
    """Public Adjusters data from Excel import."""
    
    __tablename__ = 'public_adjusters'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    license = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    # Store any additional columns as JSON
    additional_data = Column(Text, nullable=True)
    board_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<PublicAdjuster(id={self.id}, name='{self.name}', company='{self.company}')>"

class Employee(Base):
    """Employees data from Excel import."""
    
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    position = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    department = Column(String(255), nullable=True)
    hire_date = Column(String(50), nullable=True)
    # Store any additional columns as JSON
    additional_data = Column(Text, nullable=True)
    board_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', position='{self.position}')>"

class Note(Base):
    """Notes data from Excel import."""
    
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    client = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    category = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    due_date = Column(String(50), nullable=True)
    # Store any additional columns as JSON
    additional_data = Column(Text, nullable=True)
    board_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}')>"

class BoardData(Base):
    """Generic data model for any board imported from Excel."""
    
    __tablename__ = 'board_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    board_id = Column(String(50), nullable=False)
    board_name = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)  # Primary display field
    # JSON data to store all fields
    data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<BoardData(id={self.id}, board_name='{self.board_name}', name='{self.name}')>"

def init_db(db_path: str) -> 'sqlalchemy.engine.Engine':
    """
    Initialize the database and return the SQLAlchemy engine.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        SQLAlchemy engine instance
    """
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Create database engine
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    
    logger.info(f"Database initialized at: {db_path}")
    
    return engine

def get_session(engine):
    """
    Create a new session factory.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        SQLAlchemy session factory
    """
    Session = sessionmaker(bind=engine)
 