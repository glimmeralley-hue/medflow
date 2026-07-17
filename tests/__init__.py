"""Test suite for MedFlow application models."""

import pytest
from datetime import date, timedelta
from medflow.models.event import AcademicEvent
from medflow.models.flashcard import Flashcard, FlashcardDeck
from medflow.models.exam import ExamScore
from medflow.models.note import Note
from medflow.models.book import Book


# ─── Academic Event Tests ─────────────────────────────────────────────────

def test_academic_event_creation():
    """Test basic event creation and validation."""
    event = AcademicEvent(
        title="Biochemistry Lecture",
        category="Lecture",
        date="2026-01-15",
        time_start="09:00",
        time_end="10:30"
    )
    assert event.title == "Biochemistry Lecture"
    assert event.category == "Lecture"
    assert event.subtopic is None

def test_academic_event_missing_title():
    """Test that missing title raises ValueError."""
    with pytest.raises(ValueError, match="Event title is required"):
        AcademicEvent(
            title="",
            category="Lecture",
            date="2026-01-15",
            time_start="09:00",
            time_end="10:30"
        )

def test_academic_event_missing_category():
    """Test that missing category raises ValueError."""
    with pytest.raises(ValueError, match="Event category is required"):
        AcademicEvent(
            title="Test Event",
            category="",
            date="2026-01-15",
            time_start="09:00",
            time_end="10:30"
        )

def test_academic_event_to_dict():
    """Test event serialization."""
    event = AcademicEvent(
        id=1,
        title="Test Event",
        category="Lab",
        subtopic="Metabolism",
        date="2026-01-15",
        time_start="09:00",
        time_end="10:30",
        completed=True
    )
    d = event.to_dict()
    assert d['id'] == 1
    assert d['title'] == "Test Event"
    assert d['completed'] is True

def test_academic_event_from_dict():
    """Test event deserialization."""
    data = {
        'id': 2,
        'title': "Exam",
        'category': "Exam",
        'date': "2026-01-20",
        'time_start': "14:00",
        'time_end': "16:00"
    }
    event = AcademicEvent.from_dict(data)
    assert event.id == 2
    assert event.title == "Exam"
    assert event.category == "Exam"


# ─── Flashcard Tests ──────────────────────────────────────────────────────

def test_flashcard_creation():
    """Test basic flashcard creation."""
    card = Flashcard(
        front="What is the Krebs cycle?",
        back="A series of reactions that generate ATP"
    )
    assert card.front == "What is the Krebs cycle?"
    assert card.back == "A series of reactions that generate ATP"
    assert card.interval_days == 1
    assert card.ease_factor == 2.5

def test_flashcard_missing_front():
    """Test that missing front raises ValueError."""
    with pytest.raises(ValueError, match="Card front is required"):
        Flashcard(front="", back="Answer")

def test_flashcard_missing_back():
    """Test that missing back raises ValueError."""
    with pytest.raises(ValueError, match="Card back is required"):
        Flashcard(front="Question", back="")

def test_flashcard_review_again():
    """Test SM-2 review with 'Again' quality (reset)."""
    card = Flashcard(front="Q", back="A")
    card.review(Flashcard.QUALITY_AGAIN)
    
    assert card.reps == 0
    assert card.interval_days == 1
    assert card.next_review == date.today().isoformat()

def test_flashcard_review_good():
    """Test SM-2 review progression with Good quality."""
    card = Flashcard(front="Q", back="A")
    
    # First review - Good (quality 4)
    card.review(Flashcard.QUALITY_GOOD)
    assert card.reps == 1
    assert card.interval_days == 1
    
    # Second review - Good
    card.review(Flashcard.QUALITY_GOOD)
    assert card.reps == 2
    assert card.interval_days == 6

def test_flashcard_review_easy():
    """Test SM-2 review with Easy quality."""
    card = Flashcard(front="Q", back="A")
    
    # First review - Easy (quality 5)
    card.review(Flashcard.QUALITY_EASY)
    assert card.reps == 1
    assert card.interval_days == 1
    
    # Second review - Good (quality 4)
    card.review(Flashcard.QUALITY_GOOD)
    assert card.reps == 2
    # Interval should multiply by ease factor
    assert card.interval_days >= 6

def test_flashcard_is_due():
    """Test due date checking."""
    card = Flashcard(front="Q", back="A")
    assert card.is_due is True  # Default is today
    
    # Set next review to future
    future_date = (date.today() + timedelta(days=5)).isoformat()
    card.next_review = future_date
    assert card.is_due is False
    
    # Set to past
    past_date = (date.today() - timedelta(days=1)).isoformat()
    card.next_review = past_date
    assert card.is_due is True


# ─── FlashcardDeck Tests ──────────────────────────────────────────────────

def test_flashcard_deck_creation():
    """Test deck creation."""
    deck = FlashcardDeck(name="Biochemistry")
    assert deck.name == "Biochemistry"

