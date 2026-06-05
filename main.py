#!/usr/bin/env python3
"""
MedFlow - Native Medical School Command Center
A lightweight, native desktop application for medical students
featuring a high-yield planner and scheduler with dark theme aesthetic.
"""

import sys
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QSplitter, QCalendarWidget, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QTimeEdit, QGroupBox, QScrollArea, QFrame, QSystemTrayIcon,
    QMenu, QMessageBox, QProgressBar, QSlider, QTabWidget, QDateEdit,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QCheckBox, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import (
    QTimer, QTime, Qt, QDateTime, QThread, Signal, QRect, QSize, QUrl
)
from PySide6.QtGui import (
    QIcon, QPainter, QColor, QPen, QBrush, QFont, QPalette, QAction
)
from PySide6.QtCharts import (
    QChart, QChartView, QLineSeries, QScatterSeries, QValueAxis, QDateTimeAxis,
    QBarSeries, QBarSet, QBarCategoryAxis
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# Color mapping for event categories — used throughout the app
CATEGORY_COLORS = {
    "Lecture":          {"bg": "#E8F4FD", "fg": "#1A73E8", "dot": "#1A73E8"},
    "Practical Lab":    {"bg": "#EDE7F6", "fg": "#7B1FA2", "dot": "#7B1FA2"},
    "Dissection":       {"bg": "#FCE4EC", "fg": "#C62828", "dot": "#C62828"},
    "Clinical Rotation":{"bg": "#E8F5E9", "fg": "#2E7D32", "dot": "#2E7D32"},
    "Study Session":    {"bg": "#FFF3E0", "fg": "#E65100", "dot": "#E65100"},
    "Exam":             {"bg": "#FFF8E1", "fg": "#F57F17", "dot": "#F57F17"},
    "Tutorial":         {"bg": "#F3E5F5", "fg": "#6A1B9A", "dot": "#6A1B9A"},
    "Other":            {"bg": "#ECEFF1", "fg": "#546E7A", "dot": "#546E7A"},
}


class Database:
    """SQLite database handler for MedFlow application"""
    
    def __init__(self, db_path: str = None):
        if db_path is None or db_path == "medflow.db":
            db_path = str(Path.home() / "medflow.db")
        self.db_path = db_path
        self.run_backup()
        self.init_database()
        
    def run_backup(self):
        """Run automated backups of the SQLite database"""
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
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_file)
            
            # Enforce retention policy: keep only the 5 most recent backups
            backups = sorted(list(backup_dir.glob("medflow_backup_*.db")), key=lambda p: p.stat().st_mtime)
            while len(backups) > 5:
                oldest = backups.pop(0)
                oldest.unlink()
        except Exception as e:
            print(f"Error creating automated backup: {e}", file=sys.stderr)
    
    def init_database(self):
        """Initialize database tables and activate WAL mode"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Activate WAL mode for high-concurrency and native performance
            try:
                cursor.execute("PRAGMA journal_mode=WAL;")
            except Exception as e:
                print(f"Error setting WAL mode: {e}", file=sys.stderr)
            
            # Academic events table with reminders
            cursor.execute("""
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
                )
            """)
            
            # Migration: Add reminder_enabled column if it doesn't exist
            try:
                cursor.execute("SELECT reminder_enabled FROM academic_events LIMIT 1")
            except sqlite3.OperationalError:
                # Column doesn't exist, add it
                cursor.execute("ALTER TABLE academic_events ADD COLUMN reminder_enabled INTEGER DEFAULT 1")
                print("Database migrated: Added reminder_enabled column to academic_events")
            
            # Migration: Add reminder_minutes column if it doesn't exist
            try:
                cursor.execute("SELECT reminder_minutes FROM academic_events LIMIT 1")
            except sqlite3.OperationalError:
                # Column doesn't exist, add it
                cursor.execute("ALTER TABLE academic_events ADD COLUMN reminder_minutes INTEGER DEFAULT 15")
                print("Database migrated: Added reminder_minutes column to academic_events")
            
            # Study notes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    high_yield_fact TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES academic_events (id)
                )
            """)
            
            # Study debt table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_debt (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES academic_events (id)
                )
            """)
            
            # Exam scores table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exam_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_name TEXT NOT NULL,
                    exam_type TEXT NOT NULL,
                    score REAL NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Study hours tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_hours (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    hours REAL NOT NULL,
                    subject TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Completed tasks tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS completed_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    completed_date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User profile table
            cursor.execute("""
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
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Library books table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS library_books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT,
                    file_path TEXT NOT NULL,
                    category TEXT DEFAULT 'General',
                    custom_category TEXT,
                    description TEXT,
                    pages INTEGER,
                    current_page INTEGER DEFAULT 0,
                    is_read INTEGER DEFAULT 0,
                    rating INTEGER,
                    notes TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_opened TIMESTAMP
                )
            """)
            
            # Bookmarks table for saving reading positions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS book_bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES library_books (id) ON DELETE CASCADE
                )
            """)

            # General study notes (persisted across sessions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'General',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def add_event(self, title: str, category: str, subtopic: str, 
                  date: str, time_start: str, time_end: str, notes: str = "",
                  reminder_minutes: int = 15, reminder_enabled: bool = True) -> int:
        """Add a new academic event with reminder settings"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO academic_events 
                (title, category, subtopic, date, time_start, time_end, notes, reminder_minutes, reminder_enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, category, subtopic, date, time_start, time_end, notes, 
                  reminder_minutes, 1 if reminder_enabled else 0))
            conn.commit()
            return cursor.lastrowid
    
    def get_upcoming_events(self, minutes_ahead: int = 30) -> List[Dict]:
        """Get events happening within the next X minutes (for reminders)"""
        now = datetime.now()
        future = now + timedelta(minutes=minutes_ahead)
        
        with sqlite3.connect(self.db_path) as conn:
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
    
    def get_events(self, date: str = None) -> List[Dict]:
        """Get events, optionally filtered by date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if date:
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
    
    def add_study_note(self, event_id: int, fact: str):
        """Add a high-yield fact for an event"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO study_notes (event_id, high_yield_fact)
                VALUES (?, ?)
            """, (event_id, fact))
            conn.commit()
    
    def get_study_notes(self, event_id: int) -> List[str]:
        """Get high-yield facts for an event"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT high_yield_fact FROM study_notes 
                WHERE event_id = ?
            """, (event_id,))
            return [row[0] for row in cursor.fetchall()]
    
    def add_study_debt(self, event_id: int, reason: str):
        """Add a study debt entry"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO study_debt (event_id, reason)
                VALUES (?, ?)
            """, (event_id, reason))
            conn.commit()
    
    def get_study_debt(self) -> List[Dict]:
        """Get all study debt entries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sd.id, sd.event_id, sd.reason, sd.created_at, ae.title, ae.category, ae.subtopic, ae.notes, ae.date 
                FROM study_debt sd
                JOIN academic_events ae ON sd.event_id = ae.id
                ORDER BY sd.created_at DESC
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def resolve_study_debt(self, event_id: int):
        """Remove a missed event from study debt"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM study_debt WHERE event_id = ?", (event_id,))
                conn.commit()
        except Exception as e:
            print(f"Error resolving study debt: {e}", file=sys.stderr)
    
    def add_exam_score(self, subject_name: str, exam_type: str, score: float, date: str, notes: str = "") -> int:
        """Add a new exam score"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO exam_scores (subject_name, exam_type, score, date, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (subject_name, exam_type, score, date, notes))
            conn.commit()
            return cursor.lastrowid
    
    def get_exam_scores(self, subject: str = None) -> List[Dict]:
        """Get exam scores, optionally filtered by subject"""
        with sqlite3.connect(self.db_path) as conn:
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
    
    def delete_exam_score(self, exam_id: int) -> bool:
        """Delete a specific exam score by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM exam_scores WHERE id = ?", (exam_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting exam score: {e}")
            return False
    
    def clear_all_exam_scores(self) -> bool:
        """Clear all exam scores - use with caution"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM exam_scores")
                conn.commit()
                return True
        except Exception as e:
            print(f"Error clearing exam scores: {e}")
            return False
    
    def save_user_profile(self, profile_data: dict) -> bool:
        """Save user profile to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_profile 
                    (id, name, school, year_of_study, graduation_year, ambitions, 
                     specialties, hobbies, study_plan, motivation, profile_picture_path, 
                     music_file_path, updated_at)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    profile_data.get('name', ''),
                    profile_data.get('school', ''),
                    profile_data.get('year', ''),
                    profile_data.get('graduation', ''),
                    profile_data.get('ambitions', ''),
                    profile_data.get('specialties', ''),
                    profile_data.get('hobbies', ''),
                    profile_data.get('study_plan', ''),
                    profile_data.get('motivation', ''),
                    profile_data.get('profile_picture', ''),
                    profile_data.get('music_file', '')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving user profile: {e}")
            return False
    
    def clear_user_profile(self) -> bool:
        """Clear user profile from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_profile WHERE id = 1")
                conn.commit()
                return True
        except Exception as e:
            print(f"Error clearing user profile: {e}")
            return False
    
    def get_user_profile(self) -> dict:
        """Get user profile from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM user_profile WHERE id = 1")
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return {}
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return {}
    
    # Library methods
    def add_library_book(self, title: str, author: str, file_path: str, 
                         category: str = "General", custom_category: str = "",
                         description: str = "", pages: int = 0) -> int:
        """Add a book to the library"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO library_books (title, author, file_path, category, 
                                          custom_category, description, pages)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, author, file_path, category, custom_category, description, pages))
            conn.commit()
            return cursor.lastrowid
    
    def get_library_books(self, category: str = None, search: str = None) -> List[Dict]:
        """Get books from library with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if category and category != "All":
                cursor.execute("""
                    SELECT * FROM library_books 
                    WHERE category = ? OR custom_category = ?
                    ORDER BY date_added DESC
                """, (category, category))
            elif search:
                cursor.execute("""
                    SELECT * FROM library_books 
                    WHERE title LIKE ? OR author LIKE ? OR description LIKE ?
                    ORDER BY date_added DESC
                """, (f"%{search}%", f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("SELECT * FROM library_books ORDER BY date_added DESC")
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_library_categories(self) -> List[str]:
        """Get all unique categories from library"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT category FROM library_books 
                UNION
                SELECT DISTINCT custom_category FROM library_books WHERE custom_category != ''
            """)
            return [row[0] for row in cursor.fetchall() if row[0]]
    
    def update_book_read_status(self, book_id: int, is_read: bool, current_page: int = None):
        """Update book read status and current page"""
        with sqlite3.connect(self.db_path) as conn:
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
            conn.commit()
    
    def update_book_rating(self, book_id: int, rating: int):
        """Update book rating"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE library_books SET rating = ? WHERE id = ?", (rating, book_id))
            conn.commit()
    
    def delete_library_book(self, book_id: int) -> bool:
        """Delete a book from the library"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM library_books WHERE id = ?", (book_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting book: {e}")
            return False
    
    def add_book_bookmark(self, book_id: int, page_number: int, note: str = ""):
        """Add a bookmark to a book"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO book_bookmarks (book_id, page_number, note)
                VALUES (?, ?, ?)
            """, (book_id, page_number, note))
            conn.commit()
    
    def get_book_bookmarks(self, book_id: int) -> List[Dict]:
        """Get all bookmarks for a book"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM book_bookmarks WHERE book_id = ? ORDER BY page_number
            """, (book_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def add_study_hours(self, date: str, hours: float, subject: str = "", notes: str = "") -> int:
        """Add study hours for a date"""
        with sqlite3.connect(self.db_path) as conn:
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
                conn.commit()
                return existing[0]
            else:
                # Insert new entry
                cursor.execute("""
                    INSERT INTO study_hours (date, hours, subject, notes)
                    VALUES (?, ?, ?, ?)
                """, (date, hours, subject, notes))
                conn.commit()
                return cursor.lastrowid
    
    def get_total_study_notes(self) -> int:
        """Get total count of study note facts."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM study_notes")
            row = cursor.fetchone()
            return int(row[0]) if row else 0
    
    def get_study_hours(self, date: str = None) -> List[Dict]:
        """Get study hours, optionally filtered by date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if date:
                cursor.execute("""
                    SELECT * FROM study_hours WHERE date = ? ORDER BY date
                """, (date,))
            else:
                cursor.execute("""
                    SELECT * FROM study_hours ORDER BY date
                """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_study_hours_for_exam_correlation(self, days_before: int = 7) -> List[Dict]:
        """Get study hours data correlated with exam scores for graphing"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get exam scores with total study hours in the week before each exam
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
    
    def add_completed_task(self, task_name: str, completed_date: str = None) -> int:
        """Add a completed task"""
        if not completed_date:
            completed_date = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO completed_tasks (task_name, completed_date)
                VALUES (?, ?)
            """, (task_name, completed_date))
            conn.commit()
            return cursor.lastrowid
    
    def get_completed_tasks_count(self, date: str = None) -> int:
        """Get count of completed tasks for a date (or all time if no date)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if date:
                cursor.execute("""
                    SELECT COUNT(*) FROM completed_tasks WHERE completed_date = ?
                """, (date,))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM completed_tasks
                """)
            return cursor.fetchone()[0]
    
    def get_completed_tasks(self, date: str = None) -> List[str]:
        """Get list of completed task names"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if date:
                cursor.execute("""
                    SELECT task_name FROM completed_tasks WHERE completed_date = ?
                """, (date,))
            else:
                cursor.execute("""
                    SELECT task_name FROM completed_tasks
                """)
            return [row[0] for row in cursor.fetchall()]

    # ── App Notes (persistent general notes) ──────────────────────────────

    def add_app_note(self, title: str, content: str, category: str = "General") -> int:
        """Save a new general study note to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO app_notes (title, content, category)
                VALUES (?, ?, ?)
            """, (title, content, category))
            conn.commit()
            return cursor.lastrowid

    def get_app_notes(self, search: str = None) -> List[Dict]:
        """Get all general notes, optionally filtered by search text"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if search:
                cursor.execute("""
                    SELECT * FROM app_notes
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY updated_at DESC
                """, (f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("SELECT * FROM app_notes ORDER BY updated_at DESC")
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def update_app_note(self, note_id: int, title: str, content: str, category: str) -> bool:
        """Update an existing note"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE app_notes
                    SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (title, content, category, note_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating note: {e}", file=sys.stderr)
            return False

    def delete_app_note(self, note_id: int) -> bool:
        """Delete a note by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM app_notes WHERE id = ?", (note_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting note: {e}", file=sys.stderr)
            return False

    def get_app_note_by_id(self, note_id: int) -> Optional[Dict]:
        """Get a single note by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM app_notes WHERE id = ?", (note_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def mark_event_completed(self, event_id: int, completed: bool) -> bool:
        """Toggle the completed state of an academic event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE academic_events SET completed = ? WHERE id = ?",
                    (1 if completed else 0, event_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error marking event completed: {e}", file=sys.stderr)
            return False


class PulseTimer(QWidget):
    """Pomodoro-style timer — pink-themed, with session counter and break mode."""

    timer_finished = Signal()

    # Modes
    MODE_WORK  = "work"
    MODE_BREAK = "break"

    PRESETS = {
        "🍅  Pomodoro  25 min":  (25, 5),
        "🧠  Deep Work  50 min": (50, 10),
        "⚡  Blitz  15 min":     (15, 3),
    }

    def __init__(self):
        super().__init__()
        self.total_time     = 25 * 60
        self.time_remaining = 25 * 60
        self.break_time     = 5  * 60
        self.is_running     = False
        self.mode           = self.MODE_WORK
        self.sessions_done  = 0

        self._pulse_tick = 0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_ring)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.init_ui()

    # ── UI ──────────────────────────────────────────────────────────────────

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Header row ────────────────────────────────────────────────────
        header = QHBoxLayout()
        self._title_lbl = QLabel("⏱️  Focus Timer")
        self._title_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #FF6B9D;"
        )
        header.addWidget(self._title_lbl)
        header.addStretch()

        self._session_lbl = QLabel("Sessions: 0")
        self._session_lbl.setStyleSheet(
            "font-size: 12px; color: #8B6B7A;"
            "background:#FFE4E8; padding:4px 10px; border-radius:10px;"
        )
        header.addWidget(self._session_lbl)
        layout.addLayout(header)

        # ── Mode badge ────────────────────────────────────────────────────
        self._mode_lbl = QLabel("FOCUS")
        self._mode_lbl.setAlignment(Qt.AlignCenter)
        self._mode_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; letter-spacing: 2px;"
            "color: white; background: #FF6B9D;"
            "padding: 4px 16px; border-radius: 10px;"
        )
        layout.addWidget(self._mode_lbl, 0, Qt.AlignCenter)

        # ── Progress ring ─────────────────────────────────────────────────
        self.progress_ring = ProgressRing()
        self.progress_ring.setFixedSize(210, 210)
        layout.addWidget(self.progress_ring, 0, Qt.AlignCenter)

        # ── Time label (drawn inside ring via overlay trick) ──────────────
        self.timer_label = QLabel("25:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet(
            "font-size: 48px; font-weight: 700; color: #FF6B9D;"
            "background: transparent; letter-spacing: 2px;"
        )
        layout.addWidget(self.timer_label)

        # ── Preset selector ───────────────────────────────────────────────
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(list(self.PRESETS.keys()))
        self._preset_combo.setMinimumHeight(36)
        self._preset_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 6px 12px;
                border-radius: 10px;
                font-size: 13px;
            }
            QComboBox:focus { border: 2px solid #FF6B9D; }
        """)
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        layout.addWidget(self._preset_combo)

        # ── Control buttons ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setMinimumHeight(44)
        self.start_btn.setStyleSheet(self._btn_css("#FF6B9D", "white", "#FF8FA3"))
        self.start_btn.clicked.connect(self.start_timer)
        self.start_btn.setToolTip("Start / resume the timer  (Space)")
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏸  Pause")
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setStyleSheet(self._btn_css("#FFE4E8", "#8B6B7A", "#FFD1DC", border="#FFD1DC"))
        self.stop_btn.clicked.connect(self.stop_timer)
        btn_row.addWidget(self.stop_btn)

        self.reset_btn = QPushButton("↺  Reset")
        self.reset_btn.setMinimumHeight(44)
        self.reset_btn.setStyleSheet(self._btn_css("#FFE4E8", "#8B6B7A", "#FFD1DC", border="#FFD1DC"))
        self.reset_btn.clicked.connect(self.reset_timer)
        btn_row.addWidget(self.reset_btn)

        layout.addLayout(btn_row)

        # ── Break button ──────────────────────────────────────────────────
        self._break_btn = QPushButton("☕  Take a Break")
        self._break_btn.setMinimumHeight(38)
        self._break_btn.setStyleSheet(self._btn_css("#FFF3E0", "#E65100", "#FFE0B2", border="#FFE0B2"))
        self._break_btn.clicked.connect(self._start_break)
        self._break_btn.setToolTip("Switch to a short break countdown")
        layout.addWidget(self._break_btn)

        layout.addStretch()

    # ── helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _btn_css(bg, fg, hover_bg, border="none"):
        border_decl = f"border: 2px solid {border};" if border != "none" else "border: none;"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                {border_decl}
                padding: 10px 18px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {hover_bg}; }}
            QPushButton:pressed {{ opacity: 0.85; }}
        """

    def _on_preset_changed(self, text: str):
        work_min, break_min = self.PRESETS[text]
        self.break_time = break_min * 60
        self.stop_timer()
        self.total_time     = work_min * 60
        self.time_remaining = work_min * 60
        self.mode = self.MODE_WORK
        self._update_mode_ui()
        self.update_display()

    def _update_mode_ui(self):
        if self.mode == self.MODE_WORK:
            self._mode_lbl.setText("FOCUS")
            self._mode_lbl.setStyleSheet(
                "font-size: 11px; font-weight: 700; letter-spacing: 2px;"
                "color: white; background: #FF6B9D;"
                "padding: 4px 16px; border-radius: 10px;"
            )
            self.timer_label.setStyleSheet(
                "font-size: 48px; font-weight: 700; color: #FF6B9D;"
                "background: transparent; letter-spacing: 2px;"
            )
        else:
            self._mode_lbl.setText("BREAK ☕")
            self._mode_lbl.setStyleSheet(
                "font-size: 11px; font-weight: 700; letter-spacing: 2px;"
                "color: white; background: #E65100;"
                "padding: 4px 16px; border-radius: 10px;"
            )
            self.timer_label.setStyleSheet(
                "font-size: 48px; font-weight: 700; color: #E65100;"
                "background: transparent; letter-spacing: 2px;"
            )

    def _pulse_ring(self):
        """Animate ring color while running"""
        self._pulse_tick = (self._pulse_tick + 1) % 2
        alpha = 180 if self._pulse_tick == 0 else 255
        self.progress_ring.set_pulse_alpha(alpha)

    # ── Timer control ────────────────────────────────────────────────────────

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_btn.setText("⏸  Running…")
            self.start_btn.setStyleSheet(self._btn_css("#FFD1DC", "#FF6B9D", "#FFB6C1"))
            self.timer.start(1000)
            self._pulse_timer.start(600)

    def stop_timer(self):
        self.is_running = False
        self.start_btn.setText("▶  Start")
        self.start_btn.setStyleSheet(self._btn_css("#FF6B9D", "white", "#FF8FA3"))
        self.timer.stop()
        self._pulse_timer.stop()
        self.progress_ring.set_pulse_alpha(255)

    def reset_timer(self):
        self.stop_timer()
        self.mode = self.MODE_WORK
        self.time_remaining = self.total_time
        self._update_mode_ui()
        self.update_display()

    def _start_break(self):
        self.stop_timer()
        self.mode = self.MODE_BREAK
        self.time_remaining = self.break_time
        self.total_time = self.break_time
        self._update_mode_ui()
        self.update_display()
        self.start_timer()

    def set_preset(self, work_minutes: int, break_minutes: int):
        self.break_time = break_minutes * 60
        self.stop_timer()
        self.total_time     = work_minutes * 60
        self.time_remaining = work_minutes * 60
        self.mode = self.MODE_WORK
        self._update_mode_ui()
        self.update_display()

    def update_timer(self):
        if self.time_remaining > 0:
            self.time_remaining -= 1
            self.update_display()
        else:
            self.stop_timer()
            if self.mode == self.MODE_WORK:
                self.sessions_done += 1
                self._session_lbl.setText(f"Sessions: {self.sessions_done}")
            self.timer_finished.emit()

    def update_display(self):
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
        progress = 1.0 - (self.time_remaining / self.total_time) if self.total_time > 0 else 0.0
        self.progress_ring.set_progress(max(0.0, min(1.0, progress)))


class ProgressRing(QWidget):
    """Custom progress ring widget — pink-themed with optional pulse alpha."""

    def __init__(self):
        super().__init__()
        self.progress    = 0.0
        self._pulse_alpha = 255  # 255 = fully visible, lower = dimmed for pulse

    def set_progress(self, value: float):
        self.progress = value
        self.update()

    def set_pulse_alpha(self, alpha: int):
        self._pulse_alpha = alpha
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        margin = 12
        rect_size = min(w, h) - margin * 2

        # Background track
        painter.setPen(QPen(QColor("#FFE4E8"), 9))
        painter.drawEllipse(margin, margin, rect_size, rect_size)

        if self.progress <= 0:
            return

        start_angle = 90 * 16
        span_angle  = -int(self.progress * 360 * 16)
        a           = self._pulse_alpha

        # Glow bloom
        painter.setPen(QPen(QColor(255, 107, 157, max(0, min(50, int(a * 0.2)))), 18))
        painter.drawArc(margin, margin, rect_size, rect_size, start_angle, span_angle)

        # Soft halo
        painter.setPen(QPen(QColor(255, 107, 157, max(0, min(130, int(a * 0.5)))), 11))
        painter.drawArc(margin, margin, rect_size, rect_size, start_angle, span_angle)

        # Core arc
        painter.setPen(QPen(QColor(255, 107, 157, a), 7))
        painter.drawArc(margin, margin, rect_size, rect_size, start_angle, span_angle)

        # Highlight
        painter.setPen(QPen(QColor(255, 255, 255, max(0, min(220, int(a * 0.86)))), 2))
        painter.drawArc(margin, margin, rect_size, rect_size, start_angle, span_angle)


class AcademicLedger(QWidget):
    """Calendar and event management widget"""
    
    event_selected = Signal(int)
    
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.selected_date = datetime.now().strftime("%Y-%m-%d")
        self.init_ui()
        self.load_events()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("📅 Schedule & Events")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #FF6B9D;")
        layout.addWidget(title)
        
        # Calendar — light pink theme
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumHeight(280)
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                color: #4A4A4A;
                font-size: 13px;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
            }
            QCalendarWidget QToolButton {
                color: #FF6B9D;
                background-color: #FFF5F7;
                padding: 8px;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #FFD1DC;
            }
            QCalendarWidget QAbstractItemView {
                background-color: white;
                color: #4A4A4A;
                selection-color: white;
                selection-background-color: #FF6B9D;
                font-size: 13px;
                outline: none;
            }
            QCalendarWidget QAbstractItemView:enabled {
                padding: 4px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #FFF5F7;
                border-bottom: 1px solid #FFD1DC;
                border-radius: 10px;
            }
        """)
        self.calendar.clicked.connect(self.on_date_selected)
        layout.addWidget(self.calendar)
        
        # Events section
        events_label = QLabel("📌 Events for Selected Date")
        events_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #FF6B9D; margin-top: 6px;")
        layout.addWidget(events_label)
        
        # Event list
        self.event_list = QListWidget()
        self.event_list.setMinimumHeight(180)
        self.event_list.setStyleSheet("""
            QListWidget {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                border-radius: 10px;
                padding: 8px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
                margin: 2px 0px;
            }
            QListWidget::item:selected {
                background-color: #FFD1DC;
                color: #FF6B9D;
            }
            QListWidget::item:hover {
                background-color: #FFE4E8;
            }
        """)
        self.event_list.itemClicked.connect(self.on_event_selected)
        layout.addWidget(self.event_list)
        
        # Add event button
        self.add_event_btn = QPushButton("➕ Add New Event")
        self.add_event_btn.setMinimumHeight(45)
        self.add_event_btn.setToolTip("Add a new academic event for the selected date (Ctrl+N)")
        self.add_event_btn.clicked.connect(self.show_add_event_dialog)
        self.add_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #00D4FF;
                color: #0A0E14;
                border: none;
                padding: 12px 20px;
                font-weight: bold;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #00A8CC;
            }
        """)
        layout.addWidget(self.add_event_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def on_date_selected(self, date):
        self.selected_date = date.toString("yyyy-MM-dd")
        self.load_events()
    
    def on_event_selected(self, item):
        event_id = item.data(Qt.UserRole)
        self.event_selected.emit(event_id)
    
    def load_events(self):
        self.event_list.clear()
        events = self.db.get_events(self.selected_date)
        
        for event in events:
            item = QListWidgetItem(f"{event['time_start']} - {event['title']} ({event['category']})")
            item.setData(Qt.UserRole, event['id'])
            self.event_list.addItem(item)
    
    def show_add_event_dialog(self):
        dialog = AddEventDialog(self.db, self.selected_date)
        if dialog.exec():
            self.load_events()


class FullPageSchedulePlanner(QWidget):
    """Full-page dedicated schedule planner with large calendar and reminders"""
    
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.selected_date = datetime.now().strftime("%Y-%m-%d")
        self.current_view = "month"  # month, week, day
        self.init_ui()
        self.load_schedule()
        self.start_reminder_timer()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header with title and view controls
        header = QHBoxLayout()
        
        title = QLabel("📅 Medical School Planner")
        title.setStyleSheet("""
            font-size: 32px; 
            font-weight: 700; 
            color: #FF6B9D;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # View toggle buttons
        self.month_btn = QPushButton("Month")
        self.week_btn = QPushButton("Week")
        self.day_btn = QPushButton("Day")
        
        for btn in [self.month_btn, self.week_btn, self.day_btn]:
            btn.setMinimumHeight(42)
            btn.setMinimumWidth(90)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFE4E8;
                    color: #8B6B7A;
                    border: 2px solid #FFD1DC;
                    padding: 10px 20px;
                    font-weight: 600;
                    border-radius: 10px;
                    font-size: 14px;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                }
                QPushButton:checked {
                    background-color: #FF6B9D;
                    color: white;
                    border: 2px solid #FF6B9D;
                }
                QPushButton:hover:!checked {
                    background-color: #FFD1DC;
                }
            """)
            btn.setCheckable(True)
            header.addWidget(btn)
        
        self.month_btn.setChecked(True)
        self.month_btn.clicked.connect(lambda: self.set_view("month"))
        self.week_btn.clicked.connect(lambda: self.set_view("week"))
        self.day_btn.clicked.connect(lambda: self.set_view("day"))
        
        # Add Event button
        add_btn = QPushButton("➕ Add Event")
        add_btn.setMinimumHeight(48)
        add_btn.setMinimumWidth(150)
        add_btn.setToolTip("Add a new event for the selected date  (Ctrl+N)")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 14px 28px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
            QPushButton:pressed {
                background-color: #FF5280;
            }
        """)
        add_btn.clicked.connect(self.show_add_event_dialog)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Main content area - splitter for calendar and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Large Calendar
        calendar_container = QWidget()
        calendar_layout = QVBoxLayout()
        calendar_layout.setSpacing(15)
        
        # Navigation
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Previous")
        self.next_btn = QPushButton("Next ▶")
        self.today_btn = QPushButton("📍 Today")
        
        for btn in [self.prev_btn, self.today_btn, self.next_btn]:
            btn.setMinimumHeight(45)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFE4E8;
                    color: #8B6B7A;
                    border: 2px solid #FFD1DC;
                    padding: 12px 24px;
                    font-weight: 600;
                    border-radius: 12px;
                    font-size: 14px;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                }
                QPushButton:hover {
                    background-color: #FFD1DC;
                    color: #FF6B9D;
                }
                QPushButton:pressed {
                    background-color: #FF6B9D;
                    color: white;
                }
            """)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.today_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()
        
        calendar_layout.addLayout(nav_layout)
        
        # Large Calendar Widget
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumHeight(600)
        self.calendar.setGridVisible(True)
        self.calendar.setFirstDayOfWeek(Qt.Monday)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.LongDayNames)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.ISOWeekNumbers)
        
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #FFF8FA;
                color: #4A4A4A;
                font-size: 16px;
                border: 3px solid #FFD1DC;
                border-radius: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                padding: 10px;
            }
            QCalendarWidget QToolButton {
                color: white;
                background-color: #FF6B9D;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 10px;
                border: none;
                margin: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #FF8FA3;
            }
            QCalendarWidget QToolButton:pressed {
                background-color: #FF5280;
            }
            QCalendarWidget QMenu {
                background-color: white;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                border-radius: 10px;
                padding: 10px;
            }
            QCalendarWidget QMenu::item {
                padding: 10px;
                border-radius: 8px;
            }
            QCalendarWidget QMenu::item:selected {
                background-color: #FFD1DC;
                color: #FF6B9D;
            }
            QCalendarWidget QAbstractItemView {
                background-color: white;
                color: #4A4A4A;
                selection-color: white;
                selection-background-color: #FF6B9D;
                font-size: 15px;
                padding: 15px;
                border-radius: 10px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                padding: 12px;
                border-radius: 10px;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #E0E0E0;
            }
            QCalendarWidget #qt_calendar_navigationbar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #FF6B9D, stop:1 #FFB6C1);
                padding: 15px;
                border-radius: 15px 15px 0 0;
            }
            QCalendarWidget #qt_calendar_monthbutton {
                color: white;
                font-size: 18px;
                font-weight: 700;
                padding: 8px 15px;
            }
            QCalendarWidget #qt_calendar_yearbutton {
                color: white;
                font-size: 18px;
                font-weight: 700;
                padding: 8px 15px;
            }
            /* Day headers (Mon, Tue, Wed...) */
            QCalendarWidget QWidget {
                alternate-background-color: #FFF5F7;
            }
        """)
        
        self.prev_btn.clicked.connect(self.calendar.showPreviousMonth)
        self.next_btn.clicked.connect(self.calendar.showNextMonth)
        self.today_btn.clicked.connect(self.calendar.showSelectedDate)
        self.calendar.clicked.connect(self.on_date_selected)
        
        calendar_layout.addWidget(self.calendar)
        calendar_container.setLayout(calendar_layout)
        splitter.addWidget(calendar_container)
        
        # Right side - Events list and details
        details_container = QWidget()
        details_layout = QVBoxLayout()
        details_layout.setSpacing(20)
        
        # Selected date display
        self.date_label = QLabel("Selected Date: " + self.selected_date)
        self.date_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: 600; 
            color: #FF6B9D;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        details_layout.addWidget(self.date_label)
        
        # Timer section - COMPACT VERSION
        timer_group = QGroupBox("⏱️ Timer")
        timer_group.setStyleSheet("""
            QGroupBox { 
                font-size: 14px; 
                color: #FF6B9D; 
                font-weight: 600; 
                padding-top: 8px;
                border: 2px solid #FFD1DC;
                border-radius: 10px;
                margin-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        timer_layout = QVBoxLayout()
        timer_layout.setSpacing(5)
        timer_layout.setContentsMargins(8, 8, 8, 8)
        
        # Current event display - compact
        self.current_event_label = QLabel("No event selected")
        self.current_event_label.setStyleSheet("""
            font-size: 11px;
            color: #8B6B7A;
            padding: 2px;
            font-style: italic;
        """)
        self.current_event_label.setWordWrap(True)
        timer_layout.addWidget(self.current_event_label)
        
        # Timer display - smaller
        self.session_timer_label = QLabel("25:00")
        self.session_timer_label.setAlignment(Qt.AlignCenter)
        self.session_timer_label.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #FF6B9D;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            padding: 5px;
        """)
        timer_layout.addWidget(self.session_timer_label)
        
        # Timer controls - compact horizontal
        timer_controls = QHBoxLayout()
        timer_controls.setSpacing(5)
        
        self.start_timer_btn = QPushButton("▶")
        self.start_timer_btn.setMinimumHeight(32)
        self.start_timer_btn.setMaximumWidth(50)
        self.start_timer_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 5px;
                font-weight: 700;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
        """)
        self.start_timer_btn.setToolTip("Start")
        self.start_timer_btn.clicked.connect(self.start_event_timer)
        
        self.stop_timer_btn = QPushButton("⏸")
        self.stop_timer_btn.setMinimumHeight(32)
        self.stop_timer_btn.setMaximumWidth(50)
        self.stop_timer_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB6C1;
                color: white;
                border: none;
                padding: 5px;
                font-weight: 700;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
        """)
        self.stop_timer_btn.setToolTip("Pause")
        self.stop_timer_btn.clicked.connect(self.stop_event_timer)
        
        self.reset_timer_btn = QPushButton("↺")
        self.reset_timer_btn.setMinimumHeight(32)
        self.reset_timer_btn.setMaximumWidth(50)
        self.reset_timer_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE4E8;
                color: #8B6B7A;
                border: 2px solid #FFD1DC;
                padding: 5px;
                font-weight: 700;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FFD1DC;
            }
        """)
        self.reset_timer_btn.setToolTip("Reset")
        self.reset_timer_btn.clicked.connect(self.reset_event_timer)
        
        timer_controls.addWidget(self.start_timer_btn)
        timer_controls.addWidget(self.stop_timer_btn)
        timer_controls.addWidget(self.reset_timer_btn)
        timer_layout.addLayout(timer_controls)
        
        # Timer presets - compact
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(5)
        self.preset_25 = QPushButton("25'")
        self.preset_50 = QPushButton("50'")
        for btn in [self.preset_25, self.preset_50]:
            btn.setMinimumHeight(28)
            btn.setMaximumWidth(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFF5F7;
                    color: #FF6B9D;
                    border: 1px solid #FFD1DC;
                    padding: 3px;
                    font-weight: 500;
                    border-radius: 5px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #FFD1DC;
                }
            """)
        self.preset_25.clicked.connect(lambda: self.set_timer_preset(25))
        self.preset_50.clicked.connect(lambda: self.set_timer_preset(50))
        presets_layout.addWidget(self.preset_25)
        presets_layout.addWidget(self.preset_50)
        presets_layout.addStretch()
        timer_layout.addLayout(presets_layout)
        
        timer_group.setLayout(timer_layout)
        details_layout.addWidget(timer_group)
        
        # Initialize timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_event_timer)
        self.timer_remaining = 25 * 60
        self.timer_duration_minutes = 25  # Track original duration for study hours
        self.current_timer_event = None
        
        # Upcoming reminders section with pulsing header
        reminders_group = QGroupBox("")
        reminders_header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.reminders_icon = QLabel("🔔")
        self.reminders_icon.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(self.reminders_icon)
        
        reminders_title = QLabel("Upcoming Reminders")
        reminders_title.setStyleSheet("""
            font-size: 16px; 
            color: #FF6B9D; 
            font-weight: 700;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        header_layout.addWidget(reminders_title)
        header_layout.addStretch()
        
        # Pulsing indicator
        self.pulse_label = QLabel("●")
        self.pulse_label.setStyleSheet("""
            font-size: 14px;
            color: #FF6B9D;
        """)
        header_layout.addWidget(self.pulse_label)
        
        reminders_header.setLayout(header_layout)
        reminders_group.setStyleSheet("""
            QGroupBox { 
                padding-top: 15px;
                border: 3px solid #FF6B9D;
                border-radius: 15px;
                background-color: #FFF8FA;
            }
        """)
        
        reminders_layout = QVBoxLayout()
        reminders_layout.addWidget(reminders_header)
        
        self.reminders_list = QListWidget()
        self.reminders_list.setMinimumHeight(140)
        self.reminders_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding: 12px;
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QListWidget::item {
                background-color: #FFF5F7;
                padding: 12px;
                margin: 4px 0px;
                border-radius: 8px;
                border-left: 4px solid #FF6B9D;
            }
            QListWidget::item:hover {
                background-color: #FFE4E8;
            }
        """)
        reminders_layout.addWidget(self.reminders_list)
        
        # Check reminders button
        snooze_btn = QPushButton("🔔 CHECK NOW")
        snooze_btn.setMinimumHeight(45)
        snooze_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #FF6B9D, stop:1 #FFB6C1);
                color: white;
                border: none;
                padding: 12px 24px;
                font-weight: 700;
                border-radius: 10px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #FF8FA3, stop:1 #FFC0CB);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #FF5280, stop:1 #FF69B4);
            }
        """)
        snooze_btn.clicked.connect(self.check_reminders)
        reminders_layout.addWidget(snooze_btn)
        
        reminders_group.setLayout(reminders_layout)
        details_layout.addWidget(reminders_group)
        
        # Events for selected date
        events_group = QGroupBox("📋 Events for Selected Date")
        events_group.setStyleSheet("""
            QGroupBox { 
                font-size: 16px; 
                color: #FF6B9D; 
                font-weight: 600; 
                padding-top: 15px;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
            }
        """)
        events_layout = QVBoxLayout()
        
        self.events_list = QListWidget()
        self.events_list.setMinimumHeight(250)
        self.events_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QListWidget::item {
                background-color: #FFF5F7;
                padding: 15px;
                margin: 5px 0px;
                border-radius: 10px;
                border: 1px solid #FFE4E8;
            }
            QListWidget::item:selected {
                background-color: #FFD1DC;
                color: #FF6B9D;
                border: 2px solid #FF6B9D;
            }
            QListWidget::item:hover {
                background-color: #FFE4E8;
            }
        """)
        self.events_list.itemClicked.connect(self.on_event_selected)
        self.events_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.events_list.customContextMenuRequested.connect(self._events_context_menu)
        events_layout.addWidget(self.events_list)
        
        events_group.setLayout(events_layout)
        details_layout.addWidget(events_group)
        
        # Quick stats
        stats_label = QLabel("💡 Click any event to start a focus timer for that session. You'll get reminders before events start.")
        stats_label.setStyleSheet("""
            color: #8B6B7A; 
            font-size: 13px; 
            padding: 15px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        stats_label.setWordWrap(True)
        details_layout.addWidget(stats_label)
        
        details_layout.addStretch()
        details_container.setLayout(details_layout)
        splitter.addWidget(details_container)
        
        # Set splitter ratio (60% calendar, 40% details)
        splitter.setSizes([900, 600])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def set_view(self, view: str):
        """Switch between month/week/day views"""
        self.current_view = view
        self.month_btn.setChecked(view == "month")
        self.week_btn.setChecked(view == "week")
        self.day_btn.setChecked(view == "day")
        
        # For now, we only have month view implemented in QCalendarWidget
        # Week and day views would need custom implementations
        if view == "month":
            self.calendar.showSelectedDate()
    
    def on_date_selected(self, date):
        """Handle date selection from calendar"""
        self.selected_date = date.toString("yyyy-MM-dd")
        self.date_label.setText("Selected Date: " + self.selected_date)
        self.load_schedule()
    
    def on_event_selected(self, item):
        """Handle event selection - update timer with event info"""
        event_id = item.data(Qt.UserRole)
        events = self.db.get_events(self.selected_date)
        
        for event in events:
            if event['id'] == event_id:
                self.current_timer_event = event
                self.current_event_label.setText(
                    f"⏱️ Timing: {event['title']}\n🕐 {event['time_start']} - {event['time_end']}"
                )
                self.timer_remaining = 25 * 60  # Reset to 25 min
                self.update_timer_display()
                break
    
    def load_schedule(self):
        """Load events for selected date and upcoming reminders"""
        # Load events for selected date
        self.events_list.clear()
        events = self.db.get_events(self.selected_date)
        
        for event in events:
            reminder_text = "🔔 " if event.get('reminder_enabled') else ""
            time_str = f"{event['time_start']} - {event['time_end']}"
            completed = bool(event.get('completed'))
            done_mark = "✓ " if completed else ""

            # Calculate duration for display
            try:
                h1, m1 = map(int, event['time_start'].split(":"))
                h2, m2 = map(int, event['time_end'].split(":"))
                dur = (h2 * 60 + m2) - (h1 * 60 + m1)
                dur_str = f" · {dur}min" if dur > 0 else ""
            except Exception:
                dur_str = ""

            text = f"{done_mark}{reminder_text}{time_str}{dur_str}\n{event['title']}  [{event['category']}]"
            if event.get('subtopic'):
                text += f"\n  └ {event['subtopic']}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, event['id'])

            # Color-code by category
            colors = CATEGORY_COLORS.get(event['category'], CATEGORY_COLORS["Other"])
            if completed:
                item.setForeground(QColor("#AAAAAA"))
                item.setBackground(QColor("#F5F5F5"))
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
            else:
                item.setForeground(QColor(colors["fg"]))
                item.setBackground(QColor(colors["bg"]))

            self.events_list.addItem(item)
        
        # Load upcoming reminders
        self.reminders_list.clear()
        upcoming = self.db.get_upcoming_events(minutes_ahead=60)
        
        for event in upcoming:
            text = f"🔔 {event['time_start']} - {event['title']}"
            self.reminders_list.addItem(text)
        
        if not upcoming:
            self.reminders_list.addItem("No upcoming reminders")
    
    def show_add_event_dialog(self):
        """Show dialog to add new event"""
        dialog = AddEventDialog(self.db, self.selected_date)
        if dialog.exec():
            self.load_schedule()
    
    def _events_context_menu(self, pos):
        """Right-click context menu on the events list"""
        item = self.events_list.itemAt(pos)
        if not item:
            return
        event_id = item.data(Qt.UserRole)

        # Find current completed state from DB
        events = self.db.get_events(self.selected_date)
        target = next((e for e in events if e['id'] == event_id), None)
        if not target:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #FFD1DC;
                border-radius: 10px;
                padding: 6px;
                font-size: 14px;
                color: #4A4A4A;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #FFE4E8;
                color: #FF6B9D;
            }
        """)

        if target.get('completed'):
            action_toggle = menu.addAction("↩ Mark as Incomplete")
        else:
            action_toggle = menu.addAction("✓ Mark as Complete")

        action = menu.exec(self.events_list.mapToGlobal(pos))
        if action == action_toggle:
            new_state = not bool(target.get('completed'))
            self.db.mark_event_completed(event_id, new_state)
            self.load_schedule()

    def start_reminder_timer(self):
        """Start timer to check for reminders every minute"""
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # Check every minute
        
        # Start pulse animation for visual alert
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.animate_pulse)
        self.pulse_timer.start(1000)  # Pulse every second
        self.pulse_state = 0
    
    def animate_pulse(self):
        """Animate the reminder pulse indicator"""
        self.pulse_state = (self.pulse_state + 1) % 2
        if self.pulse_state == 0:
            self.pulse_label.setStyleSheet("""
                font-size: 20px;
                color: #FF6B9D;
                font-weight: bold;
            """)
            self.reminders_icon.setStyleSheet("font-size: 24px;")
        else:
            self.pulse_label.setStyleSheet("""
                font-size: 16px;
                color: #FFB6C1;
                font-weight: normal;
            """)
            self.reminders_icon.setStyleSheet("font-size: 18px;")
    
    def start_event_timer(self):
        """Start the Pomodoro timer for the selected event"""
        if not self.timer.isActive():
            # Calculate total minutes from remaining time for study hours
            self.timer_duration_minutes = self.timer_remaining // 60
            self.timer.start(1000)  # Update every second
    
    def stop_event_timer(self):
        """Stop the timer"""
        self.timer.stop()
    
    def reset_event_timer(self):
        """Reset timer to 25 minutes"""
        self.timer.stop()
        self.timer_remaining = 25 * 60
        self.update_timer_display()
    
    def set_timer_preset(self, minutes: int):
        """Set timer to specific preset"""
        self.timer.stop()
        self.timer_remaining = minutes * 60
        self.timer_duration_minutes = minutes
        self.update_timer_display()
    
    def update_event_timer(self):
        """Update the timer countdown"""
        if self.timer_remaining > 0:
            self.timer_remaining -= 1
            self.update_timer_display()
        else:
            self.timer.stop()
            # Calculate study hours contributed
            total_minutes = self.timer_duration_minutes
            hours = total_minutes / 60.0
            
            # Add to study hours if event selected
            if self.current_timer_event and hours > 0:
                today = datetime.now().strftime("%Y-%m-%d")
                subject = self.current_timer_event.get('title', 'Study Session')
                self.db.add_study_hours(
                    date=today,
                    hours=hours,
                    subject=subject,
                    notes=f"Pomodoro timer session ({total_minutes} minutes)"
                )
                
                # Show notification
                title = self.current_timer_event['title']
                QMessageBox.information(
                    self,
                    "⏱️ Session Complete!",
                    f"Great work! You've completed a {total_minutes}-minute study session for:\n\n"
                    f"📚 {title}\n\n"
                    f"{hours:.1f} hours have been added to your study log! 🎉"
                )
            else:
                QMessageBox.information(
                    self,
                    "⏱️ Timer Finished",
                    f"Your {total_minutes}-minute timer has finished! 🎉"
                )
    
    def update_timer_display(self):
        """Update the timer label"""
        minutes = self.timer_remaining // 60
        seconds = self.timer_remaining % 60
        self.session_timer_label.setText(f"{minutes:02d}:{seconds:02d}")
    
    def check_reminders(self):
        """Check for upcoming events and show notifications"""
        upcoming = self.db.get_upcoming_events(minutes_ahead=15)
        
        for event in upcoming:
            # Show system notification
            if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    "📅 Upcoming Event",
                    f"{event['title']} at {event['time_start']}",
                    QSystemTrayIcon.Information,
                    5000
                )
        
        self.load_schedule()


class AddEventDialog(QDialog):
    """Dialog for adding new academic events with reminders"""
    
    def __init__(self, database: Database, date: str):
        super().__init__()
        self.db = database
        self.date = date
        self.setWindowModality(Qt.ApplicationModal)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("➕ Add Academic Event")
        self.setMinimumSize(450, 500)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Title
        title = QLabel("Add New Event")
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: 600; 
            color: #FF6B9D;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        layout.addWidget(title)
        
        # Form container
        form_widget = QWidget()
        form_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
                border: 2px solid #FFD1DC;
            }
            QLabel {
                color: #4A4A4A;
                font-size: 14px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QLineEdit, QComboBox, QTextEdit, QSpinBox, QTimeEdit {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 12px;
                border-radius: 10px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus, QTimeEdit:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        # Event Title
        form_layout.addWidget(QLabel("📌 Event Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g., Anatomy Lecture - Lower Limb")
        form_layout.addWidget(self.title_input)
        
        # Category
        form_layout.addWidget(QLabel("📚 Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Lecture", "Practical Lab", "Dissection", "Clinical Rotation", "Study Session", "Exam", "Other"])
        self.category_combo.setMinimumHeight(40)
        form_layout.addWidget(self.category_combo)
        
        # Subtopic
        form_layout.addWidget(QLabel("📝 Subtopic (Optional):"))
        self.subtopic_input = QLineEdit()
        self.subtopic_input.setPlaceholderText("e.g., Femoral Triangle, Brachial Plexus")
        form_layout.addWidget(self.subtopic_input)
        
        # Time selection
        time_layout = QHBoxLayout()
        
        time_start_layout = QVBoxLayout()
        time_start_layout.addWidget(QLabel("🕐 Start Time:"))
        self.time_start = QTimeEdit()
        self.time_start.setTime(QTime(9, 0))
        self.time_start.setMinimumHeight(40)
        time_start_layout.addWidget(self.time_start)
        
        time_end_layout = QVBoxLayout()
        time_end_layout.addWidget(QLabel("🕐 End Time:"))
        self.time_end = QTimeEdit()
        self.time_end.setTime(QTime(10, 0))
        self.time_end.setMinimumHeight(40)
        time_end_layout.addWidget(self.time_end)
        
        time_layout.addLayout(time_start_layout)
        time_layout.addLayout(time_end_layout)
        form_layout.addLayout(time_layout)
        
        # Reminder settings
        reminder_layout = QHBoxLayout()
        
        self.reminder_checkbox = QCheckBox("🔔 Enable Reminder")
        self.reminder_checkbox.setChecked(True)
        self.reminder_checkbox.setStyleSheet("""
            color: #4A4A4A; 
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        reminder_layout.addWidget(self.reminder_checkbox)
        
        reminder_layout.addWidget(QLabel("Minutes before:"))
        self.reminder_spin = QSpinBox()
        self.reminder_spin.setRange(1, 120)
        self.reminder_spin.setValue(15)
        self.reminder_spin.setSuffix(" min")
        self.reminder_spin.setMinimumHeight(35)
        self.reminder_spin.setStyleSheet("""
            QSpinBox {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 8px;
                border-radius: 8px;
            }
            QSpinBox:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        reminder_layout.addWidget(self.reminder_spin)
        reminder_layout.addStretch()
        
        form_layout.addLayout(reminder_layout)
        
        # Notes
        form_layout.addWidget(QLabel("📎 Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Additional details, room number, preparation needed...")
        self.notes_input.setMinimumHeight(80)
        self.notes_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_layout.addWidget(self.notes_input)
        
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        save_btn = QPushButton("✓ Save Event")
        save_btn.setMinimumHeight(48)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 14px 32px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
            QPushButton:pressed {
                background-color: #FF5280;
            }
        """)
        save_btn.clicked.connect(self.save_event)
        
        cancel_btn = QPushButton("✕ Cancel")
        cancel_btn.setMinimumHeight(48)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE4E8;
                color: #8B6B7A;
                border: 2px solid #FFD1DC;
                padding: 14px 32px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #FFD1DC;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def save_event(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing Title", "Please enter an event title.")
            self.title_input.setFocus()
            return

        category = self.category_combo.currentText()
        subtopic = self.subtopic_input.text().strip()
        time_start = self.time_start.time().toString("HH:mm")
        time_end = self.time_end.time().toString("HH:mm")

        # Validate that end time is after start time
        if self.time_end.time() <= self.time_start.time():
            QMessageBox.warning(self, "Invalid Time Range",
                                "End time must be after start time.\n\nPlease adjust the times and try again.")
            self.time_end.setFocus()
            return

        notes = self.notes_input.toPlainText().strip()
        reminder_minutes = self.reminder_spin.value()
        reminder_enabled = self.reminder_checkbox.isChecked()
        
        self.db.add_event(title, category, subtopic, self.date, time_start, time_end, 
                         notes, reminder_minutes, reminder_enabled)
        self.accept()


