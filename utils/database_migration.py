"""
Database migration utility for managing schema changes.
Provides tools for applying and rolling back database changes.
"""

import os
import json
import logging
import datetime
import sqlite3
from typing import Dict, List, Tuple, Optional, Any

from sqlalchemy import create_engine, inspect, MetaData, Table, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateTable, DropTable

logger = logging.getLogger("monday_uploader.db_migration")

class DatabaseMigration:
    """
    Manages database migrations for schema changes.
    Tracks migrations in a migrations table and supports rollbacks.
    """
    
    def __init__(self, engine: Engine, migrations_dir: Optional[str] = None):
        """
        Initialize the database migration manager.
        
        Args:
            engine: SQLAlchemy engine
            migrations_dir: Optional directory for migration files
        """
        self.engine = engine
        self.migrations_dir = migrations_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "migrations"
        )
        
        # Ensure migrations directory exists
        os.makedirs(self.migrations_dir, exist_ok=True)
        
        # Initialize migrations table if it doesn't exist
        self._init_migrations_table()
        
        logger.info("Database migration manager initialized")
    
    def _init_migrations_table(self) -> None:
        """Initialize the migrations tracking table if it doesn't exist."""
        try:
            # Create migrations table if it doesn't exist
            with self.engine.connect() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id INTEGER PRIMARY KEY,
                        version VARCHAR(50) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        applied_at TIMESTAMP NOT NULL,
                        rollback_sql TEXT,
                        UNIQUE(version)
                    )
                """)
            
            logger.info("Migrations table initialized")
            
        except Exception as e:
            logger.error(f"Error initializing migrations table: {str(e)}")
            raise
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """
        Get a list of all applied migrations.
        
        Returns:
            List of migration records
        """
        try:
            # Query migrations table
            with self.engine.connect() as conn:
                result = conn.execute("""
                    SELECT version, name, applied_at
                    FROM schema_migrations
                    ORDER BY version
                """)
                
                migrations = []
                for row in result:
                    migrations.append({
                        "version": row[0],
                        "name": row[1],
                        "applied_at": row[2]
                    })
                
                return migrations
                
        except Exception as e:
            logger.error(f"Error getting applied migrations: {str(e)}")
            return []
    
    def get_pending_migrations(self) -> List[str]:
        """
        Get a list of pending migration files.
        
        Returns:
            List of pending migration filenames
        """
        try:
            # Get all migration files
            migration_files = [
                f for f in os.listdir(self.migrations_dir)
                if f.endswith('.json') and f.startswith('migration_')
            ]
            migration_files.sort()
            
            # Get already applied versions
            applied_versions = set()
            for migration in self.get_applied_migrations():
                applied_versions.add(migration["version"])
            
            # Filter to only pending migrations
            pending_migrations = []
            for filename in migration_files:
                version = filename.replace('migration_', '').replace('.json', '')
                if version not in applied_versions:
                    pending_migrations.append(filename)
            
            return pending_migrations
            
        except Exception as e:
            logger.error(f"Error getting pending migrations: {str(e)}")
            return []
    
    def apply_migration(self, migration_file: str) -> bool:
        """
        Apply a single migration.
        
        Args:
            migration_file: Name of migration file to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            migration_path = os.path.join(self.migrations_dir, migration_file)
            
            # Read migration file
            with open(migration_path, 'r') as f:
                migration = json.load(f)
            
            # Get migration details
            version = migration.get('version')
            name = migration.get('name')
            up_sql = migration.get('up')
            down_sql = migration.get('down')
            
            if not version or not name or not up_sql:
                logger.error(f"Invalid migration file: {migration_file}")
                return False
            
            # Check if already applied
            with self.engine.connect() as conn:
                result = conn.execute("""
                    SELECT 1 FROM schema_migrations WHERE version = ?
                """, (version,))
                
                if result.fetchone():
                    logger.info(f"Migration {version} already applied, skipping")
                    return True
            
            # Apply migration
            with self.engine.begin() as conn:
                # Execute migration SQL
                for statement in up_sql.split(';'):
                    if statement.strip():
                        conn.execute(statement)
                
                # Record migration
                conn.execute("""
                    INSERT INTO schema_migrations (version, name, applied_at, rollback_sql)
                    VALUES (?, ?, ?, ?)
                """, (version, name, datetime.datetime.now().isoformat(), down_sql))
            
            logger.info(f"Applied migration {version}: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying migration {migration_file}: {str(e)}")
            return False
    
    def apply_pending_migrations(self) -> Tuple[int, int]:
        """
        Apply all pending migrations.
        
        Returns:
            Tuple of (successful count, total count)
        """
        pending_migrations = self.get_pending_migrations()
        
        if not pending_migrations:
            logger.info("No pending migrations to apply")
            return (0, 0)
        
        success_count = 0
        for migration_file in pending_migrations:
            if self.apply_migration(migration_file):
                success_count += 1
        
        logger.info(f"Applied {success_count} of {len(pending_migrations)} pending migrations")
        return (success_count, len(pending_migrations))
    
    def rollback_migration(self, version: str) -> bool:
        """
        Rollback a single migration.
        
        Args:
            version: Migration version to rollback
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get migration record
            with self.engine.connect() as conn:
                result = conn.execute("""
                    SELECT rollback_sql FROM schema_migrations WHERE version = ?
                """, (version,))
                
                row = result.fetchone()
                if not row:
                    logger.error(f"Migration {version} not found, cannot rollback")
                    return False
                
                rollback_sql = row[0]
                if not rollback_sql:
                    logger.error(f"No rollback SQL for migration {version}")
                    return False
            
            # Apply rollback
            with self.engine.begin() as conn:
                # Execute rollback SQL
                for statement in rollback_sql.split(';'):
                    if statement.strip():
                        conn.execute(statement)
                
                # Remove migration record
                conn.execute("""
                    DELETE FROM schema_migrations WHERE version = ?
                """, (version,))
            
            logger.info(f"Rolled back migration {version}")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back migration {version}: {str(e)}")
            return False
    
    def rollback_to_version(self, target_version: str) -> Tuple[int, int]:
        """
        Rollback all migrations after the target version.
        
        Args:
            target_version: Target version to rollback to
            
        Returns:
            Tuple of (successful count, total count)
        """
        try:
            # Get all migrations after target version
            with self.engine.connect() as conn:
                result = conn.execute("""
                    SELECT version FROM schema_migrations
                    WHERE version > ?
                    ORDER BY version DESC
                """, (target_version,))
                
                versions_to_rollback = [row[0] for row in result]
            
            if not versions_to_rollback:
                logger.info(f"No migrations to rollback to version {target_version}")
                return (0, 0)
            
            # Rollback each migration
            success_count = 0
            for version in versions_to_rollback:
                if self.rollback_migration(version):
                    success_count += 1
            
            logger.info(f"Rolled back {success_count} of {len(versions_to_rollback)} migrations")
            return (success_count, len(versions_to_rollback))
            
        except Exception as e:
            logger.error(f"Error rolling back to version {target_version}: {str(e)}")
            return (0, 0)
    
    def create_migration(self, name: str, up_sql: str, down_sql: str) -> Optional[str]:
        """
        Create a new migration file.
        
        Args:
            name: Migration name
            up_sql: SQL statements for applying the migration
            down_sql: SQL statements for rolling back the migration
            
        Returns:
            Path to the created migration file, or None on error
        """
        try:
            # Generate version based on timestamp
            version = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Create migration data
            migration = {
                "version": version,
                "name": name,
                "up": up_sql,
                "down": down_sql
            }
            
            # Create filename
            filename = f"migration_{version}.json"
            filepath = os.path.join(self.migrations_dir, filename)
            
            # Write migration file
            with open(filepath, 'w') as f:
                json.dump(migration, f, indent=4)
            
            logger.info(f"Created migration file: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating migration: {str(e)}")
            return None
    
    def backup_database(self, backup_path: Optional[str] = None) -> Optional[str]:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Optional path for backup file
            
        Returns:
            Path to backup file, or None on error
        """
        try:
            # Get database path from engine
            db_url = str(self.engine.url)
            if not db_url.startswith('sqlite:///'):
                logger.error("Database backup only supported for SQLite databases")
                return None
            
            db_path = db_url.replace('sqlite:///', '')
            
            # Generate backup filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            backup_filename = backup_path or f"backup_{timestamp}.db"
            
            # Create backup directory if it doesn't exist
            backup_dir = os.path.dirname(backup_filename)
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup using SQLite backup API
            src_conn = sqlite3.connect(db_path)
            dst_conn = sqlite3.connect(backup_filename)
            
            src_conn.backup(dst_conn)
            
            src_conn.close()
            dst_conn.close()
            
            logger.info(f"Created database backup: {backup_filename}")
            return backup_filename
            
        except Exception as e:
            logger.error(f"Error creating database backup: {str(e)}")
            return None
    
    def generate_model_migration(self, model_class: Any) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate migration SQL from a SQLAlchemy model.
        
        Args:
            model_class: SQLAlchemy model class
            
        Returns:
            Tuple of (up SQL, down SQL), or (None, None) on error
        """
        try:
            # Generate table creation SQL
            metadata = MetaData()
            table_name = model_class.__tablename__
            
            # Introspect the table
            insp = inspect(self.engine)
            if table_name in insp.get_table_names():
                logger.error(f"Table {table_name} already exists, cannot generate creation migration")
                return (None, None)
            
            # Create a copy of the table schema for migration
            table = Table(table_name, metadata)
            for column in model_class.__table__.columns:
                table.append_column(column.copy())
            
            # Generate SQL
            up_sql = str(CreateTable(table).compile(self.engine))
            down_sql = f"DROP TABLE {table_name}"
            
            return (up_sql, down_sql)
            
        except Exception as e:
            logger.error(f"Error generating model migration: {str(e)}")
            return (None, None)
    
    def create_feature_migration(self, feature_name: str, models: List[Any]) -> Optional[str]:
        """
        Create a migration for a new feature.
        
        Args:
            feature_name: Name of the feature
            models: List of SQLAlchemy model classes
            
        Returns:
            Path to the created migration file, or None on error
        """
        try:
            # Generate up and down SQL for each model
            up_statements = []
            down_statements = []
            
            for model in models:
                up_sql, down_sql = self.generate_model_migration(model)
                if up_sql and down_sql:
                    up_statements.append(up_sql)
                    down_statements.append(down_sql)
            
            if not up_statements:
                logger.error(f"No migration SQL generated for feature {feature_name}")
                return None
            
            # Create migration
            migration_name = f"feature_{feature_name.lower().replace(' ', '_')}"
            return self.create_migration(
                migration_name,
                ";\n".join(up_statements),
                ";\n".join(down_statements)
            )
            
        except Exception as e:
            logger.error(f"Error creating feature migration: {str(e)}")
            return None 