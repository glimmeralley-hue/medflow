"""Results Ledger widget — exam score tracking with correlation graphs."""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QDialog,
    QMessageBox, QFrame, QSizePolicy, QStackedWidget, QTabWidget
)
from PySide6.QtCore import Qt, QDateTime, QSize
from PySide6.QtGui import QColor, QBrush, QFont, QPainter, QPen
from PySide6.QtCharts import (
    QChart, QChartView, QLineSeries, QScatterSeries, QValueAxis,
    QBarSeries, QBarSet, QBarCategoryAxis
)
from medflow.database import Database
from .exam_detail import ExamDetailDialog
class ResultsLedger(QWidget):
    """Performance tracker for CAT and End-of-Unit exam scores"""
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.current_scores: List[Dict] = []
        self.init_ui()
        self.load_exam_scores()
    def init_ui(self):
        layout = QVBoxLayout()
        # Title
        title = QLabel("Results Ledger - Performance Tracker")
        title.setStyleSheet("""
            font-size: 28px; 
            font-weight: 600; 
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            padding-bottom: 15px;
        """)
        layout.addWidget(title)
        # Add Exam Score Section
        add_group = QGroupBox("Add Exam Score")
        add_group.setStyleSheet("""
            QGroupBox { 
                font-size: 16px; 
                font-weight: 600;
                border: 2px solid;
            border-radius: 12px;
                padding-top: 15px;
            }
        """)
        add_layout = QGridLayout()
        add_layout.setSpacing(12)
        # Subject Name
        subject_label = QLabel("Subject Name:")
        subject_label.setStyleSheet("font-weight: 500;")
        add_layout.addWidget(subject_label, 0, 0)
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("e.g., Anatomy, Physiology")
        self.subject_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid;
            padding: 10px;
                border-radius: 8px;
            }
            QLineEdit:focus {
                border: 2px solid;
            }
        """)
        add_layout.addWidget(self.subject_input, 0, 1)
        # Exam Type
        exam_label = QLabel("Exam Type:")
        exam_label.setStyleSheet("font-weight: 500;")
        add_layout.addWidget(exam_label, 1, 0)
        self.exam_type_combo = QComboBox()
        self.exam_type_combo.addItems(["CAT (Continuous Assessment Test)", "End-of-Unit Exam"])
        self.exam_type_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid;
            padding: 8px;
                border-radius: 8px;
            }
            QComboBox:focus {
                border: 2px solid;
            }
        """)
        add_layout.addWidget(self.exam_type_combo, 1, 1)
        # Score
        score_label = QLabel("Score (%):")
        score_label.setStyleSheet("font-weight: 500;")
        add_layout.addWidget(score_label, 2, 0)
        self.score_input = QDoubleSpinBox()
        self.score_input.setRange(0, 100)
        self.score_input.setValue(50)
        self.score_input.setDecimals(1)
        self.score_input.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid;
            padding: 8px;
                border-radius: 8px;
            }
        """)
        add_layout.addWidget(self.score_input, 2, 1)
        # Date
        date_label = QLabel("Date:")
        date_label.setStyleSheet("font-weight: 500;")
        add_layout.addWidget(date_label, 3, 0)
        self.exam_date = QDateEdit()
        self.exam_date.setCalendarPopup(True)
        self.exam_date.setDate(QDateTime.currentDateTime().date())
        self.exam_date.setStyleSheet("""
            QDateEdit {
                border: 2px solid;
            padding: 8px;
                border-radius: 8px;
            }
        """)
        add_layout.addWidget(self.exam_date, 3, 1)
        # Study Hours (for correlation)
        hours_label = QLabel("Study Hours (week before):")
        hours_label.setStyleSheet("font-weight: 500;")
        add_layout.addWidget(hours_label, 4, 0)
        self.study_hours_input = QDoubleSpinBox()
        self.study_hours_input.setRange(0, 168)
        self.study_hours_input.setValue(20)
        self.study_hours_input.setDecimals(1)
        self.study_hours_input.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid;
            padding: 8px;
                border-radius: 8px;
            }
        """)
        add_layout.addWidget(self.study_hours_input, 4, 1)
        # Add Button
        self.add_score_btn = QPushButton("Add Score")
        self.add_score_btn.setMinimumHeight(45)
        self.add_score_btn.clicked.connect(self.add_exam_score)
        self.add_score_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                padding: 12px 24px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                }
            QPushButton:pressed {
                }
        """)
        add_layout.addWidget(self.add_score_btn, 5, 0, 1, 2)
        add_group.setLayout(add_layout)
        add_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.addWidget(add_group)
        # Exam Scores Table
        scores_group = QGroupBox("Exam Scores")
        scores_group.setStyleSheet("""
            QGroupBox { 
                font-size: 16px; 
                font-weight: 600;
                border: 2px solid;
            border-radius: 12px;
                padding-top: 15px;
            }
        """)
        scores_layout = QVBoxLayout()
        self.scores_table = QTableWidget()
        self.scores_table.setColumnCount(6)
        self.scores_table.setHorizontalHeaderLabels(["Subject", "Exam Type", "Score (%)", "Date", "Status", ""])
        self.scores_table.setColumnWidth(5, 80)
        self.scores_table.cellDoubleClicked.connect(self.open_exam_detail_from_row)
        self.scores_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scores_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.scores_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.scores_table.setSelectionMode(QTableWidget.SingleSelection)
        self.scores_table.setSortingEnabled(True)
        self.scores_table.setMinimumHeight(260)
        self.scores_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scores_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid;
            border-radius: 10px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #FFE4E8;
            }
            QHeaderView::section {
                padding: 12px;
                font-weight: 600;
                border: none;
                border-bottom: 2px solid #FFD1DC;
            }
        """)
        scores_layout.addWidget(self.scores_table)
        # Action buttons for selected entry
        action_layout = QHBoxLayout()
        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.setMinimumHeight(40)
        self.delete_selected_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: 600;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                }
        """)
        self.delete_selected_btn.clicked.connect(self.delete_selected_exam)
        clear_all_btn = QPushButton("Clear All Data")
        clear_all_btn.setMinimumHeight(40)
        clear_all_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid;
            padding: 10px 20px;
                font-weight: 600;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                border-}
        """)
        clear_all_btn.clicked.connect(self.clear_all_exams)
        action_layout.addWidget(self.delete_selected_btn)
        action_layout.addWidget(clear_all_btn)
        action_layout.addStretch()
        scores_layout.addLayout(action_layout)
        scores_group.setLayout(scores_layout)
        scores_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Scientist Feature - Study Hours vs Exam Score Graph
        graph_group = QGroupBox("Study Hours vs Exam Score Correlation")
        graph_group.setStyleSheet("""
            QGroupBox { 
                font-size: 16px; 
                font-weight: 600;
                border: 2px solid;
            border-radius: 12px;
                padding-top: 15px;
            }
        """)
        graph_layout = QVBoxLayout()
        # ── Tab widget: Correlation scatter + Per-subject bar ─────────────
        self._chart_tabs = QTabWidget()
        self._chart_tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 6px 16px; border-radius: 8px 8px 0 0;
                font-size: 13px;
            }
            QTabBar::tab:selected { color: white; }
        """)
        # ── Chart 1: Correlation scatter ──────────────────────────────────
        self.chart = QChart()
        self.chart.setTitle("Study Hours  ×  Exam Score")
        font = QFont(); font.setBold(True); font.setPointSize(11)
        self.chart.setTitleFont(font)
        self.chart.setTitleBrush(QBrush(QColor("#FF6B9D")))
        self.chart.setBackgroundBrush(QBrush(QColor("#FFF8FA")))
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        self.study_hours_series = QScatterSeries()
        self.study_hours_series.setName("Study Hours")
        self.study_hours_series.setMarkerSize(14)
        self.study_hours_series.setColor(QColor("#FF6B9D"))
        self.study_hours_series.setBorderColor(QColor("white"))
        self.exam_score_series = QScatterSeries()
        self.exam_score_series.setName("Exam Score (%)")
        self.exam_score_series.setMarkerSize(12)
        self.exam_score_series.setColor(QColor("#B39DDB"))
        self.exam_score_series.setBorderColor(QColor("white"))
        # Trend line for scores
        self._trend_series = QLineSeries()
        self._trend_series.setName("Score trend")
        trend_pen = QPen(QColor("#FF6B9D"))
        trend_pen.setWidth(2)
        trend_pen.setStyle(Qt.DashLine)
        self._trend_series.setPen(trend_pen)
        self.chart.addSeries(self.study_hours_series)
        self.chart.addSeries(self.exam_score_series)
        self.chart.addSeries(self._trend_series)
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Exam #")
        self.axis_x.setTitleBrush(QBrush(QColor("#4A4A4A")))
        self.axis_x.setLabelsBrush(QBrush(QColor("#4A4A4A")))
        self.axis_x.setGridLineColor(QColor("#FFE4E8"))
        self.axis_x.setMinorGridLineColor(QColor("#FFF5F7"))
        self.axis_y_hours = QValueAxis()
        self.axis_y_hours.setTitleText("Study Hours")
        self.axis_y_hours.setTitleBrush(QBrush(QColor("#FF6B9D")))
        self.axis_y_hours.setLabelsBrush(QBrush(QColor("#FF6B9D")))
        self.axis_y_hours.setGridLineColor(QColor("#FFE4E8"))
        self.axis_y_hours.setMinorGridLineVisible(True)
        self.axis_y_hours.setMinorGridLineColor(QColor("#FFF5F7"))
        self.axis_y_score = QValueAxis()
        self.axis_y_score.setTitleText("Score (%)")
        self.axis_y_score.setRange(0, 100)
        self.axis_y_score.setTitleBrush(QBrush(QColor("#7E57C2")))
        self.axis_y_score.setLabelsBrush(QBrush(QColor("#7E57C2")))
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y_hours, Qt.AlignLeft)
        self.chart.addAxis(self.axis_y_score, Qt.AlignRight)
        self.study_hours_series.attachAxis(self.axis_x)
        self.study_hours_series.attachAxis(self.axis_y_hours)
        self.exam_score_series.attachAxis(self.axis_x)
        self.exam_score_series.attachAxis(self.axis_y_score)
        self._trend_series.attachAxis(self.axis_x)
        self._trend_series.attachAxis(self.axis_y_score)
        # ── Chart 2: Per-subject average bar chart ────────────────────────
        self._bar_chart = QChart()
        self._bar_chart.setTitle("Average Score by Subject")
        self._bar_chart.setTitleFont(font)
        self._bar_chart.setTitleBrush(QBrush(QColor("#FF6B9D")))
        self._bar_chart.setBackgroundBrush(QBrush(QColor("#FFF8FA")))
        self._bar_chart.setAnimationOptions(QChart.SeriesAnimations)
        self._bar_chart.legend().setVisible(False)
        self._bar_set  = QBarSet("Avg Score")
        self._bar_set.setColor(QColor("#FF6B9D"))
        self._bar_set.setBorderColor(QColor("#FF6B9D"))
        self._bar_series = QBarSeries()
        self._bar_series.append(self._bar_set)
        self._bar_chart.addSeries(self._bar_series)
        self._bar_axis_x = QBarCategoryAxis()
        self._bar_axis_y = QValueAxis()
        self._bar_axis_y.setRange(0, 100)
        self._bar_axis_y.setTitleText("Avg Score (%)")
        self._bar_axis_y.setTitleBrush(QBrush(QColor("#FF6B9D")))
        self._bar_axis_y.setLabelsBrush(QBrush(QColor("#4A4A4A")))
        self._bar_axis_y.setGridLineColor(QColor("#FFE4E8"))
        self._bar_chart.addAxis(self._bar_axis_x, Qt.AlignBottom)
        self._bar_chart.addAxis(self._bar_axis_y, Qt.AlignLeft)
        self._bar_series.attachAxis(self._bar_axis_x)
        self._bar_series.attachAxis(self._bar_axis_y)
        # ── Chart views ───────────────────────────────────────────────────
        _cv_style = "QChartView { border-radius: 10px; }"
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(320)
        self.chart_view.setStyleSheet(_cv_style)
        self._bar_chart_view = QChartView(self._bar_chart)
        self._bar_chart_view.setRenderHint(QPainter.Antialiasing)
        self._bar_chart_view.setMinimumHeight(320)
        self._bar_chart_view.setStyleSheet(_cv_style)
        # No data label (shared across both tabs)
        self.no_data_label = QLabel("Add exam scores to see graphs")
        self.no_data_label.setAlignment(Qt.AlignCenter)
        self.no_data_label.setStyleSheet("""
            font-size: 16px; padding: 50px;
        """)
        # ── Stacked widget: tabs or "no data" ─────────────────────────────
        self._chart_tabs.addTab(self.chart_view, "Correlation")
        self._chart_tabs.addTab(self._bar_chart_view, "By Subject")
        self.graph_stack = QStackedWidget()
        self.graph_stack.addWidget(self._chart_tabs)
        self.graph_stack.addWidget(self.no_data_label)
        graph_layout.addWidget(self.graph_stack)
        graph_group.setLayout(graph_layout)
        graph_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        center_splitter = QSplitter(Qt.Vertical)
        center_splitter.setChildrenCollapsible(False)
        center_splitter.addWidget(scores_group)
        center_splitter.addWidget(graph_group)
        center_splitter.setStretchFactor(0, 1)
        center_splitter.setStretchFactor(1, 1)
        main_splitter.addWidget(center_splitter)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        layout.addWidget(main_splitter, 1)
        # Refresh button
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.setMinimumHeight(45)
        refresh_btn.clicked.connect(self.load_exam_scores)
        refresh_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid;
            padding: 12px 24px;
                border-radius: 10px;
                font-weight: 600;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                }
        """)
        layout.addWidget(refresh_btn)
        self.setLayout(layout)
    def add_exam_score(self):
        """Add a new exam score"""
        subject = self.subject_input.text().strip()
        exam_type = self.exam_type_combo.currentText()
        score = self.score_input.value()
        date = self.exam_date.date().toString("yyyy-MM-dd")
        study_hours = self.study_hours_input.value()
        if subject:
            # Add exam score
            self.db.add_exam_score(subject, exam_type, score, date)
            # Add study hours (backdated to the exam date)
            study_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
            self.db.add_study_hours(study_date, study_hours, subject, "Study hours before exam")
            # Clear inputs
            self.subject_input.clear()
            self.score_input.setValue(50)
            self.study_hours_input.setValue(20)
            # Reload data
            self.load_exam_scores()
    def load_exam_scores(self):
        """Load exam scores and update visualization"""
        scores = self.db.get_exam_scores()
        self.current_scores = scores  # Store for reference
        # Update table
        self.scores_table.setRowCount(len(scores))
        for i, score in enumerate(scores):
            self.scores_table.setItem(i, 0, QTableWidgetItem(score['subject_name']))
            self.scores_table.setItem(i, 1, QTableWidgetItem(score['exam_type']))
            self.scores_table.setItem(i, 2, QTableWidgetItem(f"{score['score']:.1f}"))
            self.scores_table.setItem(i, 3, QTableWidgetItem(score['date']))
            # Status based on 50% pass mark
            status = "PASS" if score['score'] >= 50 else "FAIL"
            status_item = QTableWidgetItem(status)
            if score['score'] >= 50:
                status_item.setBackground(QBrush(QColor("#E8F5E9")))
                status_item.setForeground(QBrush(QColor("#1B5E20")))
            else:
                status_item.setBackground(QBrush(QColor("#FFEBEE")))
                status_item.setForeground(QBrush(QColor("#B71C1C")))
            self.scores_table.setItem(i, 4, status_item)
            # Action buttons container
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)
            # View details button
            view_btn = QPushButton("View")
            view_btn.setMaximumWidth(32)
            view_btn.setMinimumHeight(28)
            view_btn.setToolTip("View Details")
            view_btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid;
            border-radius: 5px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    color: white;
                }
            """)
            view_btn.clicked.connect(lambda checked, idx=i: self.view_exam_details(idx))
            action_layout.addWidget(view_btn)
            # Delete button for this row
            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumWidth(32)
            delete_btn.setMinimumHeight(28)
            delete_btn.setToolTip("Delete")
            delete_btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid;
            border-radius: 5px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    color: white;
                }
            """)
            delete_btn.clicked.connect(lambda checked, idx=i: self.delete_exam_at_row(idx))
            action_layout.addWidget(delete_btn)
            action_layout.addStretch()
            action_widget.setLayout(action_layout)
            self.scores_table.setCellWidget(i, 5, action_widget)
        # Update correlation graph
        self.update_correlation_graph()
    def delete_exam_at_row(self, row: int):
        """Delete exam at specific row"""
        if 0 <= row < len(self.current_scores):
            score = self.current_scores[row]
            exam_id = score.get('id')
            if exam_id:
                reply = QMessageBox.question(
                    self, 
                    "Confirm Delete",
                    f"Delete exam '{score['subject_name']}' from {score['date']}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    if self.db.delete_exam_score(exam_id):
                        QMessageBox.information(self, "Success", "Exam score deleted successfully!")
                        self.load_exam_scores()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to delete exam score.")
    def delete_selected_exam(self):
        """Delete currently selected exam from table"""
        selected_row = self.scores_table.currentRow()
        if selected_row >= 0:
            self.delete_exam_at_row(selected_row)
        else:
            QMessageBox.information(self, "No Selection", "Please select an exam score to delete.")
    def clear_all_exams(self):
        """Clear all exam scores with confirmation"""
        reply = QMessageBox.warning(
            self,
            "Clear All Data",
            "Are you sure you want to delete ALL exam scores?\n\nThis action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            reply2 = QMessageBox.critical(
                self,
                "Final Confirmation",
                "This will permanently delete all your exam data.\n\nAre you absolutely sure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply2 == QMessageBox.Yes:
                if self.db.clear_all_exam_scores():
                    QMessageBox.information(self, "Success", "All exam scores have been cleared.")
                    self.load_exam_scores()
                else:
                    QMessageBox.critical(self, "Error", "Failed to clear exam scores.")
    def update_correlation_graph(self):
        """Update the Study Hours vs Exam Score correlation graph"""
        correlation_data = self.db.get_study_hours_for_exam_correlation(days_before=7)
        # Clear existing data
        self.study_hours_series.clear()
        self.exam_score_series.clear()
        # Filter valid data
        valid_data = [
            d for d in correlation_data 
            if d.get('study_hours_before_exam') is not None and d.get('score') is not None
        ]
        if not valid_data:
            # Show "no data" message
            self.graph_stack.setCurrentIndex(1)
            return
        # Show chart
        self.graph_stack.setCurrentIndex(0)
        # Add data points
        for i, data in enumerate(valid_data):
            hours = float(data['study_hours_before_exam'])
            score = float(data['score'])
            self.study_hours_series.append(i + 1, hours)
            self.exam_score_series.append(i + 1, score)
        # Update axes ranges
        max_hours = max([d['study_hours_before_exam'] for d in valid_data])
        max_score = max([d['score'] for d in valid_data])
        min_score = min([d['score'] for d in valid_data])
        self.axis_y_hours.setRange(0, max(max_hours * 1.2, 10))
        self.axis_y_score.setRange(max(0, min_score - 10), min(100, max_score + 10))
        num_exams = len(valid_data)
        self.axis_x.setRange(0, num_exams + 1)
        self.axis_x.setTickCount(min(num_exams + 2, 10))
        # ── Score trend line (linear regression) ─────────────────────────
        self._trend_series.clear()
        if len(valid_data) >= 2:
            scores_vals = [float(d['score']) for d in valid_data]
            n = len(scores_vals)
            xs = list(range(1, n + 1))
            mean_x = sum(xs) / n
            mean_y = sum(scores_vals) / n
            numer = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, scores_vals))
            denom = sum((x - mean_x) ** 2 for x in xs) or 1
            slope = numer / denom
            intercept = mean_y - slope * mean_x
            self._trend_series.append(1, intercept + slope * 1)
            self._trend_series.append(n, intercept + slope * n)
        # ── Per-subject bar chart ─────────────────────────────────────────
        all_scores = self.db.get_exam_scores()
        subj_scores: dict = defaultdict(list)
        for s in all_scores:
            if s.get('score') is not None:
                subj_scores[s['subject_name']].append(float(s['score']))
        if self._bar_set.count() > 0:
            self._bar_set.remove(0, self._bar_set.count())
        subjects = sorted(subj_scores.keys())
        self._bar_axis_x.clear()
        if subjects:
            self._bar_axis_x.append(subjects)
            for subj in subjects:
                avg = sum(subj_scores[subj]) / len(subj_scores[subj])
                self._bar_set.append(avg)
            self._bar_axis_y.setRange(0, 100)
    def view_exam_details(self, row: int):
        """Open detail dialog for exam at row"""
        if 0 <= row < len(self.current_scores):
            score = self.current_scores[row]
            dialog = ExamDetailDialog(score, self)
            dialog.exec()
    def open_exam_detail_from_row(self, row: int, column: int):
        """Open exam detail when double-clicking a row"""
        if 0 <= row < len(self.current_scores):
            score = self.current_scores[row]
            dialog = ExamDetailDialog(score, self)
            dialog.exec()