"""Offline data exporters for MedFlow — CSV, Markdown, and iCal (RFC 5545)."""

import csv
import textwrap
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from medflow.database.models import Database


# ── CSV ──────────────────────────────────────────────────────────────────────

def export_scores_csv(db: "Database", output_path: str) -> Path:
    """
    Export all exam scores to a CSV file.

    Returns:
        Path to the created file.
    """
    scores = db.get_exam_scores()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "subject_name", "exam_type", "score", "date", "notes", "created_at"],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(scores)

    return out


# ── Markdown ─────────────────────────────────────────────────────────────────

def export_notes_markdown(db: "Database", output_path: str) -> Path:
    """
    Export all general study notes to a Markdown file, grouped by category.

    Returns:
        Path to the created file.
    """
    notes = db.get_app_notes()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Group by category
    categories: dict[str, list] = {}
    for note in notes:
        cat = note.get("category") or "General"
        categories.setdefault(cat, []).append(note)

    lines = [
        "# MedFlow Study Notes",
        f"*Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
    ]

    for cat, cat_notes in sorted(categories.items()):
        lines.append(f"## {cat}")
        lines.append("")
        for note in cat_notes:
            lines.append(f"### {note['title']}")
            updated = note.get("updated_at", "")
            if updated:
                lines.append(f"*Updated: {updated}*")
            lines.append("")
            lines.append(note.get("content", ""))
            lines.append("")
            lines.append("---")
            lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ── iCal (RFC 5545) ───────────────────────────────────────────────────────────

_ICAL_DATETIME_FMT = "%Y%m%dT%H%M%S"


def _ical_fold(line: str) -> str:
    """Fold long iCal lines at 75 octets as per RFC 5545 §3.1."""
    if len(line.encode("utf-8")) <= 75:
        return line
    parts = []
    while line:
        chunk = line[:75]
        line = line[75:]
        parts.append(chunk)
    return "\r\n ".join(parts)


def _ical_escape(text: str) -> str:
    """Escape special characters for iCal TEXT values."""
    return (
        text.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
    )


def export_events_ical(db: "Database", output_path: str) -> Path:
    """
    Export all academic events as an RFC 5545 iCalendar (.ics) file.

    Returns:
        Path to the created file.
    """
    events = db.get_events()  # all events, no date filter
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    now_stamp = datetime.utcnow().strftime(_ICAL_DATETIME_FMT) + "Z"
    uid_base = "medflow"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MedFlow//Medical Student Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for ev in events:
        # Parse date and times
        date_str = ev.get("date", "")
        start_str = ev.get("time_start", "00:00")
        end_str = ev.get("time_end", "01:00")

        try:
            dt_start = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
            dt_end = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            continue  # skip malformed records

        uid = f"{uid_base}-{ev.get('id', 0)}@medflow.local"
        summary = _ical_escape(ev.get("title", ""))
        description = _ical_escape(
            "\n".join(filter(None, [
                ev.get("subtopic") or "",
                ev.get("notes") or "",
                f"Category: {ev.get('category', '')}",
            ]))
        )

        lines += [
            "BEGIN:VEVENT",
            _ical_fold(f"UID:{uid}"),
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{dt_start.strftime(_ICAL_DATETIME_FMT)}",
            f"DTEND:{dt_end.strftime(_ICAL_DATETIME_FMT)}",
            _ical_fold(f"SUMMARY:{summary}"),
            _ical_fold(f"DESCRIPTION:{description}"),
            f"CATEGORIES:{_ical_escape(ev.get('category', 'General'))}",
            "STATUS:CONFIRMED" if not ev.get("completed") else "STATUS:COMPLETED",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")

    out.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return out


# ── Convenience wrapper ───────────────────────────────────────────────────────

def default_export_path(filename: str) -> str:
    """Return ~/Documents/MedFlow/<filename>, creating the directory if needed."""
    docs = Path.home() / "Documents" / "MedFlow"
    docs.mkdir(parents=True, exist_ok=True)
    return str(docs / filename)
