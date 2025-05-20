"""
Database manager for handling database operations.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("monday_uploader.database")

class DatabaseManager:
    """Manages database operations using SQLAlchemy."""
    
    def __init__(self, engine: Engine):
        """
        Initialize the database manager.
        
        Args:
            engine: SQLAlchemy engine instance
        """
        self.engine = engine
        logger.info("Database manager initialized")
    
    def query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        
        Args:
            sql: SQL query string
            params: Optional query parameters
            
        Returns:
            List of dictionaries containing query results
        """
        try:
            with Session(self.engine) as session:
                result = session.execute(text(sql), params or {})
                return [dict(row._mapping) for row in result]
                
        except SQLAlchemyError as e:
            logger.error(f"Query error: {str(e)}")
            raise
    
    def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """
        Insert a record into a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and values
            
        Returns:
            True if successful
        """
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join([':' + key for key in data.keys()])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            with Session(self.engine) as session:
                session.execute(text(sql), data)
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Insert error: {str(e)}")
            raise
    
    def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> bool:
        """
        Update records in a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and values to update
            where: Dictionary of column names and values for WHERE clause
            
        Returns:
            True if successful
        """
        try:
            set_clause = ', '.join([f"{k} = :{k}" for k in data.keys()])
            where_clause = ' AND '.join([f"{k} = :where_{k}" for k in where.keys()])
            
            sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            
            # Prefix where clause parameters with 'where_'
            params = {**data, **{f'where_{k}': v for k, v in where.items()}}
            
            with Session(self.engine) as session:
                session.execute(text(sql), params)
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Update error: {str(e)}")
            raise
    
    def delete(self, table: str, where: Dict[str, Any]) -> bool:
        """
        Delete records from a table.
        
        Args:
            table: Table name
            where: Dictionary of column names and values for WHERE clause
            
        Returns:
            True if successful
        """
        try:
            where_clause = ' AND '.join([f"{k} = :{k}" for k in where.keys()])
            sql = f"DELETE FROM {table} WHERE {where_clause}"
            
            with Session(self.engine) as session:
                session.execute(text(sql), where)
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Delete error: {str(e)}")
            raise 