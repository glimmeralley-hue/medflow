"""Database models and operations for MedFlow application."""

import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from .connection import DatabaseConnection
from .migrations import MigrationManager
from ..utils.exceptions import DatabaseError
from ..utils.validators import (
    validate_date,
    validate_time_range,
    validate_score,
    validate_hours,
    validate_rating,
    validate_file_path,
    sanitize_string
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class Database:
    """SQLite database handler for MedFlow application with improved architecture."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database with connection pooling and migration support.
        
        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if db_path is None or db_path == "medflow.db":
            db_path = str(Path.home() / "medflow.db")
        
        self.db_path = db_path
        self.connection = DatabaseConnection(db_path)
        self.migration_manager = MigrationManager(self.connection)
        
        # Initialize database with migrations
        self.migration_manager.initialize_database()
        
        # Run backup on initialization
        self.run_backup()
        
        logger.info(f"Database initialized: {self.db_path}")
    
    def run_backup(self):
        """Run automated backups of the SQLite database."""
        try:
            db_file = Path(self.db_path)
            if not db_file.exists():
                return
            
            # Create backups directory inside com.medflow.app
            backup_dir = Path.home() / ".local" / "share" / "com.medflow.app" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Timestamp for the backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"medflow_backup_{timestamp}.db"
            
            # Copy database file using connection manager
            self.connection.backup_database(str(backup_file))
            
            # Enforce retention policy: keep only the 5 most recent backups
            backups = sorted(list(backup_dir.glob("medflow_backup_*.db")), key=lambda p: p.stat().st_mtime)
            while len(backups) > 5:
                oldest = backups.pop(0)
                oldest.unlink()
                
            logger.info(f"Backup created: {backup_file}")
            
        except Exception as e:
            logger.error(f"Error creating automated backup: {e}")
    
    # ── Academic Events ─────────────────────────────────────────────────────
    
    def add_event(self, title: str, category: str, subtopic: str, 
                  date: str, time_start: str, time_end: str, notes: str = "",
                  reminder_minutes: int = 15, reminder_enabled: bool = True) -> int:
        """Add a new academic event with reminder settings and validation."""
        try:
            # Validate inputs
            title = sanitize_string(title, max_length=200)
            subtopic = sanitize_string(subtopic, max_length=200) if subtopic else ""
            notes = sanitize_string(notes, max_length=2000) if notes else ""
            validate_date(date)
            validate_time_range(time_start, time_end)
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO academic_events 
                    (title, category, subtopic, date, time_start, time_end, notes, reminder_minutes, reminder_enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, category, subtopic, date, time_start, time_end, notes, 
                      reminder_minutes, 1 if reminder_enabled else 0))
                
                event_id = cursor.lastrowid
                logger.info(f"Added event: {title} on {date}")
                return event_id
                
        except Exception as e:
            logger.error(f"Error adding event: {e}")
            raise DatabaseError(f"Failed to add event: {e}") from e
    
    def get_upcoming_events(self, minutes_ahead: int = 30) -> List[Dict]:
        """Get events happening within the next X minutes (for reminders)."""
        try:
            now = datetime.now()
            future = now + timedelta(minutes=minutes_ahead)
            
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM academic_events 
                    WHERE reminder_enabled = 1
                    AND date = ?
                    AND time_start BETWEEN ? AND ?
                    AND completed = 0
                    ORDER BY time_start
                """, (now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), future.strftime("%H:%M")))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            raise DatabaseError(f"Failed to get upcoming events: {e}") from e
    
    def get_events(self, date: Optional[str] = None) -> List[Dict]:
        """Get events, optionally filtered by date."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                if date:
                    validate_date(date)
                    cursor.execute("""
                        SELECT * FROM academic_events 
                        WHERE date = ? ORDER BY time_start
                    """, (date,))
                else:
                    cursor.execute("""
                        SELECT * FROM academic_events 
                        ORDER BY date, time_start
                    """)
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            raise DatabaseError(f"Failed to get events: {e}") from e
    
    def mark_event_completed(self, event_id: int, completed: bool) -> bool:
        """Toggle the completed state of an academic event."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE academic_events SET completed = ? WHERE id = ?",
                    (1 if completed else 0, event_id)
                )
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Event {event_id} marked as {'completed' if completed else 'incomplete'}")
                return success
                
        except Exception as e:
            logger.error(f"Error marking event completed: {e}")
            raise DatabaseError(f"Failed to mark event completed: {e}") from e
    
    # ── Study Notes ──────────────────────────────────────────────────────────
    
    def add_study_note(self, event_id: int, fact: str) -> int:
        """Add a high-yield fact for an event."""
        try:
            fact = sanitize_string(fact, max_length=500)
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO study_notes (event_id, high_yield_fact)
                    VALUES (?, ?)
                """, (event_id, fact))
                
                note_id = cursor.lastrowid
                logger.info(f"Added study note for event {event_id}")
                return note_id
                
        except Exception as e:
            logger.error(f"Error adding study note: {e}")
            raise DatabaseError(f"Failed to add study note: {e}") from e
    
    def get_study_notes(self, event_id: int) -> List[str]:
        """Get high-yield facts for an event."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT high_yield_fact FROM study_notes 
                    WHERE event_id = ?
                """, (event_id,))
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting study notes: {e}")
            raise DatabaseError(f"Failed to get study notes: {e}") from e
    
    def get_total_study_notes(self) -> int:
        """Get total count of study note facts."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM study_notes")
                row = cursor.fetchone()
                return int(row[0]) if row else 0
                
        except Exception as e:
            logger.error(f"Error getting total study notes: {e}")
            raise DatabaseError(f"Failed to get total study notes: {e}") from e
    
    # ── Study Debt ─────────────────────────────────────────────────────────
    
    def add_study_debt(self, event_id: int, reason: str) -> int:
        """Add a study debt entry."""
        try:
            reason = sanitize_string(reason, max_length=500)
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO study_debt (event_id, reason)
                    VALUES (?, ?)
                """, (event_id, reason))
                
                debt_id = cursor.lastrowid
                logger.info(f"Added study debt for event {event_id}")
                return debt_id
                
        except Exception as e:
            logger.error(f"Error adding study debt: {e}")
            raise DatabaseError(f"Failed to add study debt: {e}") from e
    
    def get_study_debt(self) -> List[Dict]:
        """Get all study debt entries."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sd.id, sd.event_id, sd.reason, sd.created_at, ae.title, ae.category, ae.subtopic, ae.notes, ae.date 
                    FROM study_debt sd
                    JOIN academic_events ae ON sd.event_id = ae.id
                    ORDER BY sd.created_at DESC
                """)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting study debt: {e}")
            raise DatabaseError(f"Failed to get study debt: {e}") from e
    
    def resolve_study_debt(self, event_id: int) -> bool:
        """Remove a missed event from study debt."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM study_debt WHERE event_id = ?", (event_id,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Resolved study debt for event {event_id}")
                return success
                
        except Exception as e:
            logger.error(f"Error resolving study debt: {e}")
            raise DatabaseError(f"Failed to resolve study debt: {e}") from e
    
    # ── Exam Scores ─────────────────────────────────────────────────────────
    
    def add_exam_score(self, subject_name: str, exam_type: str, score: float, 
                      date: str, notes: str = "") -> int:
        """Add a new exam score with validation."""
        try:
            subject_name = sanitize_string(subject_name, max_length=100)
            notes = sanitize_string(notes, max_length=500) if notes else ""
            validate_score(score)
            validate_date(date)
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO exam_scores (subject_name, exam_type, score, date, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (subject_name, exam_type, score, date, notes))
                
                score_id = cursor.lastrowid
                logger.info(f"Added exam score: {subject_name} - {score}%")
                return score_id
                
        except Exception as e:
            logger.error(f"Error adding exam score: {e}")
            raise DatabaseError(f"Failed to add exam score: {e}") from e
    
    def get_exam_scores(self, subject: Optional[str] = None) -> List[Dict]:
        """Get exam scores, optionally filtered by subject."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                if subject:
                    cursor.execute("""
                        SELECT * FROM exam_scores 
                        WHERE subject_name = ? ORDER BY date DESC
                    """, (subject,))
                else:
                    cursor.execute("""
                        SELECT * FROM exam_scores ORDER BY date DESC
                    """)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting exam scores: {e}")
            raise DatabaseError(f"Failed to get exam scores: {e}") from e
    
    def delete_exam_score(self, exam_id: int) -> bool:
        """Delete a specific exam score by ID."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM exam_scores WHERE id = ?", (exam_id,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Deleted exam score {exam_id}")
                return success
                
        except Exception as e:
            logger.error(f"Error deleting exam score: {e}")
            raise DatabaseError(f"Failed to delete exam score: {e}") from e
    
    def clear_all_exam_scores(self) -> bool:
        """Clear all exam scores - use with caution."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM exam_scores")
                logger.warning("Cleared all exam scores")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing exam scores: {e}")
            raise DatabaseError(f"Failed to clear exam scores: {e}") from e
    
    def get_study_hours_for_exam_correlation(self, days_before: int = 7) -> List[Dict]:
        """Get study hours data correlated with exam scores for graphing."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        es.id as exam_id,
                        es.subject_name,
                        es.score,
                        es.date as exam_date,
                        COALESCE(SUM(sh.hours), 0) as study_hours_before_exam
                    FROM exam_scores es
                    LEFT JOIN study_hours sh ON 
                        sh.date >= date(es.date, ?) AND 
                        sh.date < es.date
                    GROUP BY es.id, es.subject_name, es.score, es.date
                    ORDER BY es.date
                """, (f'-{days_before} days',))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting study hours for correlation: {e}")
            raise DatabaseError(f"Failed to get study hours for correlation: {e}") from e
    
    # ── Study Hours ─────────────────────────────────────────────────────────
    
    def add_study_hours(self, date: str, hours: float, subject: str = "", 
                       notes: str = "") -> int:
        """Add study hours for a date with validation."""
        try:
            validate_date(date)
            validate_hours(hours)
            subject = sanitize_string(subject, max_length=100) if subject else ""
            notes = sanitize_string(notes, max_length=500) if notes else ""
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, hours FROM study_hours WHERE date = ? AND subject = ?
                """, (date, subject))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing entry
                    new_hours = existing[1] + hours
                    cursor.execute("""
                        UPDATE study_hours SET hours = ? WHERE id = ?
                    """, (new_hours, existing[0]))
                    entry_id = existing[0]
                else:
                    # Insert new entry
                    cursor.execute("""
                        INSERT INTO study_hours (date, hours, subject, notes)
                        VALUES (?, ?, ?, ?)
                    """, (date, hours, subject, notes))
                    entry_id = cursor.lastrowid
                
                logger.info(f"Added study hours: {hours} on {date}")
                return entry_id
                
        except Exception as e:
            logger.error(f"Error adding study hours: {e}")
            raise DatabaseError(f"Failed to add study hours: {e}") from e
    
    def get_study_hours(self, date: Optional[str] = None) -> List[Dict]:
        """Get study hours, optionally filtered by date."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                if date:
                    validate_date(date)
                    cursor.execute("""
                        SELECT * FROM study_hours WHERE date = ? ORDER BY date
                    """, (date,))
                else:
                    cursor.execute("""
                        SELECT * FROM study_hours ORDER BY date
                    """)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting study hours: {e}")
            raise DatabaseError(f"Failed to get study hours: {e}") from e
    
    # ── Completed Tasks ──────────────────────────────────────────────────────
    
    def add_completed_task(self, task_name: str, completed_date: Optional[str] = None) -> int:
        """Add a completed task."""
        try:
            task_name = sanitize_string(task_name, max_length=200)
            if not completed_date:
                completed_date = datetime.now().strftime("%Y-%m-%d")
            validate_date(completed_date)
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO completed_tasks (task_name, completed_date)
                    VALUES (?, ?)
                """, (task_name, completed_date))
                
                task_id = cursor.lastrowid
                logger.info(f"Added completed task: {task_name}")
                return task_id
                
        except Exception as e:
            logger.error(f"Error adding completed task: {e}")
            raise DatabaseError(f"Failed to add completed task: {e}") from e
    
    def get_completed_tasks_count(self, date: Optional[str] = None) -> int:
        """Get count of completed tasks for a date (or all time if no date)."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                if date:
                    validate_date(date)
                    cursor.execute("""
                        SELECT COUNT(*) FROM completed_tasks WHERE completed_date = ?
                    """, (date,))
                else:
                    cursor.execute("""
                        SELECT COUNT(*) FROM completed_tasks
                    """)
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error getting completed tasks count: {e}")
            raise DatabaseError(f"Failed to get completed tasks count: {e}") from e
    
    def get_completed_tasks(self, date: Optional[str] = None) -> List[str]:
        """Get list of completed task names."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                if date:
                    validate_date(date)
                    cursor.execute("""
                        SELECT task_name FROM completed_tasks WHERE completed_date = ?
                    """, (date,))
                else:
                    cursor.execute("""
                        SELECT task_name FROM completed_tasks
                    """)
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting completed tasks: {e}")
            raise DatabaseError(f"Failed to get completed tasks: {e}") from e
    
    # ── User Profile ────────────────────────────────────────────────────────
    
    def save_user_profile(self, profile_data: dict) -> bool:
        """Save user profile to database."""
        try:
            # Sanitize all text fields
            sanitized_data = {}
            for key, value in profile_data.items():
                if isinstance(value, str):
                    sanitized_data[key] = sanitize_string(value, max_length=1000)
                else:
                    sanitized_data[key] = value
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_profile 
                    (id, name, school, year_of_study, graduation_year, ambitions, 
                     specialties, hobbies, study_plan, motivation, profile_picture_path, 
                     music_file_path, music_folder_path, updated_at)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    sanitized_data.get('name', ''),
                    sanitized_data.get('school', ''),
                    sanitized_data.get('year', ''),
                    sanitized_data.get('graduation', ''),
                    sanitized_data.get('ambitions', ''),
                    sanitized_data.get('specialties', ''),
                    sanitized_data.get('hobbies', ''),
                    sanitized_data.get('study_plan', ''),
                    sanitized_data.get('motivation', ''),
                    sanitized_data.get('profile_picture', ''),
                    sanitized_data.get('music_file', ''),
                    sanitized_data.get('music_folder', '')
                ))
                
                logger.info("Saved user profile")
                return True
                
        except Exception as e:
            logger.error(f"Error saving user profile: {e}")
            raise DatabaseError(f"Failed to save user profile: {e}") from e
    
    def clear_user_profile(self) -> bool:
        """Clear user profile from database."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_profile WHERE id = 1")
                logger.info("Cleared user profile")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing user profile: {e}")
            raise DatabaseError(f"Failed to clear user profile: {e}") from e
    
    def get_user_profile(self) -> dict:
        """Get user profile from database."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM user_profile WHERE id = 1")
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return {}
                
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            raise DatabaseError(f"Failed to get user profile: {e}") from e
    
    # ── Library Books ────────────────────────────────────────────────────────
    
    def add_library_book(self, title: str, author: str, file_path: str, 
                        category: str = "General", custom_category: str = "",
                        description: str = "", pages: int = 0) -> int:
        """Add a book to the library."""
        try:
            title = sanitize_string(title, max_length=200)
            author = sanitize_string(author, max_length=100) if author else ""
            custom_category = sanitize_string(custom_category, max_length=100) if custom_category else ""
            description = sanitize_string(description, max_length=1000) if description else ""
            validate_file_path(file_path, must_exist=True, allowed_extensions=['.pdf', '.epub', '.txt'])
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO library_books (title, author, file_path, category, 
                                              custom_category, description, pages)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, author, file_path, category, custom_category, description, pages))
                
                book_id = cursor.lastrowid
                logger.info(f"Added library book: {title}")
                return book_id
                
        except Exception as e:
            logger.error(f"Error adding library book: {e}")
            raise DatabaseError(f"Failed to add library book: {e}") from e
    
    def get_library_books(self, category: Optional[str] = None, 
                         search: Optional[str] = None) -> List[Dict]:
        """Get books from library with optional filtering."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                if category and category != "All":
                    cursor.execute("""
                        SELECT * FROM library_books 
                        WHERE category = ? OR custom_category = ?
                        ORDER BY date_added DESC
                    """, (category, category))
                elif search:
                    search_term = f"%{search}%"
                    cursor.execute("""
                        SELECT * FROM library_books 
                        WHERE title LIKE ? OR author LIKE ? OR description LIKE ?
                        ORDER BY date_added DESC
                    """, (search_term, search_term, search_term))
                else:
                    cursor.execute("SELECT * FROM library_books ORDER BY date_added DESC")
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting library books: {e}")
            raise DatabaseError(f"Failed to get library books: {e}") from e
    
    def get_library_categories(self) -> List[str]:
        """Get all unique categories from library."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT category FROM library_books 
                    UNION
                    SELECT DISTINCT custom_category FROM library_books WHERE custom_category != ''
                """)
                return [row[0] for row in cursor.fetchall() if row[0]]
                
        except Exception as e:
            logger.error(f"Error getting library categories: {e}")
            raise DatabaseError(f"Failed to get library categories: {e}") from e
    
    def update_book_read_status(self, book_id: int, is_read: bool, 
                               current_page: Optional[int] = None) -> None:
        """Update book read status and current page."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                if current_page is not None:
                    cursor.execute("""
                        UPDATE library_books 
                        SET is_read = ?, current_page = ?, last_opened = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (1 if is_read else 0, current_page, book_id))
                else:
                    cursor.execute("""
                        UPDATE library_books 
                        SET is_read = ?, last_opened = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (1 if is_read else 0, book_id))
                
                logger.info(f"Updated book {book_id} read status")
                
        except Exception as e:
            logger.error(f"Error updating book read status: {e}")
            raise DatabaseError(f"Failed to update book read status: {e}") from e
    
    def update_book_rating(self, book_id: int, rating: int) -> None:
        """Update book rating."""
        try:
            validate_rating(rating)
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE library_books SET rating = ? WHERE id = ?", (rating, book_id))
                logger.info(f"Updated book {book_id} rating to {rating}")
                
        except Exception as e:
            logger.error(f"Error updating book rating: {e}")
            raise DatabaseError(f"Failed to update book rating: {e}") from e
    
    def delete_library_book(self, book_id: int) -> bool:
        """Delete a book from the library."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM library_books WHERE id = ?", (book_id,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Deleted library book {book_id}")
                return success
                
        except Exception as e:
            logger.error(f"Error deleting library book: {e}")
            raise DatabaseError(f"Failed to delete library book: {e}") from e
    
    def add_book_bookmark(self, book_id: int, page_number: int, note: str = "") -> int:
        """Add a bookmark to a book."""
        try:
            note = sanitize_string(note, max_length=500) if note else ""
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO book_bookmarks (book_id, page_number, note)
                    VALUES (?, ?, ?)
                """, (book_id, page_number, note))
                
                bookmark_id = cursor.lastrowid
                logger.info(f"Added bookmark for book {book_id} at page {page_number}")
                return bookmark_id
                
        except Exception as e:
            logger.error(f"Error adding book bookmark: {e}")
            raise DatabaseError(f"Failed to add book bookmark: {e}") from e
    
    def get_book_bookmarks(self, book_id: int) -> List[Dict]:
        """Get all bookmarks for a book."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM book_bookmarks WHERE book_id = ? ORDER BY page_number
                """, (book_id,))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting book bookmarks: {e}")
            raise DatabaseError(f"Failed to get book bookmarks: {e}") from e
    
    # ── App Notes ────────────────────────────────────────────────────────────
    
    def add_app_note(self, title: str, content: str, category: str = "General") -> int:
        """Save a new general study note to the database."""
        try:
            title = sanitize_string(title, max_length=200)
            content = sanitize_string(content, max_length=10000)
            category = sanitize_string(category, max_length=100)
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO app_notes (title, content, category)
                    VALUES (?, ?, ?)
                """, (title, content, category))
                
                note_id = cursor.lastrowid
                logger.info(f"Added app note: {title}")
                return note_id
                
        except Exception as e:
            logger.error(f"Error adding app note: {e}")
            raise DatabaseError(f"Failed to add app note: {e}") from e
    
    def get_app_notes(self, search: Optional[str] = None) -> List[Dict]:
        """Get all general notes, optionally filtered by search text."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                if search:
                    search_term = f"%{search}%"
                    cursor.execute("""
                        SELECT * FROM app_notes
                        WHERE title LIKE ? OR content LIKE ?
                        ORDER BY updated_at DESC
                    """, (search_term, search_term))
                else:
                    cursor.execute("SELECT * FROM app_notes ORDER BY updated_at DESC")
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting app notes: {e}")
            raise DatabaseError(f"Failed to get app notes: {e}") from e
    
    def update_app_note(self, note_id: int, title: str, content: str, category: str) -> bool:
        """Update an existing note."""
        try:
            title = sanitize_string(title, max_length=200)
            content = sanitize_string(content, max_length=10000)
            category = sanitize_string(category, max_length=100)
            
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE app_notes
                    SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (title, content, category, note_id))
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Updated app note {note_id}")
                return success
                
        except Exception as e:
            logger.error(f"Error updating app note: {e}")
            raise DatabaseError(f"Failed to update app note: {e}") from e
    
    def delete_app_note(self, note_id: int) -> bool:
        """Delete a note by ID."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM app_notes WHERE id = ?", (note_id,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Deleted app note {note_id}")
                return success
                
        except Exception as e:
            logger.error(f"Error deleting app note: {e}")
            raise DatabaseError(f"Failed to delete app note: {e}") from e
    
    def get_app_note_by_id(self, note_id: int) -> Optional[Dict]:
        """Get a single note by ID."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM app_notes WHERE id = ?", (note_id,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            logger.error(f"Error getting app note by ID: {e}")
            raise DatabaseError(f"Failed to get app note by ID: {e}") from e

    # ── Flashcard Decks ──────────────────────────────────────────────────────

    def add_flashcard_deck(self, name: str) -> int:
        """Create a new flashcard deck and return its ID."""
        try:
            name = sanitize_string(name, max_length=100)
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO flashcard_decks (name) VALUES (?)", (name,)
                )
                deck_id = cursor.lastrowid
                logger.info(f"Created flashcard deck: {name}")
                return deck_id
        except Exception as e:
            logger.error(f"Error creating flashcard deck: {e}")
            raise DatabaseError(f"Failed to create flashcard deck: {e}") from e

    def get_flashcard_decks(self) -> List[Dict]:
        """Return all flashcard decks with due-card counts."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT fd.id, fd.name, fd.created_at,
                           COUNT(f.id) AS total_cards,
                           SUM(CASE WHEN f.next_review <= date('now') THEN 1 ELSE 0 END) AS due_cards
                    FROM flashcard_decks fd
                    LEFT JOIN flashcards f ON f.deck_id = fd.id
                    GROUP BY fd.id
                    ORDER BY fd.created_at DESC
                """)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting flashcard decks: {e}")
            raise DatabaseError(f"Failed to get flashcard decks: {e}") from e

    def delete_flashcard_deck(self, deck_id: int) -> bool:
        """Delete a flashcard deck (cascades to cards)."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM flashcard_decks WHERE id = ?", (deck_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting flashcard deck: {e}")
            raise DatabaseError(f"Failed to delete flashcard deck: {e}") from e

    # ── Flashcards ───────────────────────────────────────────────────────────

    def add_flashcard(self, deck_id: int, front: str, back: str) -> int:
        """Add a card to a deck."""
        try:
            front = sanitize_string(front, max_length=1000)
            back = sanitize_string(back, max_length=1000)
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO flashcards (deck_id, front, back) VALUES (?, ?, ?)",
                    (deck_id, front, back),
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding flashcard: {e}")
            raise DatabaseError(f"Failed to add flashcard: {e}") from e

    def get_due_flashcards(self, deck_id: int) -> List[Dict]:
        """Return cards due today or earlier for the given deck."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM flashcards
                    WHERE deck_id = ? AND next_review <= date('now')
                    ORDER BY next_review ASC
                """, (deck_id,))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting due flashcards: {e}")
            raise DatabaseError(f"Failed to get due flashcards: {e}") from e

    def get_all_flashcards(self, deck_id: int) -> List[Dict]:
        """Return all cards in a deck."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM flashcards WHERE deck_id = ? ORDER BY created_at",
                    (deck_id,),
                )
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting flashcards: {e}")
            raise DatabaseError(f"Failed to get flashcards: {e}") from e

    def update_flashcard_review(
        self,
        card_id: int,
        interval_days: int,
        next_review: str,
        ease_factor: float,
        reps: int,
    ) -> None:
        """Persist SM-2 state after a review."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE flashcards
                       SET interval_days = ?, next_review = ?, ease_factor = ?, reps = ?
                       WHERE id = ?""",
                    (interval_days, next_review, ease_factor, reps, card_id),
                )
        except Exception as e:
            logger.error(f"Error updating flashcard review: {e}")
            raise DatabaseError(f"Failed to update flashcard review: {e}") from e

    def delete_flashcard(self, card_id: int) -> bool:
        """Delete a single flashcard."""
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM flashcards WHERE id = ?", (card_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting flashcard: {e}")
            raise DatabaseError(f"Failed to delete flashcard: {e}") from e

    def import_study_notes_as_flashcards(self, deck_id: int) -> int:
        """
        Import all high-yield facts from study_notes as flashcards into a deck.
        Front = 'What is this high-yield fact?', Back = the fact text.
        Returns count of cards imported.
        """
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sn.high_yield_fact, ae.title
                    FROM study_notes sn
                    LEFT JOIN academic_events ae ON sn.event_id = ae.id
                """)
                rows = cursor.fetchall()

                count = 0
                for fact, event_title in rows:
                    front = f"High-yield fact from: {event_title or 'Study Notes'}"
                    back = fact
                    cursor.execute(
                        "INSERT INTO flashcards (deck_id, front, back) VALUES (?, ?, ?)",
                        (deck_id, front, back)
                    )
                    count += 1

                logger.info(f"Imported {count} study notes as flashcards into deck {deck_id}")
                return count
        except Exception as e:
            logger.error(f"Error importing study notes as flashcards: {e}")
            raise DatabaseError(f"Failed to import study notes: {e}") from e

    def import_app_notes_as_flashcards(self, deck_id: int) -> int:
        """
        Import all app notes as flashcards into a deck.
        Creates Q&A pairs where Front = note title, Back = note content.
        Returns count of cards imported.
        """
        try:
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title, content, category
                    FROM app_notes
                """)
                rows = cursor.fetchall()

                count = 0
                for title, content, category in rows:
                    front = f"Q: {title}"
                    back = f"A: {content}"
                    if category:
                        back += f"\n\nCategory: {category}"
                    cursor.execute(
                        "INSERT INTO flashcards (deck_id, front, back) VALUES (?, ?, ?)",
                        (deck_id, front, back)
                    )
                    count += 1

                logger.info(f"Imported {count} app notes as flashcards into deck {deck_id}")
                return count
        except Exception as e:
            logger.error(f"Error importing app notes as flashcards: {e}")
            raise DatabaseError(f"Failed to import app notes: {e}") from e

    # ── Pomodoro Sessions ────────────────────────────────────────────────────

    def log_pomodoro_session(
        self, duration_minutes: int, mode: str = "work", preset: str = ""
    ) -> int:
        """Log a completed Pomodoro session."""
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            with self.connection.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO pomodoro_sessions (date, duration_minutes, mode, preset)
                       VALUES (?, ?, ?, ?)""",
                    (date_str, duration_minutes, mode, preset),
                )
                session_id = cursor.lastrowid
                logger.info(f"Logged pomodoro session: {duration_minutes}m {mode}")
                return session_id
        except Exception as e:
            logger.error(f"Error logging pomodoro session: {e}")
            raise DatabaseError(f"Failed to log pomodoro session: {e}") from e

    def get_weekly_pomodoro_summary(self) -> List[Dict]:
        """Return session counts grouped by day for the past 7 days."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date,
                           COUNT(*) AS sessions,
                           SUM(duration_minutes) AS total_minutes
                    FROM pomodoro_sessions
                    WHERE date >= date('now', '-6 days')
                      AND mode = 'work'
                    GROUP BY date
                    ORDER BY date ASC
                """)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting weekly pomodoro summary: {e}")
            raise DatabaseError(f"Failed to get weekly pomodoro summary: {e}") from e

    # ── Study Heatmap ────────────────────────────────────────────────────────

    def get_study_hours_last_n_days(self, n: int = 90) -> Dict[str, float]:
        """
        Return a dict mapping date string -> total hours for the past N days.
        Dates with no study hours are not included.
        """
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date, SUM(hours) AS total_hours
                    FROM study_hours
                    WHERE date >= date('now', ? )
                    GROUP BY date
                """, (f"-{n} days",))
                return {row[0]: float(row[1]) for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Error getting study hours heatmap data: {e}")
            raise DatabaseError(f"Failed to get study heatmap data: {e}") from e

    def get_current_study_streak(self) -> int:
        """Return the current consecutive-day study streak (days with > 0 hours)."""
        try:
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT date FROM study_hours
                    WHERE hours > 0
                    ORDER BY date DESC
                """)
                dates = [row[0] for row in cursor.fetchall()]

            if not dates:
                return 0

            streak = 0
            from datetime import date as _date, timedelta
            check = _date.today()
            for d_str in dates:
                try:
                    d = _date.fromisoformat(d_str)
                except ValueError:
                    continue
                if d == check or d == check - timedelta(days=1):
                    streak += 1
                    check = d - timedelta(days=1)
                else:
                    break
            return streak
        except Exception as e:
            logger.error(f"Error getting study streak: {e}")
            return 0