class ActiveRecallSidebar(QWidget):
    """Sidebar for quick notes and study debt tracking (Polished Pink Theme)"""
    
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.current_event_id = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("📝 Study Notes")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FF6B9D;")
        layout.addWidget(title)
        
        # High-Yield Facts section
        facts_group = QGroupBox("High-Yield Facts (3 Key Points)")
        facts_group.setStyleSheet("QGroupBox { font-size: 16px; color: #FF6B9D; font-weight: bold; }")
        facts_layout = QVBoxLayout()
        facts_layout.setSpacing(15)
        
        self.fact_inputs = []
        for i in range(3):
            fact_input = QLineEdit()
            fact_input.setPlaceholderText(f"Key fact #{i+1} about this event...")
            fact_input.setMinimumHeight(40)
            fact_input.setStyleSheet("""
                QLineEdit {
                    background-color: #FFF5F7;
                    color: #4A4A4A;
                    border: 2px solid #FFD1DC;
                    padding: 10px;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 2px solid #FF6B9D;
                }
            """)
            fact_input.returnPressed.connect(self.save_facts)
            fact_input.editingFinished.connect(self.save_facts)
            self.fact_inputs.append(fact_input)
            facts_layout.addWidget(fact_input)
        
        facts_group.setLayout(facts_layout)
        layout.addWidget(facts_group)
        
        # Study Debt section
        debt_group = QGroupBox("📚 Study Debt (Missed Topics)")
        debt_group.setStyleSheet("QGroupBox { font-size: 16px; color: #FF6B9D; font-weight: bold; }")
        debt_layout = QVBoxLayout()
        
        self.debt_list = QListWidget()
        self.debt_list.setMinimumHeight(150)
        self.debt_list.setStyleSheet("""
            QListWidget {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #FFE4E8;
                border-radius: 5px;
            }
            QListWidget::item:hover {
                background-color: #FFE4E8;
            }
        """)
        
        debt_layout.addWidget(self.debt_list)
        
        # Action Buttons Layout for Debt
        debt_buttons_layout = QHBoxLayout()
        debt_buttons_layout.setSpacing(10)
        
        # Add to study debt button
        self.add_debt_btn = QPushButton("➕ Add to Debt")
        self.add_debt_btn.setMinimumHeight(45)
        self.add_debt_btn.clicked.connect(self.add_study_debt)
        self.add_debt_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5252;
                color: white;
                border: none;
                padding: 12px;
                font-weight: bold;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF2A5F;
            }
        """)
        debt_buttons_layout.addWidget(self.add_debt_btn, 1)
        
        # Auto-Schedule button
        self.auto_schedule_btn = QPushButton("⚡ Auto-Schedule")
        self.auto_schedule_btn.setMinimumHeight(45)
        self.auto_schedule_btn.clicked.connect(self.auto_schedule_debt)
        self.auto_schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 12px;
                font-weight: bold;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
        """)
        debt_buttons_layout.addWidget(self.auto_schedule_btn, 1)
        
        debt_layout.addLayout(debt_buttons_layout)
        debt_group.setLayout(debt_layout)
        layout.addWidget(debt_group)
        
        # Help text
        help_label = QLabel("💡 Select an event from the calendar to add notes")
        help_label.setStyleSheet("color: #8B6B7A; font-size: 13px; padding: 10px;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        layout.addStretch()
        self.setLayout(layout)
        self.load_study_debt()
    
    def set_event(self, event_id: int):
        """Set the current event for note taking"""
        self.current_event_id = event_id
        self.load_facts()
    
    def save_facts(self):
        """Save high-yield facts for current event"""
        if self.current_event_id:
            # Clear existing facts for this event
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM study_notes WHERE event_id = ?", (self.current_event_id,))
                conn.commit()
            
            # Add new facts
            for fact_input in self.fact_inputs:
                fact = fact_input.text().strip()
                if fact:
                    self.db.add_study_note(self.current_event_id, fact)
    
    def load_facts(self):
        """Load high-yield facts for current event"""
        if self.current_event_id:
            facts = self.db.get_study_notes(self.current_event_id)
            for i, fact_input in enumerate(self.fact_inputs):
                if i < len(facts):
                    fact_input.setText(facts[i])
                else:
                    fact_input.clear()
    
    def add_study_debt(self):
        """Add current event to study debt"""
        if self.current_event_id:
            self.db.add_study_debt(self.current_event_id, "Missed or incomplete")
            self.load_study_debt()
    
    def load_study_debt(self):
        """Load all study debt entries"""
        self.debt_list.clear()
        debts = self.db.get_study_debt()
        
        for debt in debts:
            item_text = f"🚨 {debt['title']}\n   📅 {debt['date']}"
            item = QListWidgetItem(item_text)
            self.debt_list.addItem(item)
            
    def auto_schedule_debt(self):
        """Find free time blocks in the next 7 days and reschedule all study debts"""
        debts = self.db.get_study_debt()
        if not debts:
            QMessageBox.information(self, "No Study Debt", "You have no outstanding study debt! Excellent job staying on track! 🌟")
            return
            
        all_events = self.db.get_events()
        tomorrow = datetime.now().date() + timedelta(days=1)
        
        # High-yield open study blocks
        standard_blocks = [
            ("09:00", "11:00"),
            ("11:00", "13:00"),
            ("14:00", "16:00"),
            ("16:00", "18:00")
        ]
        
        free_slots = []
        for d in range(7):
            current_date = tomorrow + timedelta(days=d)
            date_str = current_date.strftime("%Y-%m-%d")
            
            for start_t, end_t in standard_blocks:
                overlap = False
                for event in all_events:
                    if event['date'] == date_str:
                        e_start = event['time_start']
                        e_end = event['time_end']
                        if start_t < e_end and e_start < end_t:
                            overlap = True
                            break
                if not overlap:
                    free_slots.append((date_str, start_t, end_t))
                    
        if len(free_slots) < len(debts):
            QMessageBox.warning(self, "Insufficient Free Slots", 
                                f"Only found {len(free_slots)} free slots in the next 7 days, but you have {len(debts)} study debts. "
                                "Please add more open slots or clear some tasks!")
            return
            
        # Build proposed rescheduled plan
        proposal = []
        for i, debt in enumerate(debts):
            slot = free_slots[i]
            proposal.append({
                'event_id': debt['event_id'],
                'title': debt['title'],
                'category': debt['category'],
                'date': slot[0],
                'start_time': slot[1],
                'end_time': slot[2]
            })
            
        proposal_text = "MedFlow has optimized your schedule and found free slots!\n\nProposed Reschedule Plan:\n"
        for p in proposal:
            proposal_text += f"• {p['title']} ({p['category']})\n  Rescheduled to: {p['date']} @ {p['start_time']} - {p['end_time']}\n\n"
            
        proposal_text += "Do you want to confirm and apply this auto-schedule plan?"
        
        reply = QMessageBox.question(self, "Confirm Auto-Schedule Plan", proposal_text,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                                     
        if reply == QMessageBox.Yes:
            # Apply all reschedules
            for p in proposal:
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE academic_events 
                        SET date = ?, time_start = ?, time_end = ? 
                        WHERE id = ?
                    """, (p['date'], p['start_time'], p['end_time'], p['event_id']))
                    conn.commit()
                self.db.resolve_study_debt(p['event_id'])
                
            QMessageBox.information(self, "Success", "All missed sessions have been rescheduled! Your study debt is cleared. 🎉")
            self.load_study_debt()
            
            # Refresh calendar
            main_window = self.window()
            if hasattr(main_window, 'planner_tab'):
                main_window.planner_tab.load_events()


class NotesSection(QWidget):
    """Notes workspace with clinical study journal."""

    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self._editing_note_id: Optional[int] = None  # None = creating new note
        self.init_ui()
        self.load_notes()

    def init_ui(self):
        # Main layout is QHBoxLayout directly in NotesSection
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)

        create_group = QGroupBox("✍️ Create / Edit Note")
        create_group.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                color: #FF8FA3;
                font-weight: 600;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding-top: 18px;
            }
        """)
        create_layout = QVBoxLayout()
        create_layout.setSpacing(15)

        self.note_title = QLineEdit()
        self.note_title.setPlaceholderText("Note title...")
        self.note_title.setMinimumHeight(45)
        self.note_title.setStyleSheet("""
            QLineEdit {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 12px;
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        create_layout.addWidget(self.note_title)

        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_label.setStyleSheet("color: #666666; font-weight: 500;")
        self.note_category = QComboBox()
        self.note_category.addItems(["General", "Lecture Notes", "Clinical", "Anatomy", "Physiology", "Biochemistry", "Pathology", "Pharmacology"])
        self.note_category.setMinimumHeight(40)
        self.note_category.setStyleSheet("""
            QComboBox {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 8px;
                border-radius: 10px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.note_category)
        category_layout.addStretch()
        create_layout.addLayout(category_layout)

        self.note_content = QTextEdit()
        self.note_content.setPlaceholderText("Write your notes here...")
        self.note_content.setMinimumHeight(180)
        self.note_content.setStyleSheet("""
            QTextEdit {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 15px;
                border-radius: 10px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        self.note_content.textChanged.connect(self.update_word_count)
        create_layout.addWidget(self.note_content)

        self.word_count_label = QLabel("0 words | 0 characters")
        self.word_count_label.setStyleSheet("color: #8B6B7A; font-size: 12px; font-style: italic;")
        self.word_count_label.setAlignment(Qt.AlignRight)
        create_layout.addWidget(self.word_count_label)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        self.save_note_btn = QPushButton("✍️ Save Note")
        self.save_note_btn.setMinimumHeight(50)
        self.save_note_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
        """)
        self.save_note_btn.setToolTip("Save the current note (Ctrl+S)")
        self.save_note_btn.setShortcut("Ctrl+S")
        self.save_note_btn.clicked.connect(self.add_note)
        buttons_layout.addWidget(self.save_note_btn)

        new_note_btn = QPushButton("➕ New Note")
        new_note_btn.setMinimumHeight(50)
        new_note_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE4E8;
                color: #8B6B7A;
                border: 2px solid #FFD1DC;
                padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #FFD1DC;
            }
        """)
        new_note_btn.setToolTip("Clear the editor and start a brand new note")
        new_note_btn.clicked.connect(self.clear_editor)
        buttons_layout.addWidget(new_note_btn)

        export_btn = QPushButton("📤 Export")
        export_btn.setMinimumHeight(50)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE4E8;
                color: #8B6B7A;
                border: 2px solid #FFD1DC;
                padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #FFD1DC;
            }
        """)
        export_btn.setToolTip("Export all notes to a text file")
        export_btn.clicked.connect(self.export_notes)
        buttons_layout.addWidget(export_btn)

        create_layout.addLayout(buttons_layout)
        create_group.setLayout(create_layout)
        layout.addWidget(create_group, 2)

        notes_group = QGroupBox("My Notes")
        notes_group.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                color: #FF8FA3;
                font-weight: 600;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding-top: 18px;
            }
        """)
        notes_layout = QVBoxLayout()
        notes_layout.setSpacing(15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search notes...")
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.filter_notes)
        notes_layout.addWidget(self.search_input)

        self.notes_list = QListWidget()
        self.notes_list.setMinimumHeight(420)
        self.notes_list.setStyleSheet("""
            QListWidget {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
            }
            QListWidget::item {
                background-color: white;
                padding: 14px;
                margin: 8px 0px;
                border-radius: 10px;
                border: 1px solid #FFE4E1;
            }
            QListWidget::item:selected {
                background-color: #FFD1DC;
                color: #FF6B9D;
                border: 2px solid #FF6B9D;
            }
        """)
        self.notes_list.itemClicked.connect(self.load_note)
        self.notes_list.itemDoubleClicked.connect(self.open_note_reader)
        notes_layout.addWidget(self.notes_list)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)

        read_btn = QPushButton("📖 Read Note")
        read_btn.setMinimumHeight(45)
        read_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
        """)
        read_btn.clicked.connect(self.open_note_reader)
        action_layout.addWidget(read_btn)

        delete_btn = QPushButton("🗑 Delete")
        delete_btn.setMinimumHeight(45)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB6C1;
                color: white;
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
        """)
        delete_btn.clicked.connect(self.delete_note)
        action_layout.addWidget(delete_btn)

        action_layout.addStretch()
        notes_layout.addLayout(action_layout)

        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group, 1)

    def add_note(self):
        title = self.note_title.text().strip()
        content = self.note_content.toPlainText().strip()
        category = self.note_category.currentText()

        if not title or not content:
            QMessageBox.warning(self, "Missing Note", "Please enter both a title and note content.")
            return

        if self._editing_note_id is not None:
            # Update existing note in DB
            self.db.update_app_note(self._editing_note_id, title, content, category)
        else:
            # Create new note in DB
            self.db.add_app_note(title, content, category)

        self.clear_editor()
        self.load_notes()

    def clear_editor(self):
        """Reset the editor to create a new note"""
        self._editing_note_id = None
        self.note_title.clear()
        self.note_content.clear()
        self.note_category.setCurrentIndex(0)
        self.save_note_btn.setText("✍️ Save Note")
        self.notes_list.clearSelection()

    def refresh_notes_list(self):
        notes = self.db.get_app_notes()
        self.notes_list.clear()
        for note in notes:
            ts = note.get('updated_at') or note.get('created_at', '')
            item_text = f"📄 {note['title']}\n   🏷️ {note['category']} · {ts[:16]}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, note['id'])
            self.notes_list.addItem(item)

        count = len(notes)
        # Update group box title dynamically if it exists
        parent = self.notes_list.parent()
        if isinstance(parent, QWidget):
            gb = parent.parent()
            if hasattr(gb, 'setTitle'):
                gb.setTitle(f"My Notes  ({count})")

    def load_notes(self):
        self.refresh_notes_list()

    def load_note(self, item: QListWidgetItem):
        note_id = item.data(Qt.UserRole)
        note = self.db.get_app_note_by_id(note_id)
        if note:
            self._editing_note_id = note_id
            self.note_title.setText(note['title'])
            self.note_category.setCurrentText(note['category'])
            self.note_content.setText(note['content'])
            self.save_note_btn.setText("💾 Update Note")

    def delete_note(self):
        current_item = self.notes_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a note to delete.")
            return

        note_id = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Delete Note",
            "Are you sure you want to permanently delete this note?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_app_note(note_id)
            if self._editing_note_id == note_id:
                self.clear_editor()
            self.load_notes()

    def filter_notes(self, text: str):
        notes = self.db.get_app_notes(search=text if text else None)
        self.notes_list.clear()
        for note in notes:
            ts = note.get('updated_at') or note.get('created_at', '')
            item_text = f"📄 {note['title']}\n   🏷️ {note['category']} · {ts[:16]}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, note['id'])
            self.notes_list.addItem(item)

    def update_word_count(self):
        text = self.note_content.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.setText(f"{words} words | {chars} characters")

    def export_notes(self):
        from PySide6.QtWidgets import QFileDialog

        notes = self.db.get_app_notes()
        if not notes:
            QMessageBox.information(self, "No Notes", "No notes to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Notes",
            f"medflow_notes_{datetime.now().strftime('%Y%m%d')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("MEDFLOW STUDY NOTES EXPORT\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write("=" * 60 + "\n\n")
                for i, note in enumerate(notes, 1):
                    f.write(f"{'-' * 60}\n")
                    f.write(f"NOTE #{i}\n")
                    f.write(f"{'-' * 60}\n")
                    f.write(f"Title: {note['title']}\n")
                    f.write(f"Category: {note['category']}\n")
                    f.write(f"Date: {note.get('updated_at', '')[:16]}\n\n")
                    f.write(f"Content:\n{note['content']}\n\n")
                f.write("=" * 60 + "\n")
                f.write(f"Total Notes: {len(notes)}\n")
            QMessageBox.information(self, "Export Successful", f"Notes exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")



    def open_note_reader(self):
        current_item = self.notes_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a note to read.")
            return

        note_id = current_item.data(Qt.UserRole)
        note = self.db.get_app_note_by_id(note_id)
        if note:
            # Remap key names so NoteReaderDialog gets what it expects
            note.setdefault('date', note.get('updated_at', '')[:16])
            dialog = NoteReaderDialog(note, self)
            dialog.exec()


class ResultsLedger(QWidget):
    """Performance tracker for CAT and End-of-Unit exam scores"""
    
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.init_ui()
        self.load_exam_scores()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📊 Results Ledger - Performance Tracker")
        title.setStyleSheet("""
            font-size: 28px; 
            font-weight: 600; 
            color: #FF6B9D;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            padding-bottom: 15px;
        """)
        layout.addWidget(title)
        
        # Add Exam Score Section
        add_group = QGroupBox("➕ Add Exam Score")
        add_group.setStyleSheet("""
            QGroupBox { 
                font-size: 16px; 
                color: #FF6B9D; 
                font-weight: 600;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding-top: 15px;
            }
        """)
        add_layout = QGridLayout()
        add_layout.setSpacing(12)
        
        # Subject Name
        subject_label = QLabel("Subject Name:")
        subject_label.setStyleSheet("color: #4A4A4A; font-weight: 500;")
        add_layout.addWidget(subject_label, 0, 0)
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("e.g., Anatomy, Physiology")
        self.subject_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFF5F7;
                border: 2px solid #FFD1DC;
                padding: 10px;
                border-radius: 8px;
            }
            QLineEdit:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        add_layout.addWidget(self.subject_input, 0, 1)
        
        # Exam Type
        exam_label = QLabel("Exam Type:")
        exam_label.setStyleSheet("color: #4A4A4A; font-weight: 500;")
        add_layout.addWidget(exam_label, 1, 0)
        self.exam_type_combo = QComboBox()
        self.exam_type_combo.addItems(["CAT (Continuous Assessment Test)", "End-of-Unit Exam"])
        self.exam_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFF5F7;
                border: 2px solid #FFD1DC;
                padding: 8px;
                border-radius: 8px;
            }
            QComboBox:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        add_layout.addWidget(self.exam_type_combo, 1, 1)
        
        # Score
        score_label = QLabel("Score (%):")
        score_label.setStyleSheet("color: #4A4A4A; font-weight: 500;")
        add_layout.addWidget(score_label, 2, 0)
        self.score_input = QDoubleSpinBox()
        self.score_input.setRange(0, 100)
        self.score_input.setValue(50)
        self.score_input.setDecimals(1)
        self.score_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #FFF5F7;
                border: 2px solid #FFD1DC;
                padding: 8px;
                border-radius: 8px;
            }
        """)
        add_layout.addWidget(self.score_input, 2, 1)
        
        # Date
        date_label = QLabel("Date:")
        date_label.setStyleSheet("color: #4A4A4A; font-weight: 500;")
        add_layout.addWidget(date_label, 3, 0)
        self.exam_date = QDateEdit()
        self.exam_date.setCalendarPopup(True)
        self.exam_date.setDate(QDateTime.currentDateTime().date())
        self.exam_date.setStyleSheet("""
            QDateEdit {
                background-color: #FFF5F7;
                border: 2px solid #FFD1DC;
                padding: 8px;
                border-radius: 8px;
            }
        """)
        add_layout.addWidget(self.exam_date, 3, 1)
        
        # Study Hours (for correlation)
        hours_label = QLabel("Study Hours (week before):")
        hours_label.setStyleSheet("color: #4A4A4A; font-weight: 500;")
        add_layout.addWidget(hours_label, 4, 0)
        self.study_hours_input = QDoubleSpinBox()
        self.study_hours_input.setRange(0, 168)
        self.study_hours_input.setValue(20)
        self.study_hours_input.setDecimals(1)
        self.study_hours_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #FFF5F7;
                border: 2px solid #FFD1DC;
                padding: 8px;
                border-radius: 8px;
            }
        """)
        add_layout.addWidget(self.study_hours_input, 4, 1)
        
        # Add Button
        self.add_score_btn = QPushButton("✓ Add Score")
        self.add_score_btn.setMinimumHeight(45)
        self.add_score_btn.clicked.connect(self.add_exam_score)
        self.add_score_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 12px 24px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
            QPushButton:pressed {
                background-color: #FF5280;
            }
        """)
        add_layout.addWidget(self.add_score_btn, 5, 0, 1, 2)
        
        add_group.setLayout(add_layout)
        add_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.addWidget(add_group)

        # Exam Scores Table
        scores_group = QGroupBox("📋 Exam Scores")
        scores_group.setStyleSheet("""
            QGroupBox { 
                font-size: 16px; 
                color: #FF6B9D; 
                font-weight: 600;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding-top: 15px;
            }
        """)
        scores_layout = QVBoxLayout()
        
        self.scores_table = QTableWidget()
        self.scores_table.setColumnCount(6)
        self.scores_table.setHorizontalHeaderLabels(["Subject", "Exam Type", "Score (%)", "Date", "Status", ""])
        self.scores_table.setColumnWidth(5, 80)  # Fixed width for action column
        self.scores_table.cellDoubleClicked.connect(self.open_exam_detail_from_row)
        self.scores_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scores_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.scores_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.scores_table.setSelectionMode(QTableWidget.SingleSelection)
        self.scores_table.setSortingEnabled(True)
        self.scores_table.setMinimumHeight(260)
        self.scores_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scores_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                border-radius: 10px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #FFE4E8;
            }
            QHeaderView::section {
                background-color: #FFF5F7;
                color: #FF6B9D;
                padding: 12px;
                font-weight: 600;
                border: none;
                border-bottom: 2px solid #FFD1DC;
            }
        """)
        scores_layout.addWidget(self.scores_table)
        
        # Action buttons for selected entry
        action_layout = QHBoxLayout()
        
        self.delete_selected_btn = QPushButton("🗑 Delete Selected")
        self.delete_selected_btn.setMinimumHeight(40)
        self.delete_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB6C1;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: 600;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
        """)
        self.delete_selected_btn.clicked.connect(self.delete_selected_exam)
        
        clear_all_btn = QPushButton("⚠️ Clear All Data")
        clear_all_btn.setMinimumHeight(40)
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE4E8;
                color: #8B6B7A;
                border: 2px solid #FFB6C1;
                padding: 10px 20px;
                font-weight: 600;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #FFD1DC;
                border-color: #FF69B4;
            }
        """)
        clear_all_btn.clicked.connect(self.clear_all_exams)
        
        action_layout.addWidget(self.delete_selected_btn)
        action_layout.addWidget(clear_all_btn)
        action_layout.addStretch()
        scores_layout.addLayout(action_layout)
        
        scores_group.setLayout(scores_layout)
        scores_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Scientist Feature - Study Hours vs Exam Score Graph
        graph_group = QGroupBox("📈 Study Hours vs Exam Score Correlation")
        graph_group.setStyleSheet("""
            QGroupBox { 
                font-size: 16px; 
                color: #FF6B9D; 
                font-weight: 600;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding-top: 15px;
            }
        """)
        graph_layout = QVBoxLayout()
        
        # ── Tab widget: Correlation scatter + Per-subject bar ─────────────
        self._chart_tabs = QTabWidget()
        self._chart_tabs.setStyleSheet("""
            QTabBar::tab {
                background: #FFE4E8; color: #8B6B7A;
                padding: 6px 16px; border-radius: 8px 8px 0 0;
                font-size: 13px;
            }
            QTabBar::tab:selected { background: #FF6B9D; color: white; }
        """)

        # ── Chart 1: Correlation scatter ──────────────────────────────────
        self.chart = QChart()
        self.chart.setTitle("Study Hours  ×  Exam Score")
        font = QFont(); font.setBold(True); font.setPointSize(11)
        self.chart.setTitleFont(font)
        self.chart.setTitleBrush(QBrush(QColor("#FF6B9D")))
        self.chart.setBackgroundBrush(QBrush(QColor("#FFF8FA")))
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

        self.study_hours_series = QScatterSeries()
        self.study_hours_series.setName("Study Hours")
        self.study_hours_series.setMarkerSize(14)
        self.study_hours_series.setColor(QColor("#FF6B9D"))
        self.study_hours_series.setBorderColor(QColor("white"))

        self.exam_score_series = QScatterSeries()
        self.exam_score_series.setName("Exam Score (%)")
        self.exam_score_series.setMarkerSize(12)
        self.exam_score_series.setColor(QColor("#B39DDB"))
        self.exam_score_series.setBorderColor(QColor("white"))

        # Trend line for scores
        self._trend_series = QLineSeries()
        self._trend_series.setName("Score trend")
        trend_pen = QPen(QColor("#FF6B9D")); trend_pen.setWidth(2)
        trend_pen.setStyle(Qt.DashLine)
        self._trend_series.setPen(trend_pen)

        self.chart.addSeries(self.study_hours_series)
        self.chart.addSeries(self.exam_score_series)
        self.chart.addSeries(self._trend_series)

        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Exam #")
        self.axis_x.setTitleBrush(QBrush(QColor("#4A4A4A")))
        self.axis_x.setLabelsBrush(QBrush(QColor("#4A4A4A")))
        self.axis_x.setGridLineColor(QColor("#FFE4E8"))
        self.axis_x.setMinorGridLineColor(QColor("#FFF5F7"))

        self.axis_y_hours = QValueAxis()
        self.axis_y_hours.setTitleText("Study Hours")
        self.axis_y_hours.setTitleBrush(QBrush(QColor("#FF6B9D")))
        self.axis_y_hours.setLabelsBrush(QBrush(QColor("#FF6B9D")))
        self.axis_y_hours.setGridLineColor(QColor("#FFE4E8"))
        self.axis_y_hours.setMinorGridLineVisible(True)
        self.axis_y_hours.setMinorGridLineColor(QColor("#FFF5F7"))

        self.axis_y_score = QValueAxis()
        self.axis_y_score.setTitleText("Score (%)")
        self.axis_y_score.setRange(0, 100)
        self.axis_y_score.setTitleBrush(QBrush(QColor("#7E57C2")))
        self.axis_y_score.setLabelsBrush(QBrush(QColor("#7E57C2")))

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y_hours, Qt.AlignLeft)
        self.chart.addAxis(self.axis_y_score, Qt.AlignRight)

        self.study_hours_series.attachAxis(self.axis_x)
        self.study_hours_series.attachAxis(self.axis_y_hours)
        self.exam_score_series.attachAxis(self.axis_x)
        self.exam_score_series.attachAxis(self.axis_y_score)
        self._trend_series.attachAxis(self.axis_x)
        self._trend_series.attachAxis(self.axis_y_score)

        # ── Chart 2: Per-subject average bar chart ────────────────────────
        self._bar_chart = QChart()
        self._bar_chart.setTitle("Average Score by Subject")
        self._bar_chart.setTitleFont(font)
        self._bar_chart.setTitleBrush(QBrush(QColor("#FF6B9D")))
        self._bar_chart.setBackgroundBrush(QBrush(QColor("#FFF8FA")))
        self._bar_chart.setAnimationOptions(QChart.SeriesAnimations)
        self._bar_chart.legend().setVisible(False)

        self._bar_set  = QBarSet("Avg Score")
        self._bar_set.setColor(QColor("#FF6B9D"))
        self._bar_set.setBorderColor(QColor("#FF6B9D"))
        self._bar_series = QBarSeries()
        self._bar_series.append(self._bar_set)
        self._bar_chart.addSeries(self._bar_series)

        self._bar_axis_x = QBarCategoryAxis()
        self._bar_axis_y = QValueAxis()
        self._bar_axis_y.setRange(0, 100)
        self._bar_axis_y.setTitleText("Avg Score (%)")
        self._bar_axis_y.setTitleBrush(QBrush(QColor("#FF6B9D")))
        self._bar_axis_y.setLabelsBrush(QBrush(QColor("#4A4A4A")))
        self._bar_axis_y.setGridLineColor(QColor("#FFE4E8"))
        self._bar_chart.addAxis(self._bar_axis_x, Qt.AlignBottom)
        self._bar_chart.addAxis(self._bar_axis_y, Qt.AlignLeft)
        self._bar_series.attachAxis(self._bar_axis_x)
        self._bar_series.attachAxis(self._bar_axis_y)
        
        # ── Chart views ───────────────────────────────────────────────────
        _cv_style = "QChartView { background-color: #FFF8FA; border-radius: 10px; }"

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(320)
        self.chart_view.setStyleSheet(_cv_style)

        self._bar_chart_view = QChartView(self._bar_chart)
        self._bar_chart_view.setRenderHint(QPainter.Antialiasing)
        self._bar_chart_view.setMinimumHeight(320)
        self._bar_chart_view.setStyleSheet(_cv_style)

        # No data label (shared across both tabs)
        self.no_data_label = QLabel("📊 Add exam scores to see graphs")
        self.no_data_label.setAlignment(Qt.AlignCenter)
        self.no_data_label.setStyleSheet("""
            font-size: 16px; color: #8B6B7A; padding: 50px;
        """)

        # ── Stacked widget: tabs or "no data" ─────────────────────────────
        self._chart_tabs.addTab(self.chart_view, "📈 Correlation")
        self._chart_tabs.addTab(self._bar_chart_view, "📊 By Subject")

        self.graph_stack = QStackedWidget()
        self.graph_stack.addWidget(self._chart_tabs)
        self.graph_stack.addWidget(self.no_data_label)

        graph_layout.addWidget(self.graph_stack)
        graph_group.setLayout(graph_layout)
        graph_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        center_splitter = QSplitter(Qt.Vertical)
        center_splitter.setChildrenCollapsible(False)
        center_splitter.addWidget(scores_group)
        center_splitter.addWidget(graph_group)
        center_splitter.setStretchFactor(0, 1)  # Table gets more space
        center_splitter.setStretchFactor(1, 1)  # Graph gets equal space

        main_splitter.addWidget(center_splitter)
        main_splitter.setStretchFactor(0, 0)  # Add form stays small
        main_splitter.setStretchFactor(1, 1)  # Table/graph area expands
        layout.addWidget(main_splitter, 1)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Data")
        refresh_btn.setMinimumHeight(45)
        refresh_btn.clicked.connect(self.load_exam_scores)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE4E8;
                color: #8B6B7A;
                border: 2px solid #FFD1DC;
                padding: 12px 24px;
                border-radius: 10px;
                font-weight: 600;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #FFD1DC;
            }
        """)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
    
    def add_exam_score(self):
        """Add a new exam score"""
        subject = self.subject_input.text().strip()
        exam_type = self.exam_type_combo.currentText()
        score = self.score_input.value()
        date = self.exam_date.date().toString("yyyy-MM-dd")
        study_hours = self.study_hours_input.value()
        
        if subject:
            # Add exam score
            self.db.add_exam_score(subject, exam_type, score, date)
            
            # Add study hours (backdated to the exam date)
            study_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
            self.db.add_study_hours(study_date, study_hours, subject, "Study hours before exam")
            
            # Clear inputs
            self.subject_input.clear()
            self.score_input.setValue(50)
            self.study_hours_input.setValue(20)
            
            # Reload data
            self.load_exam_scores()
    
    def load_exam_scores(self):
        """Load exam scores and update visualization"""
        scores = self.db.get_exam_scores()
        self.current_scores = scores  # Store for reference
        
        # Update table
        self.scores_table.setRowCount(len(scores))
        for i, score in enumerate(scores):
            self.scores_table.setItem(i, 0, QTableWidgetItem(score['subject_name']))
            self.scores_table.setItem(i, 1, QTableWidgetItem(score['exam_type']))
            self.scores_table.setItem(i, 2, QTableWidgetItem(f"{score['score']:.1f}"))
            self.scores_table.setItem(i, 3, QTableWidgetItem(score['date']))
            
            # Status based on 50% pass mark
            status = "PASS ✓" if score['score'] >= 50 else "FAIL ✗"
            status_item = QTableWidgetItem(status)
            if score['score'] >= 50:
                status_item.setBackground(QBrush(QColor("#90EE90")))  # Light green
                status_item.setForeground(QBrush(QColor("#228B22")))  # Forest green
            else:
                status_item.setBackground(QBrush(QColor("#FFB6C1")))  # Light pink
                status_item.setForeground(QBrush(QColor("#DC143C")))  # Crimson
            self.scores_table.setItem(i, 4, status_item)
            
            # Action buttons container
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)
            
            # View details button
            view_btn = QPushButton("👁")
            view_btn.setMaximumWidth(32)
            view_btn.setMinimumHeight(28)
            view_btn.setToolTip("View Details")
            view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFF5F7;
                    color: #FF6B9D;
                    border: 1px solid #FFD1DC;
                    border-radius: 5px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #FF6B9D;
                    color: white;
                }
            """)
            view_btn.clicked.connect(lambda checked, idx=i: self.view_exam_details(idx))
            action_layout.addWidget(view_btn)
            
            # Delete button for this row
            delete_btn = QPushButton("🗑")
            delete_btn.setMaximumWidth(32)
            delete_btn.setMinimumHeight(28)
            delete_btn.setToolTip("Delete")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFE4E8;
                    color: #FF6B9D;
                    border: 1px solid #FFD1DC;
                    border-radius: 5px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #FF69B4;
                    color: white;
                }
            """)
            delete_btn.clicked.connect(lambda checked, idx=i: self.delete_exam_at_row(idx))
            action_layout.addWidget(delete_btn)
            
            action_layout.addStretch()
            action_widget.setLayout(action_layout)
            self.scores_table.setCellWidget(i, 5, action_widget)
        
        # Update correlation graph
        self.update_correlation_graph()
    
    def delete_exam_at_row(self, row: int):
        """Delete exam at specific row"""
        if 0 <= row < len(self.current_scores):
            score = self.current_scores[row]
            exam_id = score.get('id')
            if exam_id:
                reply = QMessageBox.question(
                    self, 
                    "Confirm Delete",
                    f"Delete exam '{score['subject_name']}' from {score['date']}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    if self.db.delete_exam_score(exam_id):
                        QMessageBox.information(self, "Success", "Exam score deleted successfully!")
                        self.load_exam_scores()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to delete exam score.")
    
    def delete_selected_exam(self):
        """Delete currently selected exam from table"""
        selected_row = self.scores_table.currentRow()
        if selected_row >= 0:
            self.delete_exam_at_row(selected_row)
        else:
            QMessageBox.information(self, "No Selection", "Please select an exam score to delete.")
    
    def clear_all_exams(self):
        """Clear all exam scores with confirmation"""
        reply = QMessageBox.warning(
            self,
            "⚠️ Clear All Data",
            "Are you sure you want to delete ALL exam scores?\n\nThis action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Double confirmation
            reply2 = QMessageBox.critical(
                self,
                "Final Confirmation",
                "This will permanently delete all your exam data.\n\nAre you absolutely sure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply2 == QMessageBox.Yes:
                if self.db.clear_all_exam_scores():
                    QMessageBox.information(self, "Success", "All exam scores have been cleared.")
                    self.load_exam_scores()
                else:
                    QMessageBox.critical(self, "Error", "Failed to clear exam scores.")
    
    def update_correlation_graph(self):
        """Update the Study Hours vs Exam Score correlation graph"""
        correlation_data = self.db.get_study_hours_for_exam_correlation(days_before=7)
        
        # Clear existing data
        self.study_hours_series.clear()
        self.exam_score_series.clear()
        
        # Filter valid data
        valid_data = [
            d for d in correlation_data 
            if d.get('study_hours_before_exam') is not None and d.get('score') is not None
        ]
        
        if not valid_data:
            # Show "no data" message
            self.graph_stack.setCurrentIndex(1)
            return
        
        # Show chart
        self.graph_stack.setCurrentIndex(0)
        
        # Add data points
        for i, data in enumerate(valid_data):
            hours = float(data['study_hours_before_exam'])
            score = float(data['score'])
            self.study_hours_series.append(i + 1, hours)  # Start from 1, not 0
            self.exam_score_series.append(i + 1, score)
        
        # Update axes ranges
        max_hours = max([d['study_hours_before_exam'] for d in valid_data])
        max_score = max([d['score'] for d in valid_data])
        min_score = min([d['score'] for d in valid_data])

        self.axis_y_hours.setRange(0, max(max_hours * 1.2, 10))
        self.axis_y_score.setRange(max(0, min_score - 10), min(100, max_score + 10))
        num_exams = len(valid_data)
        self.axis_x.setRange(0, num_exams + 1)
        self.axis_x.setTickCount(min(num_exams + 2, 10))

        # ── Score trend line (linear regression) ─────────────────────────
        self._trend_series.clear()
        if len(valid_data) >= 2:
            scores_vals = [float(d['score']) for d in valid_data]
            n = len(scores_vals)
            xs = list(range(1, n + 1))
            mean_x = sum(xs) / n
            mean_y = sum(scores_vals) / n
            numer = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, scores_vals))
            denom = sum((x - mean_x) ** 2 for x in xs) or 1
            slope = numer / denom
            intercept = mean_y - slope * mean_x
            self._trend_series.append(1, intercept + slope * 1)
            self._trend_series.append(n, intercept + slope * n)

        # ── Per-subject bar chart ─────────────────────────────────────────
        all_scores = self.db.get_exam_scores()
        from collections import defaultdict
        subj_scores: dict = defaultdict(list)
        for s in all_scores:
            if s.get('score') is not None:
                subj_scores[s['subject_name']].append(float(s['score']))

        if self._bar_set.count() > 0:
            self._bar_set.remove(0, self._bar_set.count())
        subjects = sorted(subj_scores.keys())
        self._bar_axis_x.clear()
        if subjects:
            self._bar_axis_x.append(subjects)
            for subj in subjects:
                avg = sum(subj_scores[subj]) / len(subj_scores[subj])
                self._bar_set.append(avg)
            self._bar_axis_y.setRange(0, 100)
    
    def view_exam_details(self, row: int):
        """Open detail dialog for exam at row"""
        if 0 <= row < len(self.current_scores):
            score = self.current_scores[row]
            dialog = ExamDetailDialog(score, self)
            dialog.exec()
    
    def open_exam_detail_from_row(self, row: int, column: int):
        """Open exam detail when double-clicking a row"""
        if 0 <= row < len(self.current_scores):
            score = self.current_scores[row]
            dialog = ExamDetailDialog(score, self)
            dialog.exec()


class ExamDetailDialog(QDialog):
    """Full-screen dialog for viewing exam details"""
    
    def __init__(self, exam_data: dict, parent=None):
        super().__init__(parent)
        self.exam = exam_data
        self.notes: List[Dict] = []  # in-memory notes for this session
        self.setWindowTitle(f"📊 {exam_data['subject_name']} - Exam Details")
        self.setMinimumSize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Header with score badge
        header = QHBoxLayout()
        
        # Subject icon
        subject_emoji = "📚"
        if "anatomy" in self.exam['subject_name'].lower():
            subject_emoji = "🫀"
        elif "physio" in self.exam['subject_name'].lower():
            subject_emoji = "⚡"
        elif "bio" in self.exam['subject_name'].lower():
            subject_emoji = "🧬"
        elif "path" in self.exam['subject_name'].lower():
            subject_emoji = "🔬"
        elif "pharm" in self.exam['subject_name'].lower():
            subject_emoji = "💊"
        
        icon_label = QLabel(subject_emoji)
        icon_label.setStyleSheet("font-size: 60px;")
        header.addWidget(icon_label)
        
        # Title section
        title_layout = QVBoxLayout()
        
        subject_label = QLabel(self.exam['subject_name'])
        subject_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #FF6B9D;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        title_layout.addWidget(subject_label)
        
        type_label = QLabel(self.exam['exam_type'])
        type_label.setStyleSheet("""
            font-size: 16px;
            color: #8B6B7A;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        title_layout.addWidget(type_label)
        
        header.addLayout(title_layout, stretch=1)
        
        # Score badge
        score = self.exam['score']
        passed = score >= 50
        
        score_widget = QWidget()
        score_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {'#90EE90' if passed else '#FFB6C1'};
                border-radius: 15px;
                padding: 15px;
            }}
        """)
        score_layout = QVBoxLayout()
        score_layout.setContentsMargins(20, 15, 20, 15)
        
        score_num = QLabel(f"{score:.1f}%")
        score_num.setStyleSheet(f"""
            font-size: 36px;
            font-weight: 700;
            color: {'#228B22' if passed else '#DC143C'};
        """)
        score_num.setAlignment(Qt.AlignCenter)
        
        score_text = QLabel("PASS ✓" if passed else "FAIL ✗")
        score_text.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {'#228B22' if passed else '#DC143C'};
        """)
        score_text.setAlignment(Qt.AlignCenter)
        
        score_layout.addWidget(score_num)
        score_layout.addWidget(score_text)
        score_widget.setLayout(score_layout)
        header.addWidget(score_widget)
        
        layout.addLayout(header)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #FFD1DC;")
        line.setMaximumHeight(2)
        layout.addWidget(line)
        
        # Details grid
        details_group = QGroupBox("📋 Exam Details")
        details_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-size: 16px; 
                color: #FF8FA3; 
                font-weight: 600;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """)
        
        # Populate detail fields
        detail_grid = QGridLayout()
        detail_grid.setSpacing(12)
        detail_grid.setContentsMargins(20, 25, 20, 20)
        
        fields = [
            ("📚 Subject:", self.exam['subject_name']),
            ("📋 Exam Type:", self.exam['exam_type']),
            ("📊 Score:", f"{self.exam['score']:.1f}%"),
            ("📅 Date:", self.exam['date']),
        ]
        for i, (label_text, value_text) in enumerate(fields):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 14px; color: #8B6B7A; font-weight: 600;")
            val = QLabel(str(value_text))
            val.setStyleSheet("font-size: 14px; color: #4A4A4A;")
            detail_grid.addWidget(lbl, i, 0)
            detail_grid.addWidget(val, i, 1)
        
        details_group.setLayout(detail_grid)
        layout.addWidget(details_group)
        
        # Close button
        close_btn = QPushButton("✓ Close")
        close_btn.setMinimumHeight(48)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 14px 32px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        self.setLayout(layout)
        return  # Skip the broken code below
        
        # ---- DEAD CODE (kept to avoid large deletions) ----
        input_layout = QVBoxLayout()
        input_layout.setSpacing(15)
        
        # Title input
        self.note_title = QLineEdit()
        self.note_title.setPlaceholderText("Note title...")
        self.note_title.setMinimumHeight(45)
        self.note_title.setStyleSheet("""
            QLineEdit {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 12px;
                border-radius: 10px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        input_layout.addWidget(self.note_title)
        
        # Category selector
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_label.setStyleSheet("color: #666666; font-weight: 500;")
        self.note_category = QComboBox()
        self.note_category.addItems(["General", "Lecture Notes", "Clinical", "Anatomy", "Physiology", "Biochemistry", "Pathology", "Pharmacology"])
        self.note_category.setMinimumHeight(40)
        self.note_category.setStyleSheet("""
            QComboBox {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 8px;
                border-radius: 10px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.note_category)
        category_layout.addStretch()
        input_layout.addLayout(category_layout)
        
        # Note content
        self.note_content = QTextEdit()
        self.note_content.setPlaceholderText("Write your notes here...")
        self.note_content.setMinimumHeight(150)
        self.note_content.setStyleSheet("""
            QTextEdit {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 15px;
                border-radius: 10px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        self.note_content.textChanged.connect(self.update_word_count)
        input_layout.addWidget(self.note_content)
        
        # Word count label
        self.word_count_label = QLabel("0 words | 0 characters")
        self.word_count_label.setStyleSheet("""
            color: #8B6B7A;
            font-size: 12px;
            font-style: italic;
            padding: 5px;
        """)
        self.word_count_label.setAlignment(Qt.AlignRight)
        input_layout.addWidget(self.word_count_label)
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        
        # Add note button
        add_btn = QPushButton("✨ Add / Update Note")
        add_btn.setMinimumHeight(50)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 15px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
            QPushButton:pressed {
                background-color: #FF5280;
            }
        """)
        add_btn.clicked.connect(self.add_note)
        buttons_layout.addWidget(add_btn)
        
        # Export button
        export_btn = QPushButton("📤 Export Notes")
        export_btn.setMinimumHeight(50)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE4E8;
                color: #8B6B7A;
                border: 2px solid #FFD1DC;
                padding: 15px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #FFD1DC;
            }
        """)
        export_btn.clicked.connect(self.export_notes)
        buttons_layout.addWidget(export_btn)
        
        input_layout.addLayout(buttons_layout)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Notes list
        notes_group = QGroupBox("My Notes")
        notes_group.setStyleSheet("""
            QGroupBox { 
                font-size: 18px; 
                color: #FF8FA3; 
                font-weight: 600;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding-top: 15px;
            }
        """)
        notes_layout = QVBoxLayout()
        
        # Search/filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search notes...")
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.filter_notes)
        notes_layout.addWidget(self.search_input)
        
        # Notes list widget
        self.notes_list = QListWidget()
        self.notes_list.setMinimumHeight(400)
        self.notes_list.setStyleSheet("""
            QListWidget {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding: 15px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QListWidget::item {
                background-color: white;
                padding: 15px;
                margin: 8px 0px;
                border-radius: 10px;
                border: 1px solid #FFE4E1;
            }
            QListWidget::item:selected {
                background-color: #FFD1DC;
                color: #FF6B9D;
                border: 2px solid #FF6B9D;
            }
            QListWidget::item:hover {
                background-color: #FFE4E1;
            }
        """)
        self.notes_list.itemClicked.connect(self.load_note)
        self.notes_list.itemDoubleClicked.connect(self.open_note_reader)
        notes_layout.addWidget(self.notes_list)
        
        # Action buttons row
        action_layout = QHBoxLayout()
        
        # Read/View button
        read_btn = QPushButton("📖 Read Note")
        read_btn.setMinimumHeight(45)
        read_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
        """)
        read_btn.clicked.connect(self.open_note_reader)
        action_layout.addWidget(read_btn)
        
        # Delete button
        delete_btn = QPushButton("🗑 Delete")
        delete_btn.setMinimumHeight(45)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB6C1;
                color: white;
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
        """)
        delete_btn.clicked.connect(self.delete_note)
        action_layout.addWidget(delete_btn)
        
        action_layout.addStretch()
        notes_layout.addLayout(action_layout)
        
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def add_note(self):
        """Add a new note"""
        title = self.note_title.text().strip()
        content = self.note_content.toPlainText().strip()
        category = self.note_category.currentText()
        
        if title and content:
            note = {
                'id': len(self.notes),
                'title': title,
                'content': content,
                'category': category,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            self.notes.append(note)
            
            # Add to list
            self.refresh_notes_list()
            
            # Clear inputs
            self.note_title.clear()
            self.note_content.clear()
    
    def refresh_notes_list(self):
        """Refresh the notes list display"""
        self.notes_list.clear()
        for note in reversed(self.notes):  # Show newest first
            text = f"📄 {note['title']}\n   🏷️ {note['category']} • {note['date']}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, note['id'])
            self.notes_list.addItem(item)
    
    def load_notes(self):
        """Load notes from storage"""
        # In a real app, load from database
        # For now, start with a sample note
        if not self.notes:
            self.notes.append({
                'id': 0,
                'title': "Welcome to MedFlow Notes",
                'content': "Use this section to jot down quick study notes, clinical observations, or anything you need to remember. Click on any note to view it fully.",
                'category': 'General',
                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            self.refresh_notes_list()
    
    def load_note(self, item):
        """Load selected note for viewing/editing"""
        note_id = item.data(Qt.UserRole)
        for note in self.notes:
            if note['id'] == note_id:
                self.note_title.setText(note['title'])
                self.note_category.setCurrentText(note['category'])
                self.note_content.setText(note['content'])
                break
    
    def delete_note(self):
        """Delete selected note"""
        current_item = self.notes_list.currentItem()
        if current_item:
            note_id = current_item.data(Qt.UserRole)
            self.notes = [n for n in self.notes if n['id'] != note_id]
            self.refresh_notes_list()
            self.note_title.clear()
            self.note_content.clear()
    
    def filter_notes(self, text):
        """Filter notes based on search text"""
        if not text:
            self.refresh_notes_list()
            return
        
        self.notes_list.clear()
        for note in reversed(self.notes):
            if text.lower() in note['title'].lower() or text.lower() in note['content'].lower():
                item_text = f"📄 {note['title']}\n   🏷️ {note['category']} • {note['date']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, note['id'])
                self.notes_list.addItem(item)
    
    def update_word_count(self):
        """Update word and character count"""
        text = self.note_content.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.setText(f"{words} words | {chars} characters")
    
    def export_notes(self):
        """Export all notes to a text file"""
        from PySide6.QtWidgets import QFileDialog
        from datetime import datetime
        
        if not self.notes:
            QMessageBox.information(self, "No Notes", "No notes to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Notes",
            f"medflow_notes_{datetime.now().strftime('%Y%m%d')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("MEDFLOW STUDY NOTES EXPORT\n")
                    f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    for i, note in enumerate(reversed(self.notes), 1):
                        f.write(f"\n{'─' * 60}\n")
                        f.write(f"NOTE #{i}\n")
                        f.write(f"{'─' * 60}\n")
                        f.write(f"Title: {note['title']}\n")
                        f.write(f"Category: {note['category']}\n")
                        f.write(f"Date: {note['date']}\n\n")
                        f.write(f"Content:\n{note['content']}\n")
                    
                    f.write(f"\n{'=' * 60}\n")
                    f.write(f"Total Notes: {len(self.notes)}\n")
                    f.write("=" * 60 + "\n")
                
                QMessageBox.information(self, "Export Successful", f"Notes exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")
    
    def open_note_reader(self):
        """Open a full-screen dialog to read the selected note"""
        current_item = self.notes_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a note to read.")
            return
        
        note_id = current_item.data(Qt.UserRole)
        note = None
        for n in self.notes:
            if n['id'] == note_id:
                note = n
                break
        
        if note:
            dialog = NoteReaderDialog(note, self)
            dialog.exec()


class NoteReaderDialog(QDialog):
    """Full-screen dialog for reading notes comfortably"""
    
    def __init__(self, note: dict, parent=None):
        super().__init__(parent)
        self.note = note
        self.setWindowTitle(f"📖 {note['title']}")
        self.setMinimumSize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel(f"📄 {self.note['title']}")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #FF6B9D;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        header.addWidget(title)
        header.addStretch()
        
        # Meta info
        meta = QLabel(f"🏷️ {self.note['category']} | 🕐 {self.note['date']}")
        meta.setStyleSheet("""
            font-size: 14px;
            color: #8B6B7A;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        header.addWidget(meta)
        layout.addLayout(header)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #FFD1DC;")
        line.setMaximumHeight(2)
        layout.addWidget(line)
        
        # Content display
        content_display = QTextEdit()
        content_display.setPlainText(self.note['content'])
        content_display.setReadOnly(True)
        content_display.setStyleSheet("""
            QTextEdit {
                background-color: #FFF8FA;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                border-radius: 15px;
                padding: 30px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.8;
            }
        """)
        layout.addWidget(content_display)
        
        # Close button
        close_btn = QPushButton("✓ Close Reader")
        close_btn.setMinimumHeight(50)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 15px 40px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)


