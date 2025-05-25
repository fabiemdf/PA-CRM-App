"""
Database initialization and model definitions.
"""

import os
import logging
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

# Get logger
logger = logging.getLogger("monday_uploader.database")

# Create the declarative base class
Base = declarative_base()

# Create a global session factory
Session = sessionmaker()

# Export the session factory
__all__ = ['Base', 'Session', 'init_db', 'get_session']

# Model definitions
class Board(Base):
    """Model for boards."""
    __tablename__ = 'boards'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    columns = relationship("BoardColumn", back_populates="board", cascade="all, delete-orphan")
    board_items = relationship("BoardItem", back_populates="board", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="board", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Board(id={self.id}, name='{self.name}')>"

class BoardColumn(Base):
    """Model for board columns."""
    __tablename__ = 'board_columns'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    board_id = Column(String, ForeignKey('boards.id'), nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)  # Text, Number, Date, Checkbox, Dropdown, etc.
    settings = Column(JSON, default=dict)  # Additional settings for the column type
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    board = relationship("Board", back_populates="columns")
    
    def __repr__(self):
        return f"<BoardColumn(id={self.id}, title='{self.title}', type='{self.type}')>"

class BoardItem(Base):
    """Model for board items (rows)."""
    __tablename__ = 'board_items'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    board_id = Column(String, ForeignKey('boards.id'), nullable=False)
    data = Column(JSON, default=dict)  # Column values stored as key-value pairs
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    board = relationship("Board", back_populates="board_items")
    
    def __repr__(self):
        return f"<BoardItem(id={self.id}, board_id='{self.board_id}')>"

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
    
    __tablename__ = 'PA_Claims'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    claim_number = Column(String(50), nullable=True)
    person = Column(String(255), nullable=True)
    claim_status = Column(String(50), nullable=True)
    client = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    file_number = Column(String(50), nullable=True)
    received_on = Column(String(50), nullable=True)
    policy_number = Column(String(50), nullable=True)
    dup_claim_number = Column(String(50), nullable=True)
    loss_date = Column(String(50), nullable=True)
    claim_filed_date = Column(String(50), nullable=True)
    loss_type = Column(String(100), nullable=True)
    claim_location = Column(String(255), nullable=True)
    claim_address = Column(String(255), nullable=True)
    insured_amount = Column(Float, nullable=True)
    initial_offer = Column(Float, nullable=True)
    final_settlement = Column(Float, nullable=True)  # Legacy field
    settlement_amount = Column(Float, nullable=True)  # New field for settlement amount
    settled_at = Column(DateTime, nullable=True)  # New field for settlement date
    pa_fee_percent = Column(Float, nullable=True)
    pa_fee_amount = Column(Float, nullable=True)
    insurance_company = Column(String(255), nullable=True)
    insurance_adjuster = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    loss_title = Column(String(255), nullable=True)
    last_activity = Column(String(50), nullable=True)
    adjuster_initials = Column(String(50), nullable=True)
    claim_street = Column(String(255), nullable=True)
    claim_city = Column(String(255), nullable=True)
    loss_description = Column(Text, nullable=True)
    deadline_date = Column(String(50), nullable=True)
    insurance_companies = Column(String(255), nullable=True)
    insurance_representatives = Column(String(255), nullable=True)
    treaty_year = Column(String(50), nullable=True)
    treaty_type = Column(String(100), nullable=True)
    stat_limitation = Column(String(50), nullable=True)
    loss_prov_state = Column(String(50), nullable=True)
    reserve = Column(Float, nullable=True)
    first_contact = Column(String(50), nullable=True)
    next_rpt_due = Column(String(50), nullable=True)
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

# Add Insurance Company model for foreign key reference
class InsuranceCompany(Base):
    """Insurance company model."""
    
    __tablename__ = 'insurance_companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    contact_person = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    policies = relationship('Policy', back_populates='carrier')
    
    def __repr__(self):
        return f"<InsuranceCompany(id={self.id}, name='{self.name}')>"

# Add Policy model
class Policy(Base):
    """Insurance policy model."""
    
    __tablename__ = 'policies'
    
    id = Column(Integer, primary_key=True)
    policy_number = Column(String(50), nullable=False, unique=True)
    policy_type = Column(String(50), nullable=False)
    carrier_id = Column(Integer, ForeignKey("insurance_companies.id"), nullable=True)
    
    # Coverage amounts
    coverage_a = Column(Float, nullable=True)  # Dwelling
    coverage_b = Column(Float, nullable=True)  # Other Structures
    coverage_c = Column(Float, nullable=True)  # Personal Property
    coverage_d = Column(Float, nullable=True)  # Loss of Use
    coverage_e = Column(Float, nullable=True)  # Personal Liability
    coverage_f = Column(Float, nullable=True)  # Medical Payments
    
    # Policy details
    deductible = Column(Float, nullable=True)
    hurricane_deductible = Column(Float, nullable=True)
    replacement_cost = Column(Boolean, default=False)
    law_ordinance = Column(Boolean, default=False)
    
    # Dates
    effective_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    
    # Relationships
    carrier = relationship("InsuranceCompany", back_populates="policies")
    
    def __repr__(self):
        return f"<Policy(id={self.id}, number='{self.policy_number}', type='{self.policy_type}')>"

class BoardView(Base):
    """Board view configuration."""
    
    __tablename__ = 'board_views'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    board_id = Column(String(50), ForeignKey('boards.id'), nullable=False)
    name = Column(String(255), nullable=False)
    is_default = Column(Boolean, default=False)
    column_order = Column(Text, nullable=True)  # JSON array of column names
    hidden_columns = Column(Text, nullable=True)  # JSON array of hidden column names
    column_widths = Column(Text, nullable=True)  # JSON object mapping column names to widths
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    board = relationship('Board', backref='views')
    
    def __repr__(self):
        return f"<BoardView(id={self.id}, name='{self.name}', board_id='{self.board_id}')>"

def update_schema(engine):
    """
    Update the database schema to match the current model definitions.
    This is a simple migration that adds missing columns.
    """
    inspector = inspect(engine)
    
    # Add missing columns to boards table
    if 'boards' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('boards')]
        
        with engine.connect() as conn:
            if 'archived' not in columns:
                conn.execute(text("ALTER TABLE boards ADD COLUMN archived BOOLEAN DEFAULT FALSE"))
                conn.commit()
                logger.info("Added 'archived' column to boards table")

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
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Log created tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created/verified tables: {', '.join(tables)}")
        
        # Verify each required table exists
        required_tables = [
            'boards', 'board_data', 'PA_Claims', 'clients', 
            'public_adjusters', 'employees', 'notes', 
            'weather_feeds', 'calendar_events',
            'board_columns', 'board_items', 'items',
            'item_column_values', 'sync_logs', 'templates',
            'event_reminders', 'map_locations', 'insurance_companies',
            'policies', 'board_views'
        ]
        
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            logger.error(f"Missing required tables: {', '.join(missing_tables)}")
            # Try to create missing tables
            for table in missing_tables:
                try:
                    if table == 'boards':
                        Board.__table__.create(engine)
                    elif table == 'board_data':
                        BoardData.__table__.create(engine)
                    elif table == 'PA_Claims':
                        Claim.__table__.create(engine)
                    elif table == 'clients':
                        Client.__table__.create(engine)
                    elif table == 'public_adjusters':
                        PublicAdjuster.__table__.create(engine)
                    elif table == 'employees':
                        Employee.__table__.create(engine)
                    elif table == 'notes':
                        Note.__table__.create(engine)
                    elif table == 'weather_feeds':
                        WeatherFeed.__table__.create(engine)
                    elif table == 'calendar_events':
                        CalendarEvent.__table__.create(engine)
                    elif table == 'board_columns':
                        BoardColumn.__table__.create(engine)
                    elif table == 'board_items':
                        BoardItem.__table__.create(engine)
                    elif table == 'items':
                        Item.__table__.create(engine)
                    elif table == 'item_column_values':
                        ItemColumnValue.__table__.create(engine)
                    elif table == 'sync_logs':
                        SyncLog.__table__.create(engine)
                    elif table == 'templates':
                        Template.__table__.create(engine)
                    elif table == 'event_reminders':
                        EventReminder.__table__.create(engine)
                    elif table == 'map_locations':
                        MapLocation.__table__.create(engine)
                    elif table == 'insurance_companies':
                        InsuranceCompany.__table__.create(engine)
                    elif table == 'policies':
                        Policy.__table__.create(engine)
                    elif table == 'board_views':
                        BoardView.__table__.create(engine)
                    logger.info(f"Created missing table: {table}")
                except Exception as e:
                    logger.error(f"Failed to create table {table}: {str(e)}")
        
        # Update schema for existing tables
        update_schema(engine)
        
        # Import and initialize settlement models
        try:
            from src.models.settlement_models import DamageCategory, DamageItem, DamageEntry, SettlementCalculation
            # Create tables for settlement models
            DamageCategory.metadata.create_all(engine)
            DamageItem.metadata.create_all(engine)
            DamageEntry.metadata.create_all(engine)
            SettlementCalculation.metadata.create_all(engine)
            logger.info("Settlement models initialized successfully")
        except ImportError as e:
            logger.warning(f"Settlement models could not be imported: {str(e)}")
        except Exception as e:
            logger.error(f"Error initializing settlement models: {str(e)}")
        
        logger.info(f"Database initialized at: {db_path}")
        return engine
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def get_session(engine):
    """
    Create a new session factory.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        SQLAlchemy session factory
    """
    Session = sessionmaker(bind=engine)
 