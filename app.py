#!/usr/bin/env python3
"""
MedFlow Web - Flask web application for MedFlow medical student planner
"""

import sys
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

DB_PATH = str(Path(__file__).parent / "medflow.db")


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")

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

            try:
                cursor.execute("SELECT reminder_enabled FROM academic_events LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE academic_events ADD COLUMN reminder_enabled INTEGER DEFAULT 1")

            try:
                cursor.execute("SELECT reminder_minutes FROM academic_events LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE academic_events ADD COLUMN reminder_minutes INTEGER DEFAULT 15")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    high_yield_fact TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES academic_events (id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_debt (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES academic_events (id)
                )
            """)

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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS completed_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    completed_date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

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
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

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

    def add_event(self, title, category, subtopic, date, time_start, time_end,
                  notes="", reminder_minutes=15, reminder_enabled=True):
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

    def get_events(self, date=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if date:
                cursor.execute("SELECT * FROM academic_events WHERE date = ? ORDER BY time_start", (date,))
            else:
                cursor.execute("SELECT * FROM academic_events ORDER BY date, time_start")
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_events_for_month(self, year, month):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM academic_events
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
                ORDER BY date, time_start
            """, (str(year), f"{month:02d}"))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_upcoming_events(self, minutes_ahead=60):
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

    def delete_event(self, event_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM academic_events WHERE id = ?", (event_id,))
            cursor.execute("DELETE FROM study_notes WHERE event_id = ?", (event_id,))
            cursor.execute("DELETE FROM study_debt WHERE event_id = ?", (event_id,))
            conn.commit()
            return cursor.rowcount > 0

    def mark_event_complete(self, event_id, completed):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE academic_events SET completed = ? WHERE id = ?",
                           (1 if completed else 0, event_id))
            conn.commit()

    def add_study_note(self, event_id, fact):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO study_notes (event_id, high_yield_fact) VALUES (?, ?)",
                           (event_id, fact))
            conn.commit()

    def get_study_notes(self, event_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT high_yield_fact FROM study_notes WHERE event_id = ?", (event_id,))
            return [row[0] for row in cursor.fetchall()]

    def save_study_notes(self, event_id, facts):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM study_notes WHERE event_id = ?", (event_id,))
            for fact in facts:
                if fact.strip():
                    cursor.execute("INSERT INTO study_notes (event_id, high_yield_fact) VALUES (?, ?)",
                                   (event_id, fact.strip()))
            conn.commit()

    def add_study_debt(self, event_id, reason):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO study_debt (event_id, reason) VALUES (?, ?)", (event_id, reason))
            conn.commit()

    def get_study_debt(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sd.id, sd.event_id, sd.reason, sd.created_at, ae.title, ae.category, ae.subtopic, ae.date
                FROM study_debt sd
                JOIN academic_events ae ON sd.event_id = ae.id
                ORDER BY sd.created_at DESC
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def resolve_study_debt(self, debt_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM study_debt WHERE id = ?", (debt_id,))
            conn.commit()

    def add_exam_score(self, subject_name, exam_type, score, date, notes="", study_hours=0):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO exam_scores (subject_name, exam_type, score, date, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (subject_name, exam_type, score, date, notes))
            conn.commit()
            exam_id = cursor.lastrowid
        if study_hours > 0:
            self.add_study_hours(date, study_hours, subject_name)
        return exam_id

    def get_exam_scores(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exam_scores ORDER BY date DESC")
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def delete_exam_score(self, exam_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM exam_scores WHERE id = ?", (exam_id,))
            conn.commit()

    def clear_all_exam_scores(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM exam_scores")
            conn.commit()

    def add_study_hours(self, date, hours, subject="", notes=""):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, hours FROM study_hours WHERE date = ? AND subject = ?", (date, subject))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE study_hours SET hours = ? WHERE id = ?",
                               (existing[1] + hours, existing[0]))
            else:
                cursor.execute("INSERT INTO study_hours (date, hours, subject, notes) VALUES (?, ?, ?, ?)",
                               (date, hours, subject, notes))
            conn.commit()

    def get_study_hours_for_correlation(self):
        with sqlite3.connect(self.db_path) as conn:
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
                    sh.date >= date(es.date, '-7 days') AND
                    sh.date < es.date
                GROUP BY es.id, es.subject_name, es.score, es.date
                ORDER BY es.date
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def save_user_profile(self, profile_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_profile
                (id, name, school, year_of_study, graduation_year, ambitions,
                 specialties, hobbies, study_plan, motivation, profile_picture_path, updated_at)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
                profile_data.get('profile_picture', '')
            ))
            conn.commit()

    def get_user_profile(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profile WHERE id = 1")
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return {}

    def clear_all_data(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM academic_events")
            cursor.execute("DELETE FROM study_notes")
            cursor.execute("DELETE FROM study_debt")
            cursor.execute("DELETE FROM exam_scores")
            cursor.execute("DELETE FROM study_hours")
            cursor.execute("DELETE FROM completed_tasks")
            cursor.execute("DELETE FROM user_profile")
            cursor.execute("DELETE FROM library_books")
            cursor.execute("DELETE FROM app_notes")
            conn.commit()

    def add_library_book(self, title, author, file_path, category="General", custom_category="", description="", pages=0):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO library_books (title, author, file_path, category, custom_category, description, pages)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, author, file_path, category, custom_category, description, pages))
            conn.commit()
            return cursor.lastrowid

    def get_library_books(self, category=None, search=None):
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

    def update_book_rating(self, book_id, rating):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE library_books SET rating = ? WHERE id = ?", (rating, book_id))
            conn.commit()

    def update_book_status(self, book_id, is_read, current_page=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if current_page is not None:
                cursor.execute("UPDATE library_books SET is_read = ?, current_page = ?, last_opened = CURRENT_TIMESTAMP WHERE id = ?",
                               (1 if is_read else 0, current_page, book_id))
            else:
                cursor.execute("UPDATE library_books SET is_read = ?, last_opened = CURRENT_TIMESTAMP WHERE id = ?",
                               (1 if is_read else 0, book_id))
            conn.commit()

    def delete_library_book(self, book_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM library_books WHERE id = ?", (book_id,))
            conn.commit()

    def add_note(self, title, content, category="General"):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO app_notes (title, content, category) VALUES (?, ?, ?)",
                           (title, content, category))
            conn.commit()
            return cursor.lastrowid

    def get_notes(self, search=None):
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

    def update_note(self, note_id, title, content, category):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE app_notes SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (title, content, category, note_id))
            conn.commit()

    def delete_note(self, note_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM app_notes WHERE id = ?", (note_id,))
            conn.commit()

    def get_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            stats = {}
            cursor.execute("SELECT COUNT(*) FROM academic_events")
            stats['total_events'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM academic_events WHERE completed = 1")
            stats['completed_events'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM exam_scores")
            stats['total_exams'] = cursor.fetchone()[0]
            cursor.execute("SELECT AVG(score) FROM exam_scores")
            avg = cursor.fetchone()[0]
            stats['avg_score'] = round(avg, 1) if avg else 0
            cursor.execute("SELECT COUNT(*) FROM study_debt")
            stats['study_debt'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM app_notes")
            stats['total_notes'] = cursor.fetchone()[0]
            cursor.execute("SELECT COALESCE(SUM(hours), 0) FROM study_hours")
            stats['total_study_hours'] = round(cursor.fetchone()[0], 1)
            cursor.execute("SELECT COUNT(*) FROM library_books")
            stats['total_books'] = cursor.fetchone()[0]
            return stats

    def auto_schedule_debt(self):
        debts = self.get_study_debt()
        if not debts:
            return []
        all_events = self.get_events()
        tomorrow = datetime.now().date() + timedelta(days=1)
        standard_blocks = [("09:00", "11:00"), ("11:00", "13:00"), ("14:00", "16:00"), ("16:00", "18:00")]
        free_slots = []
        for d in range(7):
            current_date = tomorrow + timedelta(days=d)
            date_str = current_date.strftime("%Y-%m-%d")
            for start_t, end_t in standard_blocks:
                overlap = False
                for event in all_events:
                    if event['date'] == date_str:
                        if start_t < event['time_end'] and event['time_start'] < end_t:
                            overlap = True
                            break
                if not overlap:
                    free_slots.append((date_str, start_t, end_t))
        scheduled = []
        for i, debt in enumerate(debts):
            if i >= len(free_slots):
                break
            slot_date, slot_start, slot_end = free_slots[i]
            new_id = self.add_event(
                f"[RESCHEDULED] {debt['title']}",
                debt['category'],
                debt.get('subtopic', ''),
                slot_date, slot_start, slot_end,
                f"Auto-rescheduled study debt: {debt['reason']}"
            )
            self.resolve_study_debt(debt['id'])
            scheduled.append({'title': debt['title'], 'date': slot_date, 'time': slot_start})
        return scheduled


db = Database()


@app.route('/')
def index():
    return render_template('index.html')


# === EVENTS API ===
@app.route('/api/events', methods=['GET'])
def get_events():
    date = request.args.get('date')
    events = db.get_events(date)
    return jsonify(events)

@app.route('/api/events/month', methods=['GET'])
def get_events_month():
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    events = db.get_events_for_month(year, month)
    return jsonify(events)

@app.route('/api/events/upcoming', methods=['GET'])
def get_upcoming():
    events = db.get_upcoming_events(minutes_ahead=60)
    return jsonify(events)

@app.route('/api/events', methods=['POST'])
def add_event():
    data = request.json
    event_id = db.add_event(
        data['title'], data['category'], data.get('subtopic', ''),
        data['date'], data['time_start'], data['time_end'],
        data.get('notes', ''), data.get('reminder_minutes', 15),
        data.get('reminder_enabled', True)
    )
    return jsonify({'id': event_id, 'success': True})

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    db.delete_event(event_id)
    return jsonify({'success': True})

@app.route('/api/events/<int:event_id>/complete', methods=['POST'])
def complete_event(event_id):
    data = request.json
    db.mark_event_complete(event_id, data.get('completed', True))
    return jsonify({'success': True})


# === STUDY NOTES API ===
@app.route('/api/notes/study/<int:event_id>', methods=['GET'])
def get_study_notes(event_id):
    notes = db.get_study_notes(event_id)
    return jsonify(notes)

@app.route('/api/notes/study/<int:event_id>', methods=['POST'])
def save_study_notes(event_id):
    data = request.json
    db.save_study_notes(event_id, data.get('facts', []))
    return jsonify({'success': True})


# === STUDY DEBT API ===
@app.route('/api/debt', methods=['GET'])
def get_debt():
    debts = db.get_study_debt()
    return jsonify(debts)

@app.route('/api/debt', methods=['POST'])
def add_debt():
    data = request.json
    db.add_study_debt(data['event_id'], data.get('reason', 'Missed or incomplete'))
    return jsonify({'success': True})

@app.route('/api/debt/<int:debt_id>', methods=['DELETE'])
def resolve_debt(debt_id):
    db.resolve_study_debt(debt_id)
    return jsonify({'success': True})

@app.route('/api/debt/auto-schedule', methods=['POST'])
def auto_schedule():
    scheduled = db.auto_schedule_debt()
    return jsonify({'scheduled': scheduled, 'count': len(scheduled)})


# === EXAM SCORES API ===
@app.route('/api/exams', methods=['GET'])
def get_exams():
    exams = db.get_exam_scores()
    return jsonify(exams)

@app.route('/api/exams', methods=['POST'])
def add_exam():
    data = request.json
    exam_id = db.add_exam_score(
        data['subject_name'], data['exam_type'], float(data['score']),
        data['date'], data.get('notes', ''), float(data.get('study_hours', 0))
    )
    return jsonify({'id': exam_id, 'success': True})

@app.route('/api/exams/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    db.delete_exam_score(exam_id)
    return jsonify({'success': True})

@app.route('/api/exams/clear', methods=['POST'])
def clear_exams():
    db.clear_all_exam_scores()
    return jsonify({'success': True})

@app.route('/api/exams/correlation', methods=['GET'])
def exam_correlation():
    data = db.get_study_hours_for_correlation()
    return jsonify(data)


# === PROFILE API ===
@app.route('/api/profile', methods=['GET'])
def get_profile():
    profile = db.get_user_profile()
    return jsonify(profile)

@app.route('/api/profile', methods=['POST'])
def save_profile():
    data = request.json
    db.save_user_profile(data)
    return jsonify({'success': True})

@app.route('/api/profile/clear', methods=['POST'])
def clear_profile():
    db.clear_all_data()
    return jsonify({'success': True})


# === STATS API ===
@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = db.get_stats()
    return jsonify(stats)


# === LIBRARY API ===
@app.route('/api/library', methods=['GET'])
def get_library():
    category = request.args.get('category')
    search = request.args.get('search')
    books = db.get_library_books(category, search)
    return jsonify(books)

@app.route('/api/library', methods=['POST'])
def add_book():
    data = request.json
    book_id = db.add_library_book(
        data['title'], data.get('author', ''), data.get('file_path', ''),
        data.get('category', 'General'), data.get('custom_category', ''),
        data.get('description', ''), int(data.get('pages', 0))
    )
    return jsonify({'id': book_id, 'success': True})

@app.route('/api/library/<int:book_id>/rating', methods=['POST'])
def rate_book(book_id):
    data = request.json
    db.update_book_rating(book_id, data['rating'])
    return jsonify({'success': True})

@app.route('/api/library/<int:book_id>/status', methods=['POST'])
def book_status(book_id):
    data = request.json
    db.update_book_status(book_id, data.get('is_read', False), data.get('current_page'))
    return jsonify({'success': True})

@app.route('/api/library/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    db.delete_library_book(book_id)
    return jsonify({'success': True})


# === NOTES API ===
@app.route('/api/notes', methods=['GET'])
def get_notes():
    search = request.args.get('search')
    notes = db.get_notes(search)
    return jsonify(notes)

@app.route('/api/notes', methods=['POST'])
def add_note():
    data = request.json
    note_id = db.add_note(data['title'], data['content'], data.get('category', 'General'))
    return jsonify({'id': note_id, 'success': True})

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.json
    db.update_note(note_id, data['title'], data['content'], data.get('category', 'General'))
    return jsonify({'success': True})

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    db.delete_note(note_id)
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
