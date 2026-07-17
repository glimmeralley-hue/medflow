"""Tests for MedFlow models."""

import pytest
from datetime import datetime
from medflow.models.event import AcademicEvent
from medflow.models.note import AppNote, StudyNote


class TestAcademicEvent:
    """Tests for AcademicEvent model."""
    
    def test_create_valid_event(self):
        """Test creating a valid academic event."""
        event = AcademicEvent(
            title="Anatomy Lecture",
            category="Lecture",
            date="2026-01-15",
            time_start="09:00",
            time_end="11:00"
        )
        assert event.title == "Anatomy Lecture"
        assert event.category == "Lecture"
        assert event.date == "2026-01-15"
        assert event.time_start == "09:00"
        assert event.time_end == "11:00"
        assert event.completed is False
        assert event.reminder_minutes == 15
        assert event.reminder_enabled is True
    
    def test_create_event_missing_title(self):
        """Test that missing title raises ValueError."""
        with pytest.raises(ValueError, match="Event title is required"):
            AcademicEvent(
                title="",
                category="Lecture",
                date="2026-01-15",
                time_start="09:00",
                time_end="11:00"
            )
    
    def test_create_event_missing_category(self):
        """Test that missing category raises ValueError."""
        with pytest.raises(ValueError, match="Event category is required"):
            AcademicEvent(
                title="Anatomy Lecture",
                category="",
                date="2026-01-15",
                time_start="09:00",
                time_end="11:00"
            )
    
    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = AcademicEvent(
            id=1,
            title="Anatomy Lecture",
            category="Lecture",
            date="2026-01-15",
            time_start="09:00",
            time_end="11:00"
        )
        d = event.to_dict()
        assert d['id'] == 1
        assert d['title'] == "Anatomy Lecture"
        assert d['category'] == "Lecture"
    
    def test_from_dict(self):
        """Test creating event from dictionary."""
        data = {
            'id': 2,
            'title': "Physiology Lab",
            'category': "Practical Lab",
            'subtopic': "Cardiovascular",
            'date': "2026-01-16",
            'time_start': "14:00",
            'time_end': "16:00",
            'notes': "Bring lab coat",
            'completed': True,
            'reminder_minutes': 30,
            'reminder_enabled': False
        }
        event = AcademicEvent.from_dict(data)
        assert event.id == 2
        assert event.title == "Physiology Lab"
        assert event.category == "Practical Lab"
        assert event.subtopic == "Cardiovascular"
        assert event.completed is True
        assert event.reminder_minutes == 30


class TestAppNote:
    """Tests for AppNote model."""
    
    def test_create_valid_note(self):
        """Test creating a valid app note."""
        note = AppNote(
            title="Study Notes",
            content="Important concepts to remember",
            category="Anatomy"
        )
        assert note.title == "Study Notes"
        assert note.content == "Important concepts to remember"
        assert note.category == "Anatomy"
    
    def test_create_note_missing_title(self):
        """Test that missing title raises ValueError."""
        with pytest.raises(ValueError, match="Note title is required"):
            AppNote(
                title="",
                content="Some content",
                category="General"
            )
    
    def test_create_note_missing_content(self):
        """Test that missing content raises ValueError."""
        with pytest.raises(ValueError, match="Note content is required"):
            AppNote(
                title="Title",
                content="",
                category="General"
            )
    
    def test_word_count(self):
        """Test word count property."""
        note = AppNote(
            title="Test",
            content="One two three four five",
            category="General"
        )
        assert note.word_count == 5
    
    def test_character_count(self):
        """Test character count property."""
        note = AppNote(
            title="Test",
            content="Hello World",
            category="General"
        )
        assert note.character_count == 11
    
    def test_to_dict(self):
        """Test converting note to dictionary."""
        note = AppNote(
            id=1,
            title="Study Notes",
            content="Important concepts",
            category="Anatomy"
        )
        d = note.to_dict()
        assert d['id'] == 1
        assert d['title'] == "Study Notes"
        assert 'word_count' in d


class TestStudyNote:
    """Tests for StudyNote model."""
    
    def test_create_valid_study_note(self):
        """Test creating a valid study note."""
        note = StudyNote(
            event_id=1,
            high_yield_fact="The heart has four chambers"
        )
        assert note.event_id == 1
        assert note.high_yield_fact == "The heart has four chambers"
    
    def test_create_study_note_missing_fact(self):
        """Test that missing fact raises ValueError."""
        with pytest.raises(ValueError, match="High-yield fact is required"):
            StudyNote(event_id=1, high_yield_fact="")
    
    def test_to_dict(self):
        """Test converting study note to dictionary."""
        note = StudyNote(
            id=1,
            event_id=2,
            high_yield_fact="Important fact"
        )
        d = note.to_dict()
        assert d['id'] == 1
        assert d['event_id'] == 2
        assert d['high_yield_fact'] == "Important fact"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])