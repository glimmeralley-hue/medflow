"""Flashcard and FlashcardDeck data models with SM-2 spaced repetition scheduling."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class FlashcardDeck:
    """A named collection of flashcards."""
    id: Optional[int] = None
    name: str = ""
    created_at: Optional[str] = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("Deck name is required")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "created_at": self.created_at}

    @classmethod
    def from_dict(cls, data: dict) -> "FlashcardDeck":
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            created_at=data.get("created_at"),
        )


@dataclass
class Flashcard:
    """
    A single flashcard with SM-2 spaced repetition state.

    SM-2 algorithm (simplified):
      - ease_factor (EF): starts at 2.5, adjusted by quality score (0-5)
      - interval_days: grows multiplicatively after each successful recall
      - next_review: date of the next due review
      - reps: count of consecutive successful reviews
    """
    id: Optional[int] = None
    deck_id: Optional[int] = None
    front: str = ""
    back: str = ""
    interval_days: int = 1
    next_review: str = field(default_factory=lambda: date.today().isoformat())
    ease_factor: float = 2.5
    reps: int = 0
    created_at: Optional[str] = None

    # Quality constants for UI buttons
    QUALITY_AGAIN = 0   # Completely forgot — reset
    QUALITY_HARD  = 2   # Remembered with difficulty
    QUALITY_GOOD  = 4   # Remembered correctly
    QUALITY_EASY  = 5   # Remembered perfectly

    def __post_init__(self):
        if not self.front:
            raise ValueError("Card front is required")
        if not self.back:
            raise ValueError("Card back is required")

    @property
    def is_due(self) -> bool:
        """True if the card is due for review today or earlier."""
        try:
            return date.fromisoformat(self.next_review) <= date.today()
        except ValueError:
            return True

    def review(self, quality: int) -> None:
        """
        Apply SM-2 scheduling after a review.

        Args:
            quality: 0-5 score (use QUALITY_* constants).
        """
        quality = max(0, min(5, quality))

        if quality < 3:
            # Failed review — reset interval
            self.reps = 0
            self.interval_days = 1
        else:
            if self.reps == 0:
                self.interval_days = 1
            elif self.reps == 1:
                self.interval_days = 6
            else:
                self.interval_days = max(1, round(self.interval_days * self.ease_factor))
            self.reps += 1

        # Update ease factor (clamped to a minimum of 1.3)
        self.ease_factor = max(
            1.3,
            self.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02),
        )

        next_date = date.today() + timedelta(days=self.interval_days)
        self.next_review = next_date.isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "deck_id": self.deck_id,
            "front": self.front,
            "back": self.back,
            "interval_days": self.interval_days,
            "next_review": self.next_review,
            "ease_factor": self.ease_factor,
            "reps": self.reps,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Flashcard":
        return cls(
            id=data.get("id"),
            deck_id=data.get("deck_id"),
            front=data.get("front", ""),
            back=data.get("back", ""),
            interval_days=data.get("interval_days", 1),
            next_review=data.get("next_review", date.today().isoformat()),
            ease_factor=float(data.get("ease_factor", 2.5)),
            reps=data.get("reps", 0),
            created_at=data.get("created_at"),
        )
