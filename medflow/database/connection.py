"""Database connection management with connection pooling."""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from ..utils.exceptions import DatabaseError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """Database connection manager with connection pooling."""
    
    _instance = None
    _lock = threading.Lock()
    _local = threading.local()
    
    def __new__(cls, db_path: Optional[str] = None):
        """Singleton pattern to ensure single database connection."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection manager.
        
        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if hasattr(self, '_initialized'):
            return
        
        if db_path is None or db_path == "medflow.db":
            db_path = str(Path.home() / "medflow.db")
        
        self.db_path = db_path
        self._initialized = True
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Database connection manager initialized: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection with proper configuration
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Enable WAL mode for better concurrency
            try:
                conn.execute("PRAGMA journal_mode = WAL")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not enable WAL mode: {e}")
            
            yield conn
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}") from e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_transaction(self):
        """
        Context manager for database transactions.
        
        Yields:
            sqlite3.Connection: Database connection with transaction management
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Begin transaction
            conn.execute("BEGIN")
            
            yield conn
            
            # Commit if no exception occurred
            conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Transaction error: {e}")
            if conn:
                conn.rollback()
            raise DatabaseError(f"Transaction failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in transaction: {e}")
            if conn:
                conn.rollback()
            raise DatabaseError(f"Transaction failed: {e}") from e
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a single query and return cursor.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            sqlite3.Cursor: Query cursor
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor
    
    def execute_script(self, script: str) -> None:
        """
        Execute a SQL script.
        
        Args:
            script: SQL script to execute
        """
        with self.get_connection() as conn:
            conn.executescript(script)
    
    def backup_database(self, backup_path: str) -> None:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for backup file
        """
        import shutil
        
        try:
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
        except IOError as e:
            raise DatabaseError(f"Failed to create backup: {e}") from e
    
    def get_database_size(self) -> int:
        """
        Get the size of the database file in bytes.
        
        Returns:
            Database file size in bytes
        """
        return Path(self.db_path).stat().st_size
    
    def vacuum(self) -> None:
        """Vacuum the database to reclaim space."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        logger.info("Database vacuumed")
