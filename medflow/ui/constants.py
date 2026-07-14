"""Shared UI constants for MedFlow application."""

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

# Timer presets
TIMER_PRESETS = {
    "Pomodoro 25 min":  (25, 5),
    "Deep Work 50 min": (50, 10),
    "Blitz 15 min":     (15, 3),
}

# Event categories for dialogs
EVENT_CATEGORIES = [
    "Lecture", "Practical Lab", "Dissection",
    "Clinical Rotation", "Study Session", "Exam",
    "Tutorial", "Other"
]

# Exam types
EXAM_TYPES = ["CAT", "End-of-Unit", "Final Exam", "Quiz", "Other"]

# Library categories
LIBRARY_CATEGORIES = [
    "Anatomy", "Physiology", "Biochemistry",
    "Pathology", "Pharmacology", "Clinical", "General", "Custom"
]

# Note categories
NOTE_CATEGORIES = ["General", "Anatomy", "Physiology", "Pathology", "Pharmacology", "Clinical", "Research"]