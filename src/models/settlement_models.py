"""
Database models for settlement calculator functionality.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime

# Import the Base from database.py instead of creating a new one
try:
    from src.models.database import Base
except ImportError:
    try:
        from models.database import Base
    except ImportError:
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()

class DamageCategory(Base):
    """Model representing a damage category for claim calculations."""
    __tablename__ = "damage_categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    
    # Relationships
    damage_items = relationship("DamageItem", back_populates="category", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DamageCategory id={self.id}, name='{self.name}'>"


class DamageItem(Base):
    """Model representing a damage item within a category."""
    __tablename__ = "damage_items"
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("damage_categories.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    default_depreciation_rate = Column(Float, nullable=True)
    
    # Relationships
    category = relationship("DamageCategory", back_populates="damage_items")
    damage_entries = relationship("DamageEntry", back_populates="item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DamageItem id={self.id}, name='{self.name}'>"


class DamageEntry(Base):
    """Model representing a damage entry in a calculation."""
    __tablename__ = "damage_entries"
    
    id = Column(Integer, primary_key=True)
    calculation_id = Column(Integer, ForeignKey("settlement_calculations.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("damage_items.id"), nullable=False)
    amount = Column(Float, nullable=False)
    quantity = Column(Float, default=1.0)
    notes = Column(String(255), nullable=True)
    
    # Relationships
    calculation = relationship("SettlementCalculation", back_populates="damage_entries")
    item = relationship("DamageItem", back_populates="damage_entries")
    
    def __repr__(self):
        return f"<DamageEntry id={self.id}, item_id={self.item_id}, amount={self.amount}>"


class SettlementCalculation(Base):
    """Model representing a settlement calculation."""
    __tablename__ = "settlement_calculations"
    
    id = Column(Integer, primary_key=True)
    claim_id = Column(String(50), nullable=True)
    policy_number = Column(String(50), nullable=True)
    
    # Calculation parameters
    depreciation_rate = Column(Float, nullable=True)
    overhead_profit_rate = Column(Float, nullable=True)
    sales_tax_rate = Column(Float, nullable=True)
    
    # Calculation results
    total_damage_estimate = Column(Float, nullable=True)
    depreciation_amount = Column(Float, nullable=True)
    actual_cash_value = Column(Float, nullable=True)
    recoverable_depreciation = Column(Float, nullable=True)
    replacement_cost_value = Column(Float, nullable=True)
    overhead_profit_amount = Column(Float, nullable=True)
    sales_tax_amount = Column(Float, nullable=True)
    deductible_amount = Column(Float, nullable=True)
    net_claim_value = Column(Float, nullable=True)
    negotiation_adjustment = Column(Float, nullable=True)
    estimated_settlement = Column(Float, nullable=True)
    
    # Store the full calculation data as JSON for flexibility
    calculation_data = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    damage_entries = relationship("DamageEntry", back_populates="calculation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SettlementCalculation id={self.id}, claim_id='{self.claim_id}', estimated_settlement={self.estimated_settlement}>"

# Note: The Policy class is now defined in database.py
# Refer to src.models.database.Policy for the policy model 