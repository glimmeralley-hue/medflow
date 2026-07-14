"""Personal profile page for medical student with music player and stats."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QListWidget, QListWidgetItem,
    QGroupBox, QScrollArea, QSlider, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from medflow.database import Database
class ProfilePage(QWidget):
    """Personal profile page for medical student"""
    def __init__(self, database: Database = None):
        super().__init__()
        self.db = database
        self.profile_data = {}
        self.music_playlist = []
        self.current_track_index = 0
        self.load_profile()
        self.init_ui()
        if self.profile_data.get('music_folder'):
            self._load_music_folder(self.profile_data['music_folder'])
        self.populate_profile_fields()
        self.load_dashboard_data()
    def load_profile(self):
        """Load profile from database (primary) or JSON file (fallback)"""
        defaults = {
            'name': '', 'school': '', 'year': '', 'graduation': '',
            'ambitions': '', 'specialties': '', 'hobbies': '',
            'study_plan': '', 'motivation': '', 'profile_picture': '',
            'music_file': '', 'music_folder': ''
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
                    'music_file': db_profile.get('music_file_path') or '',
                    'music_folder': db_profile.get('music_folder_path') or ''
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
        profile_path = Path.home() / ".medflow_profile.json"
        try:
            with open(profile_path, 'w') as f:
                json.dump(self.profile_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save JSON backup: {e}")
        if self.db:
            if self.db.save_user_profile(self.profile_data):
                QMessageBox.information(self, "Saved", "Your profile has been saved to database!")
                self.load_profile()
                self.populate_profile_fields()
                self.update_quick_stats()
            else:
                QMessageBox.warning(self, "Warning", "Profile saved to file but database save failed.")
        else:
            QMessageBox.information(self, "Saved", "Your profile has been saved!")
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
                border: 2px solid;
            border-radius: 50px;
                }
        """)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.update_profile_picture()
        header.addWidget(self.avatar_label)
        # Profile picture button
        self.change_pic_btn = QPushButton("Change Photo")
        self.change_pic_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid;
            padding: 8px 15px;
                border-radius: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
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
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        title_layout.addWidget(title)
        subtitle = QLabel("Your personal profile and aspirations")
        subtitle.setStyleSheet("""
            font-size: 14px;
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
                border: 2px solid;
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
        self._media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        music_label = QLabel("Study Music")
        music_label.setStyleSheet("font-size: 12px; font-weight: 700; background: transparent; border: none;")
        music_layout.addWidget(music_label)
        self.music_path_label = QLabel(self._get_music_label_text())
        self.music_path_label.setStyleSheet("font-size: 10px; background: transparent; border: none;")
        self.music_path_label.setWordWrap(True)
        music_layout.addWidget(self.music_path_label)
        transport = QHBoxLayout()
        transport.setSpacing(6)
        self.select_music_folder_btn = QPushButton("Open Folder")
        self.select_music_folder_btn.setFixedSize(30, 30)
        self.select_music_folder_btn.setToolTip("Choose a music folder")
        self.select_music_folder_btn.setStyleSheet(self._music_btn_css())
        self.select_music_folder_btn.clicked.connect(self.select_music_folder)
        transport.addWidget(self.select_music_folder_btn)
        self.select_music_btn = QPushButton("Open File")
        self.select_music_btn.setFixedSize(30, 30)
        self.select_music_btn.setToolTip("Choose a music file")
        self.select_music_btn.setStyleSheet(self._music_btn_css())
        self.select_music_btn.clicked.connect(self.select_music_file)
        transport.addWidget(self.select_music_btn)
        self.play_music_btn = QPushButton("Play")
        self.play_music_btn.setFixedSize(34, 34)
        self.play_music_btn.setToolTip("Play / Pause")
        self.play_music_btn.setStyleSheet(self._music_btn_css(primary=True))
        self.play_music_btn.setEnabled(bool(self.profile_data.get('music_file') or self.music_playlist))
        self.play_music_btn.clicked.connect(self.toggle_music)
        transport.addWidget(self.play_music_btn)
        stop_btn = QPushButton("Stop")
        stop_btn.setFixedSize(30, 30)
        stop_btn.setToolTip("Stop")
        stop_btn.setStyleSheet(self._music_btn_css())
        stop_btn.clicked.connect(self.stop_music)
        transport.addWidget(stop_btn)
        transport.addStretch()
        vol_icon = QLabel("Volume")
        vol_icon.setStyleSheet("font-size: 11px; background: transparent; border: none;")
        transport.addWidget(vol_icon)
        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(55)
        self._vol_slider.setFixedHeight(16)
        self._vol_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px; border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 12px; height: 12px;
                margin: -4px 0; border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                border-radius: 2px;
            }
        """)
        self._vol_slider.valueChanged.connect(lambda v: self._audio_output.setVolume(v / 100.0))
        transport.addWidget(self._vol_slider)
        music_layout.addLayout(transport)
        header.addWidget(music_widget)
        layout.addLayout(header)
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        # Basic Info Section
        basic_group = self.create_section("Basic Information")
        basic_layout = QGridLayout()
        basic_layout.setSpacing(15)
        basic_layout.addWidget(self.create_label("Full Name:"), 0, 0)
        self.name_input = self.create_line_edit("Your name...")
        self.name_input.setText(self.profile_data.get('name', ''))
        basic_layout.addWidget(self.name_input, 0, 1)
        basic_layout.addWidget(self.create_label("Medical School:"), 1, 0)
        self.school_input = self.create_line_edit("e.g., Harvard Medical School")
        self.school_input.setText(self.profile_data.get('school', ''))
        basic_layout.addWidget(self.school_input, 1, 1)
        basic_layout.addWidget(self.create_label("Year of Study:"), 2, 0)
        self.year_combo = QComboBox()
        self.year_combo.addItems(["Year 1 (Pre-clinical)", "Year 2 (Pre-clinical)", 
                                 "Year 3 (Clinical)", "Year 4 (Clinical)", 
                                 "Year 5 (Final/Internship)", "Resident", "Fellow", "Attending"])
        self.year_combo.setCurrentText(self.profile_data.get('year', 'Year 1 (Pre-clinical)'))
        self.year_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid;
            padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }
            QComboBox:focus { border: 2px solid;
            }
        """)
        basic_layout.addWidget(self.year_combo, 2, 1)
        basic_layout.addWidget(self.create_label("Expected Graduation:"), 3, 0)
        self.graduation_input = self.create_line_edit("e.g., 2028")
        self.graduation_input.setText(self.profile_data.get('graduation', ''))
        basic_layout.addWidget(self.graduation_input, 3, 1)
        basic_group.layout().addLayout(basic_layout)
        content_layout.addWidget(basic_group)
        # Career Goals Section
        career_group = self.create_section("Career Goals & Ambitions")
        self.ambitions_input = self.create_text_edit("What are your ambitions? (e.g., Become a pediatric surgeon, Research oncology...)")
        self.ambitions_input.setText(self.profile_data.get('ambitions', ''))
        career_group.layout().addWidget(self.ambitions_input)
        content_layout.addWidget(career_group)
        # Special Interests
        interests_group = self.create_section("Special Interests & Hobbies")
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
        study_group = self.create_section("Study Plan & Strategies")
        self.study_plan_input = self.create_text_edit("Describe your study strategies, preferred resources, daily routines...")
        self.study_plan_input.setText(self.profile_data.get('study_plan', ''))
        study_group.layout().addWidget(self.study_plan_input)
        content_layout.addWidget(study_group)
        # Motivation Section
        motivation_group = self.create_section("Motivation & Mantra")
        self.motivation_input = self.create_text_edit("What keeps you going? Your favorite quotes or personal mantra...")
        self.motivation_input.setMinimumHeight(80)
        self.motivation_input.setText(self.profile_data.get('motivation', ''))
        motivation_group.layout().addWidget(self.motivation_input)
        content_layout.addWidget(motivation_group)
        # Upcoming Events Section
        events_group = self.create_section("Upcoming Events")
        self.events_list = QListWidget()
        self.events_list.setMinimumHeight(120)
        self.events_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.events_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 2px solid;
            border-radius: 12px;
                padding: 10px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 12px;
                margin: 4px 0px;
                border-radius: 8px;
                border-left: 4px solid #FF6B9D;
            }
            QListWidget::item:hover { }
        """)
        events_group.layout().addWidget(self.events_list)
        content_layout.addWidget(events_group)
        # Congratulations Section
        self.congrats_group = self.create_section("Recent Achievements")
        self.congrats_layout = QVBoxLayout()
        self.congrats_layout.setSpacing(10)
        self.congrats_label = QLabel("No recent exam results. Add your scores in the Results Ledger!")
        self.congrats_label.setStyleSheet("font-size: 14px; font-style: italic; padding: 20px;")
        self.congrats_label.setAlignment(Qt.AlignCenter)
        self.congrats_layout.addWidget(self.congrats_label)
        self.congrats_group.layout().addLayout(self.congrats_layout)
        content_layout.addWidget(self.congrats_group)
        # Stats
        self.stats_group = self.create_section("Quick Stats")
        stats_layout = QHBoxLayout()
        self.stats_labels = {}
        stats = [
            ("notes_created", "Notes Created", "0"),
            ("events_planned", "Events Planned", "0"),
            ("exams_logged", "Exams Logged", "0"),
            ("study_hours", "Study Hours", "0")
        ]
        for key, label, value in stats:
            stat_box = QGroupBox()
            stat_box.setStyleSheet("""
                QGroupBox {
                    border: 2px solid;
            border-radius: 12px;
                    padding: 15px;
                }
            """)
            stat_layout = QVBoxLayout()
            val_label = QLabel(value)
            val_label.setObjectName(key)
            self.stats_labels[key] = val_label
            val_label.setStyleSheet("font-size: 28px; font-weight: 700; ")
            val_label.setAlignment(Qt.AlignCenter)
            txt_label = QLabel(label)
            txt_label.setStyleSheet("font-size: 12px; ")
            txt_label.setAlignment(Qt.AlignCenter)
            stat_layout.addWidget(val_label)
            stat_layout.addWidget(txt_label)
            stat_box.setLayout(stat_layout)
            stats_layout.addWidget(stat_box)
        self.stats_group.layout().addLayout(stats_layout)
        content_layout.addWidget(self.stats_group)
        self.update_quick_stats()
        # Save button
        save_btn = QPushButton("Save Profile")
        save_btn.setMinimumHeight(55)
        save_btn.clicked.connect(self.save_profile_data)
        save_btn.setStyleSheet("""
            QPushButton {
                color: white; border: none;
                padding: 18px 40px; font-weight: 700; border-radius: 15px;
                font-size: 18px;
            }
            QPushButton:hover { }
        """)
        clear_btn = QPushButton("Clear Profile")
        clear_btn.setMinimumHeight(55)
        clear_btn.clicked.connect(self.clear_profile_data)
        clear_btn.setStyleSheet("""
            QPushButton {
                color: white; border: none;
                padding: 18px 40px; font-weight: 700; border-radius: 15px;
                font-size: 18px;
            }
            QPushButton:hover { }
        """)
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
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 18px; font-weight: 600; border: 2px solid;
            border-radius: 15px; padding-top: 20px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 20px; padding: 0 15px;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        group.setLayout(layout)
        return group
    def create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size: 14px; font-weight: 500;")
        return label
    def create_line_edit(self, placeholder: str) -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(40)
        edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid;
            padding: 10px; border-radius: 10px; font-size: 14px;
                }
            QLineEdit:focus { border: 2px solid;
            }
        """)
        return edit
    def create_text_edit(self, placeholder: str) -> QTextEdit:
        edit = QTextEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(120)
        edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid;
            padding: 15px; border-radius: 10px; font-size: 14px;
                }
            QTextEdit:focus { border: 2px solid;
            }
        """)
        return edit
    def populate_profile_fields(self):
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
        self.music_path_label.setText(self._get_music_label_text())
        self.play_music_btn.setEnabled(bool(self.profile_data.get('music_file') or self.music_playlist))
        self.update_profile_picture()
    def update_quick_stats(self):
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
        if not self.db:
            return
        self.load_upcoming_events()
        self.load_passed_exams()
    def load_upcoming_events(self):
        upcoming_events = []
        for i in range(7):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            events = self.db.get_events(date)
            for event in events:
                upcoming_events.append({
                    'date': date, 'title': event['title'],
                    'time': event['time_start'], 'category': event['category']
                })
        self.events_list.clear()
        if upcoming_events:
            for event in upcoming_events[:5]:
                date_obj = datetime.strptime(event['date'], "%Y-%m-%d")
                day_name = date_obj.strftime("%a")
                date_str = date_obj.strftime("%b %d")
                text = f"{day_name}, {date_str} at {event['time']}\n   {event['title']}"
                self.events_list.addItem(text)
        else:
            item = QListWidgetItem("No upcoming events in the next 7 days\n   Add events in the Planner tab!")
            item.setForeground(QColor("#5A4A5A"))
            self.events_list.addItem(item)
    def load_passed_exams(self):
        scores = self.db.get_exam_scores()
        passed_exams = [s for s in scores if s['score'] >= 50]
        while self.congrats_layout.count() > 1:
            item = self.congrats_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        if passed_exams:
            self.congrats_label.setVisible(False)
            for exam in passed_exams[:3]:
                score = exam['score']
                card = QWidget()
                card.setStyleSheet("""
                    QWidget {
                        border: 2px solid;
            border-radius: 12px; padding: 15px;
                    }
                """)
                card_layout = QHBoxLayout()
                card_layout.setContentsMargins(15, 15, 15, 15)
                trophy = QLabel("★")
                trophy.setStyleSheet("font-size: 32px;")
                card_layout.addWidget(trophy)
                message = QLabel()
                if score >= 80:
                    message_text = f"Amazing! You aced the {exam['subject_name']} {exam['exam_type']}!\n   Score: {score:.1f}% - Outstanding work!"
                elif score >= 70:
                    message_text = f"Great job! You passed {exam['subject_name']} {exam['exam_type']}!\n   Score: {score:.1f}% - Well done!"
                else:
                    message_text = f"Congrats! You passed {exam['subject_name']} {exam['exam_type']}!\n   Score: {score:.1f}% - Keep it up!"
                message.setText(message_text)
                message.setStyleSheet("font-size: 14px; font-weight: 500;")
                card_layout.addWidget(message, stretch=1)
                card.setLayout(card_layout)
                self.congrats_layout.addWidget(card)
        else:
            self.congrats_label.setVisible(True)
    def save_profile_data(self):
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
        reply = QMessageBox.question(self, "Clear Profile", 
                                   "Are you sure you want to clear all profile data? This cannot be undone.",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.name_input.clear()
            self.school_input.clear()
            self.year_combo.setCurrentIndex(0)
            self.graduation_input.clear()
            self.ambitions_input.clear()
            self.specialties_input.clear()
            self.hobbies_input.clear()
            self.study_plan_input.clear()
            self.motivation_input.clear()
            self.profile_data = {}
            if self.db:
                self.db.clear_user_profile()
            profile_path = Path.home() / ".medflow_profile.json"
            if profile_path.exists():
                profile_path.unlink()
            self.update_profile_picture()
            self.update_quick_stats()
            QMessageBox.information(self, "Cleared", "Profile data has been cleared.")
    def update_profile_picture(self):
        if self.profile_data.get('profile_picture') and Path(self.profile_data['profile_picture']).exists():
            pixmap = QPixmap(self.profile_data['profile_picture'])
            scaled = pixmap.scaled(90, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.avatar_label.setPixmap(scaled)
        else:
            self.avatar_label.setText("👤")
            self.avatar_label.setStyleSheet("""
                QLabel {
                    border: 2px solid;
            border-radius: 50px;
                    font-size: 40px;
                }
            """)
    def select_profile_picture(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Picture", str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.bmp);All Files (*)"
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
                    color: white;
                    border: none; border-radius: 8px; font-size: 14px; font-weight: 700;
                }
                QPushButton:hover { }
                QPushButton:disabled { color: white; }
            """
        return """
            QPushButton {
                border: 2px solid;
            border-radius: 7px; font-size: 13px;
            }
            QPushButton:hover { }
        """
    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_music_btn.setText("Pause")
            self.play_music_btn.setToolTip("Pause")
        else:
            self.play_music_btn.setText("Play")
            self.play_music_btn.setToolTip("Play")
    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._play_next_track()
    def _get_music_label_text(self) -> str:
        folder = self.profile_data.get('music_folder', '')
        if folder:
            track_count = len(self.music_playlist)
            if track_count:
                current_name = Path(self.music_playlist[self.current_track_index]).name
                return f"{Path(folder).name} • {self.current_track_index + 1}/{track_count} {current_name}"
            return f"{Path(folder).name} • 0 tracks found"
        if self.profile_data.get('music_file'):
            return Path(self.profile_data['music_file']).name
        return "No music selected"
    def _set_current_track(self, file_path: str):
        if not file_path:
            return
        self.profile_data['music_file'] = file_path
        self.music_path_label.setText(self._get_music_label_text())
        self._media_player.setSource(QUrl.fromLocalFile(file_path))
    def _load_music_folder(self, folder_path: str):
        self.music_playlist = []
        self.current_track_index = 0
        if not folder_path:
            return
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            return
        audio_patterns = ['*.mp3', '*.wav', '*.ogg', '*.flac', '*.m4a']
        tracks = []
        for pattern in audio_patterns:
            tracks.extend(folder.rglob(pattern))
        tracks = [p for p in tracks if p.is_file()]
        tracks = sorted(tracks, key=lambda p: p.name.lower())
        self.music_playlist = [str(p) for p in tracks]
        if self.music_playlist:
            self._set_current_track(self.music_playlist[0])
    def _play_next_track(self):
        if not self.music_playlist:
            return
        self.current_track_index = (self.current_track_index + 1) % len(self.music_playlist)
        self._set_current_track(self.music_playlist[self.current_track_index])
        self._media_player.play()
    def select_music_file(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Study Music", str(Path.home()),
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a);All Files (*)"
        )
        if file_path:
            self.profile_data['music_folder'] = ''
            self.music_playlist = []
            self.current_track_index = 0
            self.profile_data['music_file'] = file_path
            self._set_current_track(file_path)
            self.play_music_btn.setEnabled(True)
            self.save_profile()
    def select_music_folder(self):
        from PySide6.QtWidgets import QFileDialog
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Study Music Folder", str(Path.home())
        )
        if folder_path:
            self.profile_data['music_folder'] = folder_path
            self._load_music_folder(folder_path)
            self.play_music_btn.setEnabled(bool(self.music_playlist))
            self.music_path_label.setText(self._get_music_label_text())
            if not self.music_playlist:
                QMessageBox.information(self, "No audio found", "No supported audio tracks were found in that folder.")
            self.save_profile()
    def toggle_music(self):
        if not self.profile_data.get('music_file') and not self.music_playlist:
            return
        if self._media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._media_player.pause()
        else:
            src = self._media_player.source()
            if not src.isValid() or src.isEmpty():
                if self.music_playlist:
                    self._set_current_track(self.music_playlist[self.current_track_index])
                else:
                    self._set_current_track(self.profile_data['music_file'])
            self._media_player.play()
    def stop_music(self):
        self._media_player.stop()