"""Notes Section widget — clinical study journal with search and export."""
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from medflow.database import Database
from .constants import NOTE_CATEGORIES
from .note_reader import NoteReaderDialog
from .theme_manager import get_theme_manager, ThemeColors, IOS_FONT_STACK


class NotesSection(QWidget):
    """Notes workspace with clinical study journal."""
    
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self._editing_note_id: Optional[int] = None  # None = creating new note
        self.theme_manager = get_theme_manager()
        self._colors = self.theme_manager.get_colors(self.theme_manager.get_theme())
        self.init_ui()
        self.load_notes()
        
        # Connect to theme changes
        self.theme_manager.theme_changed_connect(self._on_theme_changed)
    
    def _on_theme_changed(self, theme_type):
        """Update styles when theme changes."""
        self._colors = self.theme_manager.get_colors(theme_type)
        self._apply_theme_styles()
    
    def _apply_theme_styles(self):
        """Apply theme-aware styles to all widgets."""
        c = self._colors
        
        # Update button styles
        self.save_note_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['PRIMARY']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                background-color: {c['PRIMARY_LIGHT']};
            }}
        """)
        
        self._new_note_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['SECONDARY_LIGHT']};
                color: {c['TEXT_SECONDARY']};
                border: 2px solid {c['SECONDARY']};
                padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                background-color: {c['SECONDARY']};
            }}
        """)
        
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['INFO']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                background-color: {c['PRIMARY']};
            }}
        """)
        
        self.read_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['SUCCESS']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                background-color: {c['PRIMARY']};
            }}
        """)
        
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['ERROR']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                background-color: {c['PRIMARY_DARK']};
            }}
        """)
        
        # Update input styles
        self.note_title.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['INPUT_BG']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 12px;
                border-radius: 10px;
                font-size: 15px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QLineEdit:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
        """)
        
        self.note_category.setStyleSheet(f"""
            QComboBox {{
                background-color: {c['INPUT_BG']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 8px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QComboBox:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
        """)
        
        self.note_content.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['INPUT_BG']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 15px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QTextEdit:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
        """)
        
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['INPUT_BG']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QLineEdit:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
        """)
        
        # Update group box styles
        self.create_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: 600;
                border: 2px solid {c['BORDER']};
            border-radius: 12px;
                padding-top: 18px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }}
        """)
        
        self.notes_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: 600;
                border: 2px solid {c['BORDER']};
            border-radius: 12px;
                padding-top: 18px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }}
        """)
        
        # Update notes list style
        self.update_notes_list_style()
        
        # Update labels
        self.category_label.setStyleSheet(f"font-weight: 500; font-family: {IOS_FONT_STACK}; color: {c['TEXT_PRIMARY']};")
        self.word_count_label.setStyleSheet(f"font-size: 12px; font-style: italic; font-family: {IOS_FONT_STACK}; color: {c['TEXT_SECONDARY']};")
        self.reminders_icon.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {c['PRIMARY']}; font-family: {IOS_FONT_STACK};")
    
    def init_ui(self):
        c = self._colors
        
        # Main layout is QHBoxLayout directly in NotesSection
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Create/Edit Note group
        self.create_group = QGroupBox("Create / Edit Note")
        self.create_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: 600;
                border: 2px solid {c['BORDER']};
            border-radius: 12px;
                padding-top: 18px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }}
        """)
        create_layout = QVBoxLayout()
        create_layout.setSpacing(15)
        
        self.note_title = QLineEdit()
        self.note_title.setPlaceholderText("Note title...")
        self.note_title.setMinimumHeight(45)
        self.note_title.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['INPUT_BG']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 12px;
                border-radius: 10px;
                font-size: 15px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QLineEdit:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
        """)
        create_layout.addWidget(self.note_title)
        
        category_layout = QHBoxLayout()
        self.category_label = QLabel("Category:")
        self.category_label.setStyleSheet(f"font-weight: 500; font-family: {IOS_FONT_STACK}; color: {c['TEXT_PRIMARY']};")
        self.note_category = QComboBox()
        self.note_category.addItems(NOTE_CATEGORIES)
        self.note_category.setMinimumHeight(40)
        self.note_category.setStyleSheet(f"""
            QComboBox {{
                background-color: {c['INPUT_BG']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 8px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QComboBox:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
        """)
        category_layout.addWidget(self.category_label)
        category_layout.addWidget(self.note_category)
        category_layout.addStretch()
        create_layout.addLayout(category_layout)
        
        self.note_content = QTextEdit()
        self.note_content.setPlaceholderText("Write your notes here...")
        self.note_content.setMinimumHeight(180)
        self.note_content.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['INPUT_BG']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 15px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QTextEdit:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
        """)
        self.note_content.textChanged.connect(self.update_word_count)
        create_layout.addWidget(self.note_content)
        
        self.word_count_label = QLabel("0 words | 0 characters")
        self.word_count_label.setStyleSheet(f"font-size: 12px; font-style: italic; font-family: {IOS_FONT_STACK}; color: {c['TEXT_SECONDARY']};")
        self.word_count_label.setAlignment(Qt.AlignRight)
        create_layout.addWidget(self.word_count_label)
        
        # Buttons at bottom
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.save_note_btn = QPushButton("Save Note")
        self.save_note_btn.setMinimumHeight(50)
        self.save_note_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['PRIMARY']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                background-color: {c['PRIMARY_LIGHT']};
            }}
        """)
        self.save_note_btn.setToolTip("Save the current note (Ctrl+S)")
        self.save_note_btn.setShortcut("Ctrl+S")
        self.save_note_btn.clicked.connect(self.add_note)
        buttons_layout.addWidget(self.save_note_btn)
        
        self._new_note_btn = QPushButton("New Note")
        self._new_note_btn.setMinimumHeight(50)
        self._new_note_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['SECONDARY_LIGHT']};
                color: {c['TEXT_SECONDARY']};
                border: 2px solid {c['SECONDARY']};
                padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                background-color: {c['SECONDARY']};
            }}
        """)
        self._new_note_btn.setToolTip("Clear the editor and start a brand new note")
        self._new_note_btn.clicked.connect(self.clear_editor)
        buttons_layout.addWidget(self._new_note_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setMinimumHeight(50)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['INFO']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                background-color: {c['PRIMARY']};
            }}
        """)
        self.export_btn.setToolTip("Export all notes to a text file")
        self.export_btn.clicked.connect(self.export_notes)
        buttons_layout.addWidget(self.export_btn)
        
        create_layout.addLayout(buttons_layout)
        self.create_group.setLayout(create_layout)
        layout.addWidget(self.create_group, 2)
        
        # Notes list group
        self.notes_group = QGroupBox("My Notes")
        self.notes_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: 600;
                border: 2px solid {c['BORDER']};
            border-radius: 12px;
                padding-top: 18px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }}
        """)
        
        notes_layout = QVBoxLayout()
        notes_layout.setSpacing(15)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search notes...")
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['INPUT_BG']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
                color: {c['TEXT_PRIMARY']};
            }}
            QLineEdit:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
        """)
        self.search_input.textChanged.connect(self.filter_notes)
        notes_layout.addWidget(self.search_input)
        
        self.notes_list = QListWidget()
        self.notes_list.setMinimumHeight(420)
        self.update_notes_list_style()
        
        self.notes_list.itemClicked.connect(self.load_note)
        self.notes_list.itemDoubleClicked.connect(self.open_note_reader)
        notes_layout.addWidget(self.notes_list)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        
        self.read_btn = QPushButton("Read Note")
        self.read_btn.setMinimumHeight(45)
        self.read_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['SUCCESS']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                background-color: {c['PRIMARY']};
            }}
        """)
        self.read_btn.clicked.connect(self.open_note_reader)
        action_layout.addWidget(self.read_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setMinimumHeight(45)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['ERROR']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                background-color: {c['PRIMARY_DARK']};
            }}
        """)
        self.delete_btn.clicked.connect(self.delete_note)
        action_layout.addWidget(self.delete_btn)
        action_layout.addStretch()
        
        notes_layout.addLayout(action_layout)
        self.notes_group.setLayout(notes_layout)
        layout.addWidget(self.notes_group, 1)
    
    def update_notes_list_style(self):
        """Update the notes list stylesheet based on current theme."""
        c = self._colors
        self.notes_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {c['INPUT_BG']};
                border: 2px solid {c['BORDER']};
            border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QListWidget::item {{
                padding: 14px;
                margin: 8px 0px;
                border-radius: 10px;
                border: 2px solid {c['BORDER']};
                color: {c['TEXT_PRIMARY']};
            }}
            QListWidget::item:selected {{
                border: 2px solid {c['PRIMARY']};
                background-color: {c['SECONDARY']};
            }}
            QListWidget::item:hover {{
                background-color: {c['HOVER']};
            }}
        """)
        # Update header widgets if they exist
        if hasattr(self, 'reminders_icon'):
            self.reminders_icon.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {c['PRIMARY']}; font-family: {IOS_FONT_STACK};")
    
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
        self.save_note_btn.setText("Save Note")
        self.notes_list.clearSelection()
    
    def refresh_notes_list(self):
        notes = self.db.get_app_notes()
        self.notes_list.clear()
        for note in notes:
            ts = note.get('updated_at') or note.get('created_at', '')
            item_text = f"{note['title']}\n   {note['category']} · {ts[:16]}"
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
            self.save_note_btn.setText("Update Note")
    
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
            item_text = f"{note['title']}\n   {note['category']} · {ts[:16]}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, note['id'])
            self.notes_list.addItem(item)
    
    def update_word_count(self):
        text = self.note_content.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.setText(f"{words} words | {chars} characters")
    
    def export_notes(self):
        notes = self.db.get_app_notes()
        if not notes:
            QMessageBox.information(self, "No Notes", "No notes to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Notes",
            f"medflow_notes_{datetime.now().strftime('%Y%m%d')}.txt",
            "Text Files (*.txt);All Files (*)"
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