def test_flashcard_deck_missing_name():
    """Test that missing name raises ValueError."""
    with pytest.raises(ValueError, match="Deck name is required"):
        FlashcardDeck(name="")


# ─── Exam Score Tests ─────────────────────────────────────────────────────

def test_exam_score_creation():
    """Test exam score creation and properties."""
    exam = ExamScore(
        subject_name="Biochemistry",
        exam_type="Midterm",
        score=85.5,
        date="2026-01-15"
    )
    assert exam.subject == "Biochemistry"
    assert exam.exam_type == "Midterm"
    assert exam.score == 85.5
    assert exam.passed is True
    assert exam.grade == "B"

def test_exam_score_passed_boundaries():
    """Test passed property at boundaries."""
    exam_pass = ExamScore(subject_name="Test", exam_type="Quiz", score=70.0, date="2026-01-15")
    exam_fail = ExamScore(subject_name="Test", exam_type="Quiz", score=69.9, date="2026-01-15")
    
    assert exam_pass.passed is True
    assert exam_fail.passed is False

def test_exam_score_grades():
    """Test grade calculation."""
    cases = [
        (97, "A+"),
        (93, "A"),
        (90, "A-"),
        (87, "B+"),
        (83, "B"),
        (80, "B-"),
        (77, "C+"),
        (73, "C"),
        (70, "C-"),
        (67, "D+"),
        (63, "D"),
        (60, "D-"),
        (57, "F"),
    ]
    for score, expected_grade in cases:
        exam = ExamScore(subject_name="Test", exam_type="Quiz", score=float(score), date="2026-01-15")
        assert exam.grade == expected_grade, f"Expected {expected_grade} for score {score}, got {exam.grade}"


# ─── Note Tests ───────────────────────────────────────────────────────────

def test_note_creation():
    """Test note creation."""
    note = Note(
        title="Important fact",
        content="This is a high-yield point",
        category="Clinical"
    )
    assert note.title == "Important fact"
    assert note.category == "Clinical"


# ─── Book Tests ────────────────────────────────────────────────────────────

def test_book_creation():
    """Test book creation and properties."""
    book = Book(
        title="BRS Physiology",
        author="Costanzo",
        file_path="/path/to/book.pdf",
        pages=500,
        current_page=150
    )
    assert book.title == "BRS Physiology"
    assert book.reading_progress == 30.0  # 150/500 * 100


def test_book_reading_progress_zero_pages():
    """Test reading progress when pages is 0."""
    book = Book(
        title="Book",
        author="Author",
        file_path="/path/to/book.pdf",
        pages=0
    )
    assert book.reading_progress == 0.0


# ─── Validator Tests ──────────────────────────────────────────────────────

from medflow.utils.validators import (
    validate_score,
    validate_hours,
    validate_rating
)

def test_validate_score_valid():
    """Test valid score validation."""
    assert validate_score(75.5) == 75.5
    assert validate_score(100) == 100
    assert validate_score(0) == 0.0

def test_validate_score_invalid():
    """Test invalid score raises ValidationError."""
    from medflow.utils.exceptions import ValidationError
    with pytest.raises(ValidationError):
        validate_score(101)
    with pytest.raises(ValidationError):
        validate_score(-1)

def test_validate_hours_valid():
    """Test valid hours validation."""
    assert validate_hours(2.5) == 2.5
    assert validate_hours(8) == 8.0

def test_validate_hours_invalid():
    """Test invalid hours raises ValidationError."""
    from medflow.utils.exceptions import ValidationError
    with pytest.raises(ValidationError):
        validate_hours(25)  # Max is 24

def test_validate_rating_valid():
    """Test valid rating validation."""
    assert validate_rating(3) == 3
    assert validate_rating(5) == 5

def test_validate_rating_invalid():
    """Test invalid rating raises ValidationError."""
    from medflow.utils.exceptions import ValidationError
    with pytest.raises(ValidationError):
        validate_rating(0)
    with pytest.raises(ValidationError):
        validate_rating(6)


# ─── Theme Manager Tests ──────────────────────────────────────────────────

from medflow.ui.theme_manager import ThemeManager, ThemeType, get_theme_manager

def test_theme_manager_singleton():
    """Test that get_theme_manager returns singleton."""
    tm1 = get_theme_manager()
    tm2 = get_theme_manager()
    assert tm1 is tm2

def test_theme_manager_switch():
    """Test theme switching."""
    tm = ThemeManager()
    tm.set_theme(ThemeType.DARK)
    assert tm.get_theme() == ThemeType.DARK

def test_theme_manager_global_stylesheet():
    """Test that global stylesheet is generated."""
    tm = ThemeManager()
    stylesheet = tm.get_global_stylesheet()
    assert "QPushButton" in stylesheet
    assert "QMainWindow" in stylesheet
    assert len(stylesheet) > 1000  # Should be substantial


if __name__ == "__main__":
    pytest.main([__file__, "-v"])