"""Database migration management system."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from ..utils.exceptions import MigrationError, DatabaseError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MigrationManager:
    """Manages database schema migrations."""
    
    MIGRATIONS = {
        1: """
        -- Initial schema creation
        CREATE TABLE IF NOT EXISTS academic_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            subtopic TEXT,
            date TEXT NOT NULL,
            time_start TEXT NOT NULL,
            time_end TEXT NOT NULL,
            notes TEXT,
            completed INTEGER DEFAULT 0,
            reminder_minutes INTEGER DEFAULT 15,
            reminder_enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS study_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            high_yield_fact TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES academic_events (id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS study_debt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            reason TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES academic_events (id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS exam_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            exam_type TEXT NOT NULL,
            score REAL NOT NULL CHECK (score >= 0 AND score <= 100),
            date TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS study_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            hours REAL NOT NULL CHECK (hours >= 0),
            subject TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS completed_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            completed_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT,
            school TEXT,
            year_of_study TEXT,
            graduation_year TEXT,
            ambitions TEXT,
            specialties TEXT,
            hobbies TEXT,
            study_plan TEXT,
            motivation TEXT,
            profile_picture_path TEXT,
            music_file_path TEXT,
            music_folder_path TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS library_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            file_path TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT 'General',
            custom_category TEXT,
            description TEXT,
            pages INTEGER CHECK (pages >= 0),
            current_page INTEGER DEFAULT 0 CHECK (current_page >= 0),
            is_read INTEGER DEFAULT 0,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            notes TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_opened TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS book_bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            page_number INTEGER NOT NULL CHECK (page_number >= 0),
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (book_id) REFERENCES library_books (id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS app_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_academic_events_date ON academic_events(date);
        CREATE INDEX IF NOT EXISTS idx_academic_events_category ON academic_events(category);
        CREATE INDEX IF NOT EXISTS idx_exam_scores_subject ON exam_scores(subject_name);
        CREATE INDEX IF NOT EXISTS idx_exam_scores_date ON exam_scores(date);
        CREATE INDEX IF NOT EXISTS idx_study_hours_date ON study_hours(date);
        CREATE INDEX IF NOT EXISTS idx_library_books_category ON library_books(category);
        """,
        
        2: """
        -- Add CHECK constraint for time ranges (requires recreating table)
        -- SQLite doesn't support adding CHECK constraints directly
        -- This is handled in the application layer for now
        """,
        
        3: """
        -- Add migration tracking table
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        );
        
        -- Insert initial migration record
        INSERT OR IGNORE INTO schema_migrations (version, description) 
        VALUES (1, 'Initial schema creation');
        """,

        4: """
        -- Flashcard decks and cards (SM-2 spaced repetition)
        CREATE TABLE IF NOT EXISTS flashcard_decks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deck_id INTEGER,
            front TEXT NOT NULL,
            back TEXT NOT NULL,
            interval_days INTEGER DEFAULT 1,
            next_review TEXT DEFAULT (date('now')),
            ease_factor REAL DEFAULT 2.5,
            reps INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (deck_id) REFERENCES flashcard_decks(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_flashcards_deck ON flashcards(deck_id);
        CREATE INDEX IF NOT EXISTS idx_flashcards_next_review ON flashcards(next_review);
        """,

        5: """
        -- Persistent Pomodoro session log
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            mode TEXT NOT NULL DEFAULT 'work',
            preset TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_pomodoro_date ON pomodoro_sessions(date);
        """,

        6: """
        -- Add music_folder_path column to user_profile (for databases created before this column existed)
        ALTER TABLE user_profile ADD COLUMN music_folder_path TEXT;
        """
    }
    
    def __init__(self, db_connection):
        """
        Initialize migration manager.
        
        Args:
            db_connection: DatabaseConnection instance
        """
        self.db_connection = db_connection
    
    def get_current_version(self) -> int:
        """
        Get the current database schema version.
        
        Returns:
            Current schema version (0 if no migrations applied)
        """
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(version) FROM schema_migrations")
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0
        except (sqlite3.OperationalError, DatabaseError) as e:
            # Migration table doesn't exist (or DatabaseError wrapping it)
            if "no such table" in str(e):
                return 0
            raise
    
    def get_pending_migrations(self) -> List[int]:
        """
        Get list of pending migration versions.
        
        Returns:
            List of migration versions that need to be applied
        """
        current_version = self.get_current_version()
        return [v for v in sorted(self.MIGRATIONS.keys()) if v > current_version]
    
    def apply_migration(self, version: int) -> None:
        """
        Apply a specific migration.
        
        Args:
            version: Migration version to apply
            
        Raises:
            MigrationError: If migration fails
        """
        if version not in self.MIGRATIONS:
            raise MigrationError(f"Migration version {version} not found")
        
        migration_script = self.MIGRATIONS[version]
        
        try:
            with self.db_connection.get_transaction() as conn:
                cursor = conn.cursor()
                
                # Execute migration script
                cursor.executescript(migration_script)
                
                # Record migration
                if version > 0:  # Skip recording for version 0 (initial setup)
                    cursor.execute(
                        "INSERT OR REPLACE INTO schema_migrations (version, description) "
                        "VALUES (?, ?)",
                        (version, f"Migration {version}")
                    )
                
                logger.info(f"Applied migration {version}")
                
        except sqlite3.Error as e:
            raise MigrationError(f"Failed to apply migration {version}: {e}") from e
    
    def migrate_to_latest(self) -> None:
        """Apply all pending migrations to bring database to latest version."""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("Database is up to date")
            return
        
        logger.info(f"Applying {len(pending)} pending migrations...")
        
        for version in pending:
            self.apply_migration(version)
        
        logger.info(f"Database migrated to version {max(pending)}")
    
    def initialize_database(self) -> None:
        """Initialize database with latest schema."""
        try:
            with self.db_connection.get_transaction() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """)
        except Exception as e:
            logger.error(f"Failed to ensure schema_migrations table: {e}")
            raise MigrationError(f"Failed to initialize migration table: {e}") from e

        current_version = self.get_current_version()
        
        if current_version == 0:
            logger.info("Initializing database with latest schema...")
            # Apply all migrations
            self.migrate_to_latest()
        else:
            logger.info(f"Database at version {current_version}, checking for updates...")
            self.migrate_to_latest()