"""Repository pattern for standardized database access.

This module provides repository classes that return typed model objects
instead of raw dictionaries, improving type safety and consistency.
"""

from typing import List, Optional, Dict, Any
from medflow.models.event import AcademicEvent
from medflow.models.note import AppNote
from medflow.database import Database


class EventRepository:
    """Standardized access to academic events with typed models."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def create(self, event: AcademicEvent) -> int:
        """Create a new academic event."""
        return self.db.add_event(
            title=event.title,
            category=event.category,
            subtopic=event.subtopic or "",
            date=event.date,
            time_start=event.time_start,
            time_end=event.time_end,
            notes=event.notes or "",
            reminder_minutes=event.reminder_minutes,
            reminder_enabled=event.reminder_enabled
        )
    
    def get_all(self) -> List[AcademicEvent]:
        """Get all events as model objects."""
        return [AcademicEvent.from_dict(d) for d in self.db.get_events()]
    
    def get_by_date(self, date: str) -> List[AcademicEvent]:
        """Get events for a specific date."""
        return [AcademicEvent.from_dict(d) for d in self.db.get_events(date)]
    
    def get_upcoming(self, minutes_ahead: int = 30) -> List[AcademicEvent]:
        """Get upcoming events within specified minutes."""
        return [AcademicEvent.from_dict(d) for d in self.db.get_upcoming_events(minutes_ahead)]
    
    def mark_completed(self, event_id: int, completed: bool) -> bool:
        """Toggle event completion status."""
        return self.db.mark_event_completed(event_id, completed)


class NoteRepository:
    """Standardized access to app notes with typed models."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def create(self, note: AppNote) -> int:
        """Create a new note."""
        return self.db.add_app_note(note.title, note.content, note.category)
    
    def get_all(self, search: Optional[str] = None) -> List[AppNote]:
        """Get all notes or filter by search."""
        notes = self.db.get_app_notes(search)
        return [AppNote.from_dict(d) for d in notes]
    
    def get_by_id(self, note_id: int) -> Optional[AppNote]:
        """Get a single note by ID."""
        data = self.db.get_app_note_by_id(note_id)
        return AppNote.from_dict(data) if data else None
    
    def update(self, note_id: int, note: AppNote) -> bool:
        """Update an existing note."""
        return self.db.update_app_note(note_id, note.title, note.content, note.category)
    
    def delete(self, note_id: int) -> bool:
        """Delete a note."""
        return self.db.delete_app_note(note_id)


class ExamRepository:
    """Standardized access to exam scores."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def create(self, subject: str, exam_type: str, score: float, 
               date: str, notes: str = "") -> int:
        """Add a new exam score."""
        return self.db.add_exam_score(subject, exam_type, score, date, notes)
    
    def get_all(self, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all exam scores or filter by subject."""
        return self.db.get_exam_scores(subject)
    
    def delete(self, exam_id: int) -> bool:
        """Delete an exam score."""
        return self.db.delete_exam_score(exam_id)
    
    def clear_all(self) -> bool:
        """Clear all exam scores."""
        return self.db.clear_all_exam_scores()
    
    def get_study_hours_correlation(self, days_before: int = 7) -> List[Dict[str, Any]]:
        """Get study hours correlated with exam scores."""
        return self.db.get_study_hours_for_exam_correlation(days_before)


class StudyHoursRepository:
    """Standardized access to study hours tracking."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def create(self, date: str, hours: float, subject: str = "", 
               notes: str = "") -> int:
        """Add study hours entry."""
        return self.db.add_study_hours(date, hours, subject, notes)
    
    def get_all(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get study hours entries."""
        return self.db.get_study_hours(date)


class LibraryRepository:
    """Standardized access to library books."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def create(self, title: str, author: str, file_path: str,
               category: str = "General", custom_category: str = "",
               description: str = "", pages: int = 0) -> int:
        """Add a book to the library."""
        return self.db.add_library_book(
            title, author, file_path, category, custom_category, description, pages
        )
    
    def get_all(self, category: Optional[str] = None, 
                search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all books with optional filtering."""
        return self.db.get_library_books(category, search)
    
    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return self.db.get_library_categories()
    
    def update_read_status(self, book_id: int, is_read: bool, 
                          current_page: Optional[int] = None) -> None:
        """Update book read status."""
        return self.db.update_book_read_status(book_id, is_read, current_page)
    
    def update_rating(self, book_id: int, rating: int) -> None:
        """Update book rating."""
        return self.db.update_book_rating(book_id, rating)
    
    def delete(self, book_id: int) -> bool:
        """Delete a book."""
        return self.db.delete_library_book(book_id)
    
    def add_bookmark(self, book_id: int, page: int, note: str = "") -> int:
        """Add a bookmark to a book."""
        return self.db.add_book_bookmark(book_id, page, note)
    
    def get_bookmarks(self, book_id: int) -> List[Dict[str, Any]]:
        """Get bookmarks for a book."""
        return self.db.get_book_bookmarks(book_id)


class StudyNoteRepository:
    """Standardized access to high-yield study notes."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def create(self, event_id: int, fact: str) -> int:
        """Add a study note for an event."""
        return self.db.add_study_note(event_id, fact)
    
    def get_by_event(self, event_id: int) -> List[str]:
        """Get study notes for an event."""
        return self.db.get_study_notes(event_id)
    
    def get_total_count(self) -> int:
        """Get total count of study notes."""
        return self.db.get_total_study_notes()


class FlashcardRepository:
    """Standardized access to flashcards and decks."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def create_deck(self, name: str) -> int:
        """Create a new flashcard deck."""
        return self.db.add_flashcard_deck(name)
    
    def get_decks(self) -> List[Dict[str, Any]]:
        """Get all decks with card counts."""
        return self.db.get_flashcard_decks()
    
    def delete_deck(self, deck_id: int) -> bool:
        """Delete a deck and all its cards."""
        return self.db.delete_flashcard_deck(deck_id)
    
    def create_card(self, deck_id: int, front: str, back: str) -> int:
        """Add a card to a deck."""
        return self.db.add_flashcard(deck_id, front, back)
    
    def get_due_cards(self, deck_id: int) -> List[Dict[str, Any]]:
        """Get cards due for review."""
        return self.db.get_due_flashcards(deck_id)
    
    def get_all_cards(self, deck_id: int) -> List[Dict[str, Any]]:
        """Get all cards in a deck."""
        return self.db.get_all_flashcards(deck_id)
    
    def delete_card(self, card_id: int) -> bool:
        """Delete a card."""
        return self.db.delete_flashcard(card_id)
    
    def update_review(self, card_id: int, interval_days: int, next_review: str,
                     ease_factor: float, reps: int) -> None:
        """Update card after review (SM-2 algorithm)."""
        return self.db.update_flashcard_review(
            card_id, interval_days, next_review, ease_factor, reps
        )
    
    def import_study_notes(self, deck_id: int) -> int:
        """Import study notes as flashcards."""
        return self.db.import_study_notes_as_flashcards(deck_id)


class ProfileRepository:
    """Standardized access to user profile."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def get(self) -> Dict[str, Any]:
        """Get user profile."""
        return self.db.get_user_profile()
    
    def save(self, profile_data: dict) -> bool:
        """Save user profile."""
        return self.db.save_user_profile(profile_data)
    
    def clear(self) -> bool:
        """Clear user profile."""
        return self.db.clear_user_profile()