class ProfilePage(QWidget):
    """Personal profile page for medical student"""
    
    def __init__(self, database: Database = None):
        super().__init__()
        self.db = database
        self.profile_data = {}
        self.load_profile()
        self.init_ui()
        self.populate_profile_fields()
        self.load_dashboard_data()
    
    def load_profile(self):
        """Load profile from database (primary) or JSON file (fallback)"""
        defaults = {
            'name': '',
            'school': '',
            'year': '',
            'graduation': '',
            'ambitions': '',
            'specialties': '',
            'hobbies': '',
            'study_plan': '',
            'motivation': '',
            'profile_picture': '',
            'music_file': ''
        }

        if self.db:
            db_profile = self.db.get_user_profile()
            if db_profile:
                self.profile_data = {
                    'name': db_profile.get('name') or '',
                    'school': db_profile.get('school') or '',
                    'year': db_profile.get('year_of_study') or '',
                    'graduation': db_profile.get('graduation_year') or '',
                    'ambitions': db_profile.get('ambitions') or '',
                    'specialties': db_profile.get('specialties') or '',
                    'hobbies': db_profile.get('hobbies') or '',
                    'study_plan': db_profile.get('study_plan') or '',
                    'motivation': db_profile.get('motivation') or '',
                    'profile_picture': db_profile.get('profile_picture_path') or '',
                    'music_file': db_profile.get('music_file_path') or ''
                }
                return

        # Fallback to JSON file
        profile_path = Path.home() / ".medflow_profile.json"
        if profile_path.exists():
            try:
                with open(profile_path, 'r') as f:
                    self.profile_data = json.load(f)
            except:
                self.profile_data = defaults
        else:
            self.profile_data = defaults
        
    def save_profile(self):
        """Save profile to database and JSON file as backup"""
        # Also save to JSON as backup
        profile_path = Path.home() / ".medflow_profile.json"
        try:
            with open(profile_path, 'w') as f:
                json.dump(self.profile_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save JSON backup: {e}")
        
        # Save to database
        if self.db:
            if self.db.save_user_profile(self.profile_data):
                QMessageBox.information(self, "✓ Saved", "Your profile has been saved to database!")
                self.load_profile()
                self.populate_profile_fields()
                self.update_quick_stats()
            else:
                QMessageBox.warning(self, "Warning", "Profile saved to file but database save failed.")
        else:
            QMessageBox.information(self, "✓ Saved", "Your profile has been saved!")
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Header with avatar and music banner
        header = QHBoxLayout()
        
        # Profile Picture
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(100, 100)
        self.avatar_label.setStyleSheet("""
            QLabel {
                border: 3px solid #FFD1DC;
                border-radius: 50px;
                background-color: #FFF5F7;
            }
        """)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.update_profile_picture()
        header.addWidget(self.avatar_label)
        
        # Profile picture button
        self.change_pic_btn = QPushButton("📷 Change Photo")
        self.change_pic_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE4E8;
                color: #8B6B7A;
                border: 2px solid #FFD1DC;
                padding: 8px 15px;
                border-radius: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FFD1DC;
            }
        """)
        self.change_pic_btn.clicked.connect(self.select_profile_picture)
        
        pic_layout = QVBoxLayout()
        pic_layout.addWidget(self.avatar_label)
        pic_layout.addWidget(self.change_pic_btn)
        pic_layout.setAlignment(Qt.AlignCenter)
        header.addLayout(pic_layout)
        
        # Title section
        title_layout = QVBoxLayout()
        
        title = QLabel("My Medical Journey")
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #FF6B9D;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("Your personal profile and aspirations")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #8B6B7A;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        title_layout.addWidget(subtitle)
        
        header.addLayout(title_layout)
        header.addStretch()
        
        # ── Inline Music Player ──────────────────────────────────────────────
        music_widget = QWidget()
        music_widget.setMinimumWidth(220)
        music_widget.setMaximumWidth(260)
        music_widget.setStyleSheet("""
            QWidget {
                background-color: #FFF5F7;
                border: 2px solid #FFD1DC;
                border-radius: 14px;
            }
        """)
        music_layout = QVBoxLayout(music_widget)
        music_layout.setContentsMargins(12, 10, 12, 10)
        music_layout.setSpacing(6)

        # QMediaPlayer backend
        self._media_player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._media_player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.8)
        self._media_player.playbackStateChanged.connect(self._on_playback_state_changed)

        # Header label
        music_label = QLabel("🎵  Study Music")
        music_label.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #FF6B9D; background: transparent; border: none;"
        )
        music_layout.addWidget(music_label)

        # Now-playing label
        self.music_path_label = QLabel("No track selected")
        self.music_path_label.setStyleSheet(
            "font-size: 10px; color: #8B6B7A; background: transparent; border: none;"
        )
        self.music_path_label.setWordWrap(True)
        if self.profile_data.get('music_file'):
            self.music_path_label.setText(Path(self.profile_data['music_file']).name)
        music_layout.addWidget(self.music_path_label)

        # Transport row: ◀ ▶/⏸ ■
        transport = QHBoxLayout()
        transport.setSpacing(6)

        self.select_music_btn = QPushButton("📂")
        self.select_music_btn.setFixedSize(30, 30)
        self.select_music_btn.setToolTip("Choose a music file")
        self.select_music_btn.setStyleSheet(self._music_btn_css())
        self.select_music_btn.clicked.connect(self.select_music_file)
        transport.addWidget(self.select_music_btn)

        self.play_music_btn = QPushButton("▶")
        self.play_music_btn.setFixedSize(34, 34)
        self.play_music_btn.setToolTip("Play / Pause")
        self.play_music_btn.setStyleSheet(self._music_btn_css(primary=True))
        self.play_music_btn.setEnabled(bool(self.profile_data.get('music_file')))
        self.play_music_btn.clicked.connect(self.toggle_music)
        transport.addWidget(self.play_music_btn)

        stop_btn = QPushButton("■")
        stop_btn.setFixedSize(30, 30)
        stop_btn.setToolTip("Stop")
        stop_btn.setStyleSheet(self._music_btn_css())
        stop_btn.clicked.connect(self.stop_music)
        transport.addWidget(stop_btn)

        transport.addStretch()

        # Volume slider
        vol_icon = QLabel("🔊")
        vol_icon.setStyleSheet("font-size: 11px; background: transparent; border: none;")
        transport.addWidget(vol_icon)

        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(55)
        self._vol_slider.setFixedHeight(16)
        self._vol_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #FFD1DC;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #FF6B9D;
                width: 12px; height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #FF6B9D;
                border-radius: 2px;
            }
        """)
        self._vol_slider.valueChanged.connect(
            lambda v: self._audio_output.setVolume(v / 100.0)
        )
        transport.addWidget(self._vol_slider)

        music_layout.addLayout(transport)
        header.addWidget(music_widget)
        
        layout.addLayout(header)
        
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        
        # Basic Info Section
        basic_group = self.create_section("📋 Basic Information")
        basic_layout = QGridLayout()
        basic_layout.setSpacing(15)
        
        # Name
        basic_layout.addWidget(self.create_label("Full Name:"), 0, 0)
        self.name_input = self.create_line_edit("Your name...")
        self.name_input.setText(self.profile_data.get('name', ''))
        basic_layout.addWidget(self.name_input, 0, 1)
        
        # School/University
        basic_layout.addWidget(self.create_label("Medical School:"), 1, 0)
        self.school_input = self.create_line_edit("e.g., Harvard Medical School")
        self.school_input.setText(self.profile_data.get('school', ''))
        basic_layout.addWidget(self.school_input, 1, 1)
        
        # Year of Study
        basic_layout.addWidget(self.create_label("Year of Study:"), 2, 0)
        self.year_combo = QComboBox()
        self.year_combo.addItems(["Year 1 (Pre-clinical)", "Year 2 (Pre-clinical)", 
                                   "Year 3 (Clinical)", "Year 4 (Clinical)", 
                                   "Year 5 (Final/Internship)", "Resident", "Fellow", "Attending"])
        self.year_combo.setCurrentText(self.profile_data.get('year', 'Year 1 (Pre-clinical)'))
        self.year_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFF5F7;
                border: 2px solid #FFD1DC;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        basic_layout.addWidget(self.year_combo, 2, 1)
        
        # Expected Graduation
        basic_layout.addWidget(self.create_label("Expected Graduation:"), 3, 0)
        self.graduation_input = self.create_line_edit("e.g., 2028")
        self.graduation_input.setText(self.profile_data.get('graduation', ''))
        basic_layout.addWidget(self.graduation_input, 3, 1)
        
        basic_group.layout().addLayout(basic_layout)
        content_layout.addWidget(basic_group)
        
        # Career Goals Section
        career_group = self.create_section("🎯 Career Goals & Ambitions")
        
        self.ambitions_input = self.create_text_edit("What are your ambitions? (e.g., Become a pediatric surgeon, Research oncology...)")
        self.ambitions_input.setText(self.profile_data.get('ambitions', ''))
        career_group.layout().addWidget(self.ambitions_input)
        
        content_layout.addWidget(career_group)
        
        # Special Interests
        interests_group = self.create_section("🔬 Special Interests & Hobbies")
        
        interests_layout = QGridLayout()
        interests_layout.setSpacing(10)
        
        interests_layout.addWidget(self.create_label("Medical Specialties of Interest:"), 0, 0)
        self.specialties_input = self.create_line_edit("e.g., Cardiology, Neurology, Pediatrics...")
        self.specialties_input.setText(self.profile_data.get('specialties', ''))
        interests_layout.addWidget(self.specialties_input, 0, 1)
        
        interests_layout.addWidget(self.create_label("Hobbies & Activities:"), 1, 0)
        self.hobbies_input = self.create_line_edit("e.g., Reading, Hiking, Painting...")
        self.hobbies_input.setText(self.profile_data.get('hobbies', ''))
        interests_layout.addWidget(self.hobbies_input, 1, 1)
        
        interests_group.layout().addLayout(interests_layout)
        content_layout.addWidget(interests_group)
        
        # Study Plan Section
        study_group = self.create_section("📚 Study Plan & Strategies")
        
        self.study_plan_input = self.create_text_edit("Describe your study strategies, preferred resources, daily routines...")
        self.study_plan_input.setText(self.profile_data.get('study_plan', ''))
        study_group.layout().addWidget(self.study_plan_input)
        
        content_layout.addWidget(study_group)
        
        # Motivation Section
        motivation_group = self.create_section("💪 Motivation & Mantra")
        
        self.motivation_input = self.create_text_edit("What keeps you going? Your favorite quotes or personal mantra...")
        self.motivation_input.setMinimumHeight(80)
        self.motivation_input.setText(self.profile_data.get('motivation', ''))
        motivation_group.layout().addWidget(self.motivation_input)
        
        content_layout.addWidget(motivation_group)
        
        # Upcoming Events Section
        events_group = self.create_section("📅 Upcoming Events")
        self.events_list = QListWidget()
        self.events_list.setMinimumHeight(120)
        self.events_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.events_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding: 10px;
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QListWidget::item {
                background-color: #FFF5F7;
                padding: 12px;
                margin: 4px 0px;
                border-radius: 8px;
                border-left: 4px solid #FF6B9D;
            }
            QListWidget::item:hover {
                background-color: #FFE4E8;
            }
        """)
        events_group.layout().addWidget(self.events_list)
        content_layout.addWidget(events_group)
        
        # Congratulations Section (for passed exams)
        self.congrats_group = self.create_section("🎉 Recent Achievements")
        self.congrats_layout = QVBoxLayout()
        self.congrats_layout.setSpacing(10)
        
        self.congrats_label = QLabel("No recent exam results. Add your scores in the Results Ledger!")
        self.congrats_label.setStyleSheet("""
            font-size: 14px;
            color: #8B6B7A;
            font-style: italic;
            padding: 20px;
        """)
        self.congrats_label.setAlignment(Qt.AlignCenter)
        self.congrats_layout.addWidget(self.congrats_label)
        
        self.congrats_group.layout().addLayout(self.congrats_layout)
        content_layout.addWidget(self.congrats_group)
        
        # Stats/Quick Info
        self.stats_group = self.create_section("📊 Quick Stats")
        stats_layout = QHBoxLayout()
        self.stats_labels = {}
        
        stats = [
            ("notes_created", "📝 Notes Created", "0"),
            ("events_planned", "📅 Events Planned", "0"),
            ("exams_logged", "📚 Exams Logged", "0"),
            ("study_hours", "⏱️ Study Hours", "0")
        ]
        
        for key, label, value in stats:
            stat_box = QGroupBox()
            stat_box.setStyleSheet("""
                QGroupBox {
                    background-color: #FFF5F7;
                    border: 2px solid #FFD1DC;
                    border-radius: 12px;
                    padding: 15px;
                }
            """)
            stat_layout = QVBoxLayout()
            
            val_label = QLabel(value)
            val_label.setObjectName(key)
            self.stats_labels[key] = val_label
            val_label.setStyleSheet("""
                font-size: 28px;
                font-weight: 700;
                color: #FF6B9D;
            """)
            val_label.setAlignment(Qt.AlignCenter)
            
            txt_label = QLabel(label)
            txt_label.setStyleSheet("""
                font-size: 12px;
                color: #8B6B7A;
            """)
            txt_label.setAlignment(Qt.AlignCenter)
            
            stat_layout.addWidget(val_label)
            stat_layout.addWidget(txt_label)
            stat_box.setLayout(stat_layout)
            stats_layout.addWidget(stat_box)
        
        self.stats_group.layout().addLayout(stats_layout)
        content_layout.addWidget(self.stats_group)
        
        self.update_quick_stats()
        
        # Save button
        save_btn = QPushButton("💾 Save Profile")
        save_btn.setMinimumHeight(55)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 18px 40px;
                font-weight: 700;
                border-radius: 15px;
                font-size: 18px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
            QPushButton:pressed {
                background-color: #FF5280;
            }
        """)
        save_btn.clicked.connect(self.save_profile_data)
        
        clear_btn = QPushButton("🗑️ Clear Profile")
        clear_btn.setMinimumHeight(55)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                color: white;
                border: none;
                padding: 18px 40px;
                font-weight: 700;
                border-radius: 15px;
                font-size: 18px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #FF6666;
            }
            QPushButton:pressed {
                background-color: #CC2222;
            }
        """)
        clear_btn.clicked.connect(self.clear_profile_data)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        content_layout.addLayout(btn_layout)
        
        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
    
    def create_section(self, title: str) -> QGroupBox:
        """Create a styled group box section"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: 600;
                color: #FF6B9D;
                border: 2px solid #FFD1DC;
                border-radius: 15px;
                padding-top: 20px;
                margin-top: 10px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 15px;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        group.setLayout(layout)
        return group
    
    def create_label(self, text: str) -> QLabel:
        """Create a styled label"""
        label = QLabel(text)
        label.setStyleSheet("""
            font-size: 14px;
            color: #4A4A4A;
            font-weight: 500;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        return label
    
    def create_line_edit(self, placeholder: str) -> QLineEdit:
        """Create a styled line edit"""
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(40)
        edit.setStyleSheet("""
            QLineEdit {
                background-color: #FFF5F7;
                border: 2px solid #FFD1DC;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        return edit
    
    def create_text_edit(self, placeholder: str) -> QTextEdit:
        """Create a styled text edit"""
        edit = QTextEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(120)
        edit.setStyleSheet("""
            QTextEdit {
                background-color: #FFF5F7;
                border: 2px solid #FFD1DC;
                padding: 15px;
                border-radius: 10px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border: 2px solid #FF6B9D;
            }
        """)
        return edit
    
    def populate_profile_fields(self):
        """Populate UI inputs using loaded profile data."""
        self.name_input.setText(self.profile_data.get('name', ''))
        self.school_input.setText(self.profile_data.get('school', ''))
        year_value = self.profile_data.get('year', '')
        if year_value and year_value in [self.year_combo.itemText(i) for i in range(self.year_combo.count())]:
            self.year_combo.setCurrentText(year_value)
        else:
            self.year_combo.setCurrentText("Year 1 (Pre-clinical)")
        self.graduation_input.setText(self.profile_data.get('graduation', ''))
        self.ambitions_input.setText(self.profile_data.get('ambitions', ''))
        self.specialties_input.setText(self.profile_data.get('specialties', ''))
        self.hobbies_input.setText(self.profile_data.get('hobbies', ''))
        self.study_plan_input.setText(self.profile_data.get('study_plan', ''))
        self.motivation_input.setText(self.profile_data.get('motivation', ''))
        self.music_path_label.setText(Path(self.profile_data.get('music_file', '')).name if self.profile_data.get('music_file') else "No music selected")
        self.play_music_btn.setEnabled(bool(self.profile_data.get('music_file')))
        self.update_profile_picture()

    def update_quick_stats(self):
        """Update the profile quick stats from the database."""
        if not self.db or not self.stats_labels:
            return

        total_notes = self.db.get_total_study_notes()
        total_events = len(self.db.get_events())
        total_exams = len(self.db.get_exam_scores())
        study_hours_sum = sum([entry.get('hours', 0) for entry in self.db.get_study_hours()])

        self.stats_labels.get('notes_created').setText(str(total_notes))
        self.stats_labels.get('events_planned').setText(str(total_events))
        self.stats_labels.get('exams_logged').setText(str(total_exams))
        self.stats_labels.get('study_hours').setText(f"{study_hours_sum:.1f}")

    def load_dashboard_data(self):
        """Load upcoming events and exam results"""
        if not self.db:
            return
        
        # Load upcoming events (next 7 days)
        self.load_upcoming_events()
        
        # Load recent passed exams
        self.load_passed_exams()
    
    def load_upcoming_events(self):
        """Load and display upcoming events"""
        today = datetime.now().strftime("%Y-%m-%d")
        upcoming_events = []
        
        # Get events for next 7 days
        for i in range(7):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            events = self.db.get_events(date)
            for event in events:
                upcoming_events.append({
                    'date': date,
                    'title': event['title'],
                    'time': event['time_start'],
                    'category': event['category']
                })
        
        self.events_list.clear()
        
        if upcoming_events:
            for event in upcoming_events[:5]:  # Show max 5
                date_obj = datetime.strptime(event['date'], "%Y-%m-%d")
                day_name = date_obj.strftime("%a")
                date_str = date_obj.strftime("%b %d")
                
                emoji = {"Lecture": "📚", "Practical Lab": "🔬", "Dissection": "🔪", 
                        "Clinical Rotation": "🏥", "Study Session": "📖", "Exam": "📝"}.get(event['category'], "📅")
                
                text = f"{emoji} {day_name}, {date_str} at {event['time']}\n   {event['title']}"
                item = QListWidgetItem(text)
                self.events_list.addItem(item)
        else:
            item = QListWidgetItem("📭 No upcoming events in the next 7 days\n   Add events in the Planner tab!")
            item.setForeground(QColor("#8B6B7A"))
            self.events_list.addItem(item)
    
    def load_passed_exams(self):
        """Load and display congratulations for passed exams"""
        scores = self.db.get_exam_scores()
        passed_exams = [s for s in scores if s['score'] >= 50]
        
        # Clear existing widgets except label
        while self.congrats_layout.count() > 1:
            item = self.congrats_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        
        if passed_exams:
            self.congrats_label.setVisible(False)
            
            # Show last 3 passed exams
            for exam in passed_exams[:3]:
                score = exam['score']
                subject = exam['subject_name']
                exam_type = exam['exam_type']
                
                # Create achievement card
                card = QWidget()
                card.setStyleSheet("""
                    QWidget {
                        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 #FFE4E8, stop:1 #FFF5F7);
                        border: 2px solid #FF6B9D;
                        border-radius: 12px;
                        padding: 15px;
                    }
                """)
                card_layout = QHBoxLayout()
                card_layout.setContentsMargins(15, 15, 15, 15)
                
                # Trophy icon
                trophy = QLabel("🏆")
                trophy.setStyleSheet("font-size: 32px;")
                card_layout.addWidget(trophy)
                
                # Message
                message = QLabel()
                if score >= 80:
                    message_text = f"🌟 AMAZING! You aced the {subject} {exam_type}!\n   Score: {score:.1f}% - Outstanding work!"
                elif score >= 70:
                    message_text = f"🎉 Great job! You passed {subject} {exam_type}!\n   Score: {score:.1f}% - Well done!"
                else:
                    message_text = f"✅ Congrats! You passed {subject} {exam_type}!\n   Score: {score:.1f}% - Keep it up!"
                
                message.setText(message_text)
                message.setStyleSheet("""
                    font-size: 14px;
                    color: #4A4A4A;
                    font-weight: 500;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                """)
                card_layout.addWidget(message, stretch=1)
                
                card.setLayout(card_layout)
                self.congrats_layout.addWidget(card)
        else:
            self.congrats_label.setVisible(True)
            self.congrats_label.setText("No exam results yet. Add your scores in the Results Ledger!\nPass an exam (50%+) to see congratulations here! 🎓")
        self.update_quick_stats()
    
    def save_profile_data(self):
        """Collect and save profile data"""
        self.profile_data['name'] = self.name_input.text()
        self.profile_data['school'] = self.school_input.text()
        self.profile_data['year'] = self.year_combo.currentText()
        self.profile_data['graduation'] = self.graduation_input.text()
        self.profile_data['ambitions'] = self.ambitions_input.toPlainText()
        self.profile_data['specialties'] = self.specialties_input.text()
        self.profile_data['hobbies'] = self.hobbies_input.text()
        self.profile_data['study_plan'] = self.study_plan_input.toPlainText()
        self.profile_data['motivation'] = self.motivation_input.toPlainText()
        self.save_profile()
    
    def clear_profile_data(self):
        """Clear all profile data"""
        reply = QMessageBox.question(self, "Clear Profile", 
                                   "Are you sure you want to clear all profile data? This cannot be undone.",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Clear fields
            self.name_input.clear()
            self.school_input.clear()
            self.year_combo.setCurrentIndex(0)
            self.graduation_input.clear()
            self.ambitions_input.clear()
            self.specialties_input.clear()
            self.hobbies_input.clear()
            self.study_plan_input.clear()
            self.motivation_input.clear()
            
            # Clear profile data
            self.profile_data = {}
            
            # Clear from database
            if self.db:
                self.db.clear_user_profile()
            
            # Clear JSON backup
            profile_path = Path.home() / ".medflow_profile.json"
            if profile_path.exists():
                profile_path.unlink()
            
            # Update UI
            self.update_profile_picture()
            self.update_quick_stats()
            
            QMessageBox.information(self, "✓ Cleared", "Profile data has been cleared.")
    
    def update_profile_picture(self):
        """Update the profile picture display"""
        if self.profile_data.get('profile_picture') and Path(self.profile_data['profile_picture']).exists():
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(self.profile_data['profile_picture'])
            scaled = pixmap.scaled(90, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.avatar_label.setPixmap(scaled)
        else:
            self.avatar_label.setText("👤")
            self.avatar_label.setStyleSheet("""
                QLabel {
                    border: 3px solid #FFD1DC;
                    border-radius: 50px;
                    background-color: #FFF5F7;
                    font-size: 40px;
                }
            """)
    
    def select_profile_picture(self):
        """Open file dialog to select profile picture"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Picture",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        
        if file_path:
            self.profile_data['profile_picture'] = file_path
            self.update_profile_picture()
    
    # ── Music player helpers ──────────────────────────────────────────────

    @staticmethod
    def _music_btn_css(primary: bool = False) -> str:
        if primary:
            return """
                QPushButton {
                    background-color: #FF6B9D; color: white;
                    border: none; border-radius: 8px;
                    font-size: 14px; font-weight: 700;
                }
                QPushButton:hover { background-color: #FF8FA3; }
                QPushButton:disabled { background-color: #FFD1DC; color: white; }
            """
        return """
            QPushButton {
                background-color: #FFE4E8; color: #8B6B7A;
                border: 2px solid #FFD1DC; border-radius: 7px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #FFD1DC; }
        """

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_music_btn.setText("⏸")
            self.play_music_btn.setToolTip("Pause")
        else:
            self.play_music_btn.setText("▶")
            self.play_music_btn.setToolTip("Play")

    def select_music_file(self):
        """Open file dialog to select music file"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Study Music",
            str(Path.home()),
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a);;All Files (*)"
        )
        if file_path:
            self.profile_data['music_file'] = file_path
            self.music_path_label.setText(Path(file_path).name)
            self.play_music_btn.setEnabled(True)
            self._media_player.setSource(QUrl.fromLocalFile(file_path))
            self.save_profile()

    def toggle_music(self):
        """Play or pause the current track."""
        if not self.profile_data.get('music_file'):
            return
        if self._media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._media_player.pause()
        else:
            src = self._media_player.source()
            if not src.isValid() or src.isEmpty():
                self._media_player.setSource(
                    QUrl.fromLocalFile(self.profile_data['music_file'])
                )
            self._media_player.play()

    def stop_music(self):
        """Stop playback and reset position."""
        self._media_player.stop()

    def play_music(self):
        """Legacy alias — kept for any existing connections."""
        self.toggle_music()


class LibrarySection(QWidget):
    """Digital library for medical books"""
    
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.books = []
        self.current_category = "All"
        self.init_ui()
        self.load_books()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📚 Medical Library")
        title.setStyleSheet("font-size: 28px; font-weight: 700; color: #FF6B9D;")
        header.addWidget(title)
        
        self.stats_label = QLabel("0 books")
        self.stats_label.setStyleSheet("font-size: 14px; color: #8B6B7A; padding: 5px 15px; background-color: #FFF5F7; border-radius: 10px;")
        header.addWidget(self.stats_label)
        header.addStretch()
        
        add_btn = QPushButton("➕ Add Book")
        add_btn.setStyleSheet("background-color: #FF6B9D; color: white; border: none; padding: 10px 20px; border-radius: 10px; font-weight: 600;")
        add_btn.clicked.connect(self.show_add_book_dialog)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Filter bar
        filter_bar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search books...")
        self.search_input.setStyleSheet("background-color: #FFF5F7; border: 2px solid #FFD1DC; padding: 10px; border-radius: 10px;")
        self.search_input.textChanged.connect(self.load_books)
        filter_bar.addWidget(self.search_input, stretch=2)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Anatomy", "Physiology", "Biochemistry", "Pathology", "Pharmacology", "Clinical", "Custom"])
        self.category_combo.setStyleSheet("background-color: #FFF5F7; border: 2px solid #FFD1DC; padding: 10px; border-radius: 10px;")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        filter_bar.addWidget(QLabel("Category:"))
        filter_bar.addWidget(self.category_combo)
        
        layout.addLayout(filter_bar)
        
        # Grid container for books
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.books_container = QWidget()
        self.books_grid = QGridLayout()
        self.books_grid.setSpacing(15)
        self.books_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.books_container.setLayout(self.books_grid)
        
        scroll.setWidget(self.books_container)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
    
    def on_category_changed(self, category):
        self.current_category = category
        self.load_books()
    
    def load_books(self):
        # Clear grid
        while self.books_grid.count() > 0:
            item = self.books_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        search_text = self.search_input.text().strip()
        if search_text:
            self.books = self.db.get_library_books(search=search_text)
        elif self.current_category != "All":
            self.books = self.db.get_library_books(category=self.current_category)
        else:
            self.books = self.db.get_library_books()
        
        total = len(self.books)
        read_count = sum(1 for b in self.books if b.get('is_read'))
        self.stats_label.setText(f"{total} books • {read_count} read")
        
        if not self.books:
            empty = QLabel("📚 No books yet. Click 'Add Book' to start!")
            empty.setStyleSheet("font-size: 16px; color: #8B6B7A; padding: 50px;")
            empty.setAlignment(Qt.AlignCenter)
            self.books_grid.addWidget(empty, 0, 0)
        else:
            # Add books in grid (3 columns)
            for idx, book in enumerate(self.books):
                row = idx // 3
                col = idx % 3
                card = self.create_book_card(book)
                self.books_grid.addWidget(card, row, col)
    
    def create_book_card(self, book):
        card = QFrame()
        card.setMinimumSize(200, 270)
        card.setMaximumWidth(260)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #FFD1DC;
                border-radius: 15px;
            }
            QFrame:hover {
                border: 2px solid #FF6B9D;
                background-color: #FFFAFA;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(7)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Book cover/icon area
        cover = QLabel("📖" if not book.get('is_read') else "✅")
        cover.setAlignment(Qt.AlignCenter)
        cover.setStyleSheet("""
            font-size: 52px;
            background-color: #FFF5F7;
            border-radius: 10px;
            padding: 12px;
        """)
        layout.addWidget(cover)
        
        # Title
        title_text = book['title']
        title = QLabel(title_text)
        title.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #4A4A4A;
        """)
        title.setWordWrap(True)
        title.setToolTip(title_text)
        layout.addWidget(title)
        
        # Author
        if book.get('author'):
            author_text = book['author'][:20] + "..." if len(book['author']) > 20 else book['author']
            author = QLabel(f"✍️ {author_text}")
            author.setStyleSheet("font-size: 11px; color: #8B6B7A;")
            layout.addWidget(author)
        
        # Category badge
        cat = book.get('custom_category') or book.get('category', 'General')
        cat_label = QLabel(f"📁 {cat[:15]}")
        cat_label.setStyleSheet("""
            font-size: 10px;
            color: #FF6B9D;
            background-color: #FFF5F7;
            padding: 2px 8px;
            border-radius: 8px;
        """)
        layout.addWidget(cat_label)
        
        # Reading progress bar (only shown when pages info is available)
        pages = book.get('pages') or 0
        current_page = book.get('current_page') or 0
        if pages > 0:
            progress_pct = min(100, int(current_page / pages * 100))
            prog_label = QLabel(f"p.{current_page}/{pages}  ({progress_pct}%)")
            prog_label.setStyleSheet("font-size: 10px; color: #8B6B7A;")
            layout.addWidget(prog_label)
            from PySide6.QtWidgets import QProgressBar
            prog_bar = QProgressBar()
            prog_bar.setValue(progress_pct)
            prog_bar.setFixedHeight(6)
            prog_bar.setTextVisible(False)
            prog_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 3px;
                    background-color: #FFE4E8;
                }
                QProgressBar::chunk {
                    background-color: #FF6B9D;
                    border-radius: 3px;
                }
            """)
            layout.addWidget(prog_bar)

        # Rating stars
        if book.get('rating'):
            stars = QLabel("⭐" * book['rating'])
            stars.setStyleSheet("font-size: 11px;")
            layout.addWidget(stars)
        
        layout.addStretch()
        
        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        
        read_btn = QPushButton("📖")
        read_btn.setFixedSize(32, 32)
        read_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
        """)
        read_btn.setToolTip("Read")
        read_btn.clicked.connect(lambda: self.open_book(book['id']))
        btn_layout.addWidget(read_btn)
        
        rate_btn = QPushButton("⭐")
        rate_btn.setFixedSize(32, 32)
        rate_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE4E8;
                color: #8B6B7A;
                border: 1px solid #FFD1DC;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD1DC;
            }
        """)
        rate_btn.setToolTip("Rate")
        rate_btn.clicked.connect(lambda: self.rate_book(book['id']))
        btn_layout.addWidget(rate_btn)
        
        del_btn = QPushButton("🗑️")
        del_btn.setFixedSize(32, 32)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB6C1;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
        """)
        del_btn.setToolTip("Remove")
        del_btn.clicked.connect(lambda: self.delete_book(book['id']))
        btn_layout.addWidget(del_btn)
        
        layout.addLayout(btn_layout)
        card.setLayout(layout)
        return card
    
    def show_add_book_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Book")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        title = QLineEdit()
        title.setPlaceholderText("Book Title")
        layout.addWidget(title)
        
        author = QLineEdit()
        author.setPlaceholderText("Author")
        layout.addWidget(author)
        
        cat = QComboBox()
        cat.addItems(["Anatomy", "Physiology", "Biochemistry", "Pathology", "Pharmacology", "Clinical", "Custom"])
        layout.addWidget(cat)
        
        custom = QLineEdit()
        custom.setPlaceholderText("Custom Category")
        layout.addWidget(custom)
        
        file_btn = QPushButton("📁 Select File")
        file_path = [None]
        def select_file():
            from PySide6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(dialog, "Select Book", str(Path.home()), "Books (*.pdf *.epub *.txt)")
            if path:
                file_path[0] = path
                file_btn.setText(f"📄 {Path(path).name[:20]}...")
        file_btn.clicked.connect(select_file)
        layout.addWidget(file_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(lambda: self.save_book(dialog, title.text(), author.text(), cat.currentText(), custom.text(), file_path[0]))
        layout.addWidget(save_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_book(self, dialog, title, author, category, custom, file_path):
        if not title or not file_path:
            QMessageBox.warning(dialog, "Error", "Title and file required!")
            return
        
        custom_cat = custom if category == "Custom" else ""
        self.db.add_library_book(title, author, file_path, category, custom_cat)
        dialog.accept()
        self.load_books()
    
    def open_book(self, book_id):
        book = next((b for b in self.books if b['id'] == book_id), None)
        if book and Path(book['file_path']).exists():
            import subprocess
            subprocess.Popen(['xdg-open', book['file_path']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            QMessageBox.warning(self, "Error", "Book file not found!")
    
    def rate_book(self, book_id):
        dialog = QDialog(self)
        dialog.setWindowTitle("Rate Book")
        layout = QVBoxLayout()
        
        for i in range(1, 6):
            btn = QPushButton("⭐" * i)
            btn.clicked.connect(lambda checked, r=i: self.save_rating(book_id, r, dialog))
            layout.addWidget(btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_rating(self, book_id, rating, dialog):
        self.db.update_book_rating(book_id, rating)
        dialog.accept()
        self.load_books()
    
    def delete_book(self, book_id):
        reply = QMessageBox.question(self, "Confirm", "Remove this book from library?")
        if reply == QMessageBox.Yes:
            self.db.delete_library_book(book_id)
            self.load_books()


class MedFlowMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()
        self.setup_system_tray()
        self.apply_light_theme()
    
    def init_ui(self):
        self.setWindowTitle("MedFlow")
        self.setGeometry(100, 100, 1400, 900)
        
        # Load and set window icon
        icon_path = Path(__file__).parent / "medflow-icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Create tab widget with iOS-style light pink theme
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #FFF8FA;
            }
            QTabBar::tab {
                background-color: #FFE4E8;
                color: #8B6B7A;
                padding: 12px 28px;
                border: none;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                font-size: 14px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #FF6B9D;
                color: white;
                border: none;
            }
            QTabBar::tab:hover:!selected {
                background-color: #FFD1DC;
            }
        """)
        
        # Tab 1: Full Page Schedule Planner (dedicated large calendar view)
        self.schedule_planner = FullPageSchedulePlanner(self.db)
        self.tab_widget.addTab(self.schedule_planner, "📅 Planner")
        
        # Tab 2: Results Ledger (Performance Tracker)
        self.results_ledger = ResultsLedger(self.db)
        self.tab_widget.addTab(self.results_ledger, "Results Ledger")
        
        # Tab 3: Notes Section
        self.notes_section = NotesSection(self.db)
        self.tab_widget.addTab(self.notes_section, "📝 Notes")
        
        # Tab 4: Library Section
        self.library_section = LibrarySection(self.db)
        self.tab_widget.addTab(self.library_section, "📚 Library")
        
        # Tab 5: Profile Page
        self.profile_page = ProfilePage(self.db)
        self.tab_widget.addTab(self.profile_page, "👤 Profile")
        
        self.setCentralWidget(self.tab_widget)

        # Status bar with live clock and date
        self._status_bar = self.statusBar()
        self._status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #FFE4E8;
                color: #8B6B7A;
                font-size: 13px;
                padding: 4px 12px;
                border-top: 1px solid #FFD1DC;
            }
        """)
        self._clock_label = QLabel()
        self._status_bar.addPermanentWidget(self._clock_label)
        self._update_clock()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(30000)  # refresh every 30 s

        # Keyboard shortcut: Ctrl+N → add event on Planner tab
        add_event_shortcut = QAction("Add Event", self)
        add_event_shortcut.setShortcut("Ctrl+N")
        add_event_shortcut.triggered.connect(self._shortcut_add_event)
        self.addAction(add_event_shortcut)

    def _update_clock(self):
        now = datetime.now()
        day_str = now.strftime("%A, %B %-d %Y")
        time_str = now.strftime("%-I:%M %p")
        self._clock_label.setText(f"📅  {day_str}   🕐  {time_str}")

    def _shortcut_add_event(self):
        """Ctrl+N: switch to the Planner tab and open Add Event dialog"""
        self.tab_widget.setCurrentIndex(0)
        if hasattr(self.schedule_planner, 'show_add_event_dialog'):
            self.schedule_planner.show_add_event_dialog()
    
    def create_dashboard_tab(self):
        """Create the main schedule tab with clean 3-pane layout"""
        dashboard_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Horizontal)
        
        # Left pane - Academic Ledger
        self.academic_ledger = AcademicLedger(self.db)
        self.academic_ledger.event_selected.connect(self.on_event_selected)
        splitter.addWidget(self.academic_ledger)
        
        # Middle pane - Timer and Active Task
        middle_pane = QWidget()
        middle_layout = QVBoxLayout()
        middle_layout.setSpacing(20)
        middle_layout.setContentsMargins(20, 20, 20, 20)
        
        self.pulse_timer = PulseTimer()
        middle_layout.addWidget(self.pulse_timer)
        
        # Current task display
        self.current_task_label = QLabel("No event selected")
        self.current_task_label.setAlignment(Qt.AlignCenter)
        self.current_task_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                color: #00D4FF;
                padding: 30px;
                background-color: #1A1F2E;
                border-radius: 15px;
                border: 2px solid #00D4FF;
            }
        """)
        middle_layout.addWidget(self.current_task_label)
        
        middle_pane.setLayout(middle_layout)
        splitter.addWidget(middle_pane)
        
        # Right pane - Active Recall Sidebar
        self.active_recall = ActiveRecallSidebar(self.db)
        splitter.addWidget(self.active_recall)
        
        # Set splitter sizes (1:2:1 ratio)
        splitter.setSizes([400, 800, 400])
        
        main_layout.addWidget(splitter)
        dashboard_widget.setLayout(main_layout)
        
        return dashboard_widget
    
    def on_event_selected(self, event_id: int):
        """Handle event selection"""
        self.active_recall.set_event(event_id)
        
        # Update current task display
        events = self.db.get_events()
        for event in events:
            if event['id'] == event_id:
                self.current_task_label.setText(
                    f"Current: {event['title']} ({event['category']})"
                )
                break
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Set icon
        icon_path = Path(__file__).parent / "medflow-icon.svg"
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def apply_light_theme(self):
        """Apply iOS-style light pink/beige theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFF8FA;
                color: #4A4A4A;
            }
            QWidget {
                background-color: #FFF8FA;
                color: #4A4A4A;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QGroupBox {
                font-weight: 600;
                color: #FF6B9D;
                background-color: white;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                font-weight: 600;
            }
            QLabel {
                color: #4A4A4A;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 10px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #FF8FA3;
            }
            QPushButton:pressed {
                background-color: #FF5280;
            }
            QLineEdit, QTextEdit, QComboBox, QTimeEdit {
                background-color: #FFF5F7;
                color: #4A4A4A;
                border: 2px solid #FFD1DC;
                padding: 10px;
                border-radius: 10px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #FF6B9D;
            }
            QSplitter::handle {
                background-color: #FFD1DC;
            }
            QScrollBar:vertical {
                background-color: #FFE4E8;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #FFB6C1;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #FF6B9D;
            }
            QCalendarWidget {
                background-color: white;
                border-radius: 15px;
            }
        """)
    
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("MedFlow")
    
    # Create and show main window
    window = MedFlowMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
