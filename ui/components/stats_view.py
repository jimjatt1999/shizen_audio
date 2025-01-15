# ui/components/stats_view.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QProgressBar, QGridLayout, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

class StatsView(QWidget):
    def __init__(self, review_system):
        super().__init__()
        self.review_system = review_system
        self.setup_ui()
        
        # Update stats every 30 seconds
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(30000)  # 30 seconds

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Title
        title = QLabel("Statistics")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 16px;
        """)
        layout.addWidget(title)

        # Today's Progress
        progress_group = QGroupBox("Today's Progress")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 500;
                padding: 24px;
                margin-top: 16px;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                background: white;
            }
            QGroupBox::title {
                color: #1f2937;
                padding: 0 12px;
            }
        """)
        
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(16)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #f3f4f6;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: #2196F3;
                border-radius: 4px;
            }
        """)
        
        self.progress_label = QLabel("0/0 cards reviewed")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("color: #6b7280; font-size: 14px;")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        layout.addWidget(progress_group)

        # Main stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)
        
        # Define stat boxes
        stat_boxes = [
            ("Current Streak", "streak", "days"),
            ("Reviews Today", "today_reviews", "cards"),
            ("Study Time", "study_time", "hours"),
            ("Total Cards", "total_cards", "cards"),
            ("Success Rate", "success_rate", "%"),
            ("Average Time", "avg_time", "min/card")
        ]
        
        self.stat_labels = {}
        
        for i, (title, key, unit) in enumerate(stat_boxes):
            box = self.create_stat_box(title, "0", unit)
            stats_grid.addWidget(box, i // 3, i % 3)
            self.stat_labels[key] = box.findChild(QLabel, "value_label")
        
        layout.addLayout(stats_grid)

        # Source Distribution
        sources_group = QGroupBox("Cards by Source")
        sources_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 500;
                padding: 24px;
                margin-top: 16px;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                background: white;
            }
            QGroupBox::title {
                color: #1f2937;
                padding: 0 12px;
            }
        """)
        
        sources_layout = QVBoxLayout(sources_group)
        
        # Scrollable area for sources
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f3f4f6;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #d1d5db;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9ca3af;
            }
        """)
        
        self.sources_container = QWidget()
        self.sources_layout = QVBoxLayout(self.sources_container)
        self.sources_layout.setSpacing(12)
        scroll.setWidget(self.sources_container)
        
        sources_layout.addWidget(scroll)
        layout.addWidget(sources_group)

        # Initial stats update
        self.update_stats()

    def create_stat_box(self, title: str, value: str, unit: str) -> QWidget:
        """Create a styled stat box"""
        box = QWidget()
        box.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(box)
        layout.setSpacing(4)
        
        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2196F3;
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(f"{title} ({unit})")
        title_label.setStyleSheet("""
            color: #6b7280;
            font-size: 14px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(value_label)
        layout.addWidget(title_label)
        
        return box

    def create_source_item(self, source: str, total: int, reviewed: int) -> QWidget:
        """Create a source progress item"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Source name and counts
        label = QLabel(f"{source}")
        label.setStyleSheet("color: #374151; font-size: 14px;")
        
        counts = QLabel(f"{reviewed}/{total}")
        counts.setStyleSheet("color: #6b7280; font-size: 14px;")
        counts.setFixedWidth(80)
        counts.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, total)
        progress.setValue(reviewed)
        progress.setFixedWidth(100)
        progress.setFixedHeight(6)
        progress.setTextVisible(False)
        progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #f3f4f6;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: #2196F3;
                border-radius: 3px;
            }
        """)
        
        layout.addWidget(label)
        layout.addWidget(counts)
        layout.addWidget(progress)
        
        return widget

    def update_stats(self):
        """Update all statistics"""
        try:
            stats = self.review_system.get_detailed_stats()
            regular_stats = self.review_system.get_stats()
            
            # Update progress bar and label
            progress = stats['progress']
            self.progress_bar.setMaximum(progress['total'])
            self.progress_bar.setValue(progress['done'])
            self.progress_label.setText(f"{progress['done']}/{progress['total']} cards reviewed")
            
            # Update stat values
            self.stat_labels['streak'].setText(str(stats['streak']))
            self.stat_labels['today_reviews'].setText(str(stats['today_reviews']))
            self.stat_labels['study_time'].setText(str(stats['study_time']))
            self.stat_labels['total_cards'].setText(str(regular_stats['total']))
            
            # Calculate and update success rate
            ratings = stats['ratings_distribution']
            total_ratings = sum(ratings.values())
            if total_ratings > 0:
                success_rate = round((ratings.get('good', 0) + ratings.get('easy', 0)) / total_ratings * 100)
                self.stat_labels['success_rate'].setText(f"{success_rate}")
            else:
                self.stat_labels['success_rate'].setText("0")
            
            # Calculate average time per card
            if stats['today_reviews'] > 0:
                avg_time = round(stats['study_time'] * 60 / stats['today_reviews'])
                self.stat_labels['avg_time'].setText(str(avg_time))
            else:
                self.stat_labels['avg_time'].setText("0")
            
            # Update source distribution
            self.update_sources_distribution(stats['sources_distribution'])
            
        except Exception as e:
            print(f"Error updating stats: {e}")

    def update_sources_distribution(self, distribution: dict):
        """Update the sources distribution display"""
        # Clear existing items
        while self.sources_layout.count():
            item = self.sources_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new items
        for source, data in distribution.items():
            item = self.create_source_item(source, data['total'], data['reviewed'])
            self.sources_layout.addWidget(item)
        
        # Add stretch at the end
        self.sources_layout.addStretch()

    def showEvent(self, event):
        """Update stats when view becomes visible"""
        super().showEvent(event)
        self.update_stats()

    def hideEvent(self, event):
        """Handle view being hidden"""
        super().hideEvent(event)
        # Could add cleanup here if needed