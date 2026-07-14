"""Exam score data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExamScore:
    """Represents an exam score in the results ledger."""
    
    id: Optional[int] = None
    subject_name: str = ""
    exam_type: str = ""
    score: float = 0.0
    date: str = ""
    notes: Optional[str] = None
    created_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate exam score data after initialization."""
        if not self.subject_name:
            raise ValueError("Subject name is required")
        if not self.exam_type:
            raise ValueError("Exam type is required")
        if not (0 <= self.score <= 100):
            raise ValueError("Score must be between 0 and 100")
        if not self.date:
            raise ValueError("Exam date is required")
    
    @property
    def passed(self) -> bool:
        """Check if exam was passed (50% or higher)."""
        return self.score >= 50.0
    
    @property
    def grade(self) -> str:
        """Get letter grade based on score."""
        if self.score >= 80:
            return "A"
        elif self.score >= 70:
            return "B"
        elif self.score >= 60:
            return "C"
        elif self.score >= 50:
            return "D"
        else:
            return "F"
    
    def to_dict(self) -> dict:
        """Convert exam score to dictionary."""
        return {
            'id': self.id,
            'subject_name': self.subject_name,
            'exam_type': self.exam_type,
            'score': self.score,
            'date': self.date,
            'notes': self.notes,
            'created_at': self.created_at,
            'passed': self.passed,
            'grade': self.grade
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExamScore':
        """Create exam score from dictionary."""
        return cls(
            id=data.get('id'),
            subject_name=data.get('subject_name', ''),
            exam_type=data.get('exam_type', ''),
            score=data.get('score', 0.0),
            date=data.get('date', ''),
            notes=data.get('notes'),
            created_at=data.get('created_at')
        )
