# ui/main_window.py

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                           QLabel, QStackedWidget, QListWidget, QListWidgetItem, QScrollArea, QSplitter,
                           QMessageBox, QInputDialog, QDialog, QProgressBar, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QColor, QPixmap
from .components.audio_card import AudioCard
from .components.settings import Settings
from .components.stats_view import StatsView
from audio_processors.media_processor import MediaProcessor
import requests
from pathlib import Path
from .components.manage_view import ManageSourcesView
from .components.upload_view import UploadView



class ProcessingThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, media_processor, url, media_type='youtube'):
        super().__init__()
        self.media_processor = media_processor
        self.url = url
        self.media_type = media_type
        self.is_running = True

    def run(self):
        try:
            if not self.is_running:
                return

            self.progress.emit("Downloading...")
            if self.media_type == 'youtube':
                result = self.media_processor.process_youtube(self.url)
            else:  # podcast
                result = self.media_processor.process_podcast_episode(
                    self.url['url'], self.url['title'])
            
            if not self.is_running:
                return

            self.progress.emit("Transcribing audio...")
            segments = self.media_processor.whisper.transcribe(result['audio_path'])
            
            if not segments:
                raise Exception("No segments were generated from the audio")
                
            self.finished.emit({
                'source': result,
                'segments': segments
            })
        except Exception as e:
            if self.is_running:
                print(f"Processing error: {str(e)}")
                self.error.emit(str(e))

    def stop(self):
        """Stop the thread cleanly"""
        self.is_running = False

    def __del__(self):
        """Ensure thread is stopped on deletion"""
        self.stop()
        self.wait()


class MainWindow(QMainWindow):
    VIEWS = ["Review", "Upload", "YouTube", "Podcasts", "Stats", "Manage", "Settings"]

    @classmethod
    def create(cls, review_system):
        window = cls()
        window.initialize(review_system)
        return window

    def __init__(self):
        super().__init__()
        self.content_stack = None
        self.settings_view = None
        self.nav_buttons = {}
        self.review_layout = None
        self.review_progress = None
        self.youtube_status = None
        self.podcast_status = None
        self.url_input = None
        self.podcast_search = None
        self.podcasts_list = None
        self.episodes_list = None
        self.episodes_layout = None
        self.sources_list = None
        self.processing_thread = None
        self.stats_labels = {}

    def initialize(self, review_system):
        self.review_system = review_system
        self.media_processor = MediaProcessor()
        self.setup_ui()
        self.setWindowTitle("SHIZEN")
        self.resize(1200, 800)

    def setup_ui(self):
        """Initialize the main UI"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add sidebar
        main_layout.addWidget(self.setup_sidebar())

        # Create and add content stack
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("QStackedWidget {background: #f9fafb;}")
        
        # Add views to stack
        self.content_stack.addWidget(self.create_review_view())    # Index 0
        self.content_stack.addWidget(self.create_upload_view())    # Index 1
        self.content_stack.addWidget(self.create_youtube_view())   # Index 2
        self.content_stack.addWidget(self.create_podcast_view())   # Index 3
        self.content_stack.addWidget(self.create_stats_view())     # Index 4
        self.content_stack.addWidget(self.create_manage_view())    # Index 5
        
        # Create and add settings view
        self.settings_view = Settings(self.review_system)
        self.settings_view.settingsChanged.connect(self.refresh_all_views)
        self.content_stack.addWidget(self.settings_view)           # Index 6

        main_layout.addWidget(self.content_stack)

        # Start review session
        self.review_system.start_session()

    def setup_sidebar(self):
        """Create and setup the sidebar"""
        sidebar = QWidget()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("""
            QWidget {
                background: white;
                border-right: 1px solid #e5e7eb;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(8)

        # App title/logo
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(8, 0, 0, 0)
        
        logo_label = QLabel("SHIZEN")
        logo_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        """)
        
        title_layout.addWidget(logo_label)
        title_layout.addStretch()
        sidebar_layout.addWidget(title_container)
        sidebar_layout.addSpacing(20)

        # Navigation buttons
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        button_styles = {
            "Review": ("#4f46e5", "#818cf8"),    # Indigo
            "Upload": ("#059669", "#10b981"),     # Green
            "YouTube": ("#dc2626", "#ef4444"),    # Red
            "Podcasts": ("#059669", "#10b981"),   # Emerald
            "Stats": ("#0891b2", "#06b6d4"),      # Cyan
            "Manage": ("#6b7280", "#9ca3af"),     # Gray
            "Settings": ("#6b7280", "#9ca3af")    # Gray
        }

        for view_name in self.VIEWS:
            btn = QPushButton(view_name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, v=view_name: self.switch_view(v))
            
            main_color, hover_color = button_styles[view_name]
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 12px 16px;
                    background: transparent;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    color: #6b7280;
                }}
                QPushButton:hover {{
                    background: #f3f4f6;
                    color: {main_color};
                }}
                QPushButton:checked {{
                    background: {main_color};
                    color: white;
                }}
            """)
            
            nav_layout.addWidget(btn)
            self.nav_buttons[view_name] = btn

        sidebar_layout.addWidget(nav_container)
        sidebar_layout.addStretch()

        # Version info
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("""
            color: #9ca3af;
            font-size: 12px;
            padding: 8px;
        """)
        sidebar_layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        return sidebar

    def switch_view(self, view_name):
        """Switch between different views"""
        try:
            index = self.VIEWS.index(view_name)
            self.content_stack.setCurrentIndex(index)
            
            # Update button states
            for name, btn in self.nav_buttons.items():
                btn.setChecked(name == view_name)
                
        except Exception as e:
            print(f"Error switching view: {e}")

    def create_review_view(self):
        """Create the review view"""
        from .components.focus_mode import FocusModeDialog
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Add header with Focus Mode button
        header = QHBoxLayout()
        
        # Title
        title = QLabel("Review")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        """)
        header.addWidget(title)
        
        # Focus Mode button
        focus_btn = QPushButton("Focus Mode")
        focus_btn.setFixedWidth(120)
        focus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        focus_btn.clicked.connect(self.show_focus_mode)
        focus_btn.setStyleSheet("""
            QPushButton {
                background: #4f46e5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #4338ca;
            }
        """)
        header.addWidget(focus_btn)
        
        layout.addLayout(header)

        # Progress bar for daily goal
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.review_progress = QProgressBar()
        self.review_progress.setTextVisible(False)
        self.review_progress.setFixedHeight(4)
        self.review_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #f3f4f6;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: #2196F3;
                border-radius: 2px;
            }
        """)
        progress_layout.addWidget(self.review_progress)
        layout.addWidget(progress_container)

        # Stats panel
        stats = QWidget()
        stats_layout = QHBoxLayout(stats)
        stats_layout.setContentsMargins(20, 20, 20, 20)
        
        for key in ['due', 'new', 'total']:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            
            value_label = QLabel("0")
            value_label.setStyleSheet("""
                font-size: 24px;
                font-weight: bold;
                color: #2196F3;
            """)
            
            title_label = QLabel(key.title())
            title_label.setStyleSheet("color: #666; font-size: 14px;")
            
            container_layout.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
            stats_layout.addWidget(container)
            self.stats_labels[key] = value_label

        stats.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 10px;
                border: 1px solid #eee;
            }
        """)
        layout.addWidget(stats)

        # Review area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea {border: none; background: #f9fafb;}")
        
        content = QWidget()
        self.review_layout = QVBoxLayout(content)
        self.review_layout.setContentsMargins(24, 24, 24, 24)
        self.review_layout.setSpacing(20)
        self.review_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

        view.setStyleSheet("QWidget {background: #f9fafb;}")

        self.update_stats()
        self.load_due_cards()
        return view

    def show_focus_mode(self):
        """Show focus mode dialog"""
        try:
            from .components.focus_mode import FocusModeDialog
            
            if not self.review_system.items:
                QMessageBox.warning(
                    self,
                    "No Content",
                    "Add some content first before using Focus Mode."
                )
                return

            dialog = FocusModeDialog(self.review_system, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.update_stats()
                self.load_due_cards()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to start Focus Mode: {str(e)}"
            )

    def create_upload_view(self):
        """Create the upload view"""
        print("Creating upload view")  # Debug print
        upload_view = UploadView(self.review_system, self.media_processor)
        print("Connecting upload signals")  # Debug print
        upload_view.uploadComplete.connect(self.handle_upload_complete)
        upload_view.uploadFailed.connect(self.handle_upload_error)
        return upload_view

    def handle_upload_complete(self, result: dict):
        """Handle successful upload"""
        try:
            # Add to review system
            self.review_system.add_source(result, result.get('segments', []))
            
            # Show success message
            QMessageBox.information(
                self,
                "Upload Complete",
                f"Successfully processed {result['title']}\n"
                f"Added {len(result.get('segments', []))} segments for review."
            )

            # Switch to review view
            self.switch_view("Review")
            
            # Force complete refresh of the review view
            self.refresh_all_views()
            QApplication.processEvents()

        except Exception as e:
            self.handle_upload_error(str(e))

    def handle_upload_error(self, error: str):
        """Handle upload error"""
        QMessageBox.critical(
            self,
            "Upload Error",
            f"Failed to process upload: {error}"
        )

    def create_youtube_view(self):
        """Create the YouTube view"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("YouTube")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        """)
        header.addWidget(title)
        layout.addLayout(header)

        # Description
        desc = QLabel("Process YouTube videos for learning")
        desc.setStyleSheet("color: #6b7280; font-size: 14px;")
        layout.addWidget(desc)

        # URL input row
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL")
        self.url_input.setMinimumHeight(40)
        self.url_input.returnPressed.connect(self.process_youtube)
        self.url_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 0 16px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        
        process_btn = QPushButton("Process")
        process_btn.setMinimumHeight(40)
        process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        process_btn.clicked.connect(self.process_youtube)
        process_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        
        input_layout.addWidget(self.url_input)
        input_layout.addWidget(process_btn)
        layout.addLayout(input_layout)

        # Progress section (same style as upload view)
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        self.youtube_progress = QProgressBar()
        self.youtube_progress.setVisible(False)
        self.youtube_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #f3f4f6;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #2196F3;
                border-radius: 4px;
            }
        """)

        self.youtube_status = QLabel()
        self.youtube_status.setStyleSheet("color: #6b7280; font-size: 13px;")
        self.youtube_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        progress_layout.addWidget(self.youtube_progress)
        progress_layout.addWidget(self.youtube_status)
        layout.addWidget(progress_container)

        layout.addStretch()
        return view

    def create_podcast_view(self):
        """Create the podcast view"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("Podcasts")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        """)
        header.addWidget(title)
        layout.addLayout(header)

        # Description
        desc = QLabel("Search and process podcasts for learning")
        desc.setStyleSheet("color: #6b7280; font-size: 14px;")
        layout.addWidget(desc)

        # Search row
        search_layout = QHBoxLayout()
        self.podcast_search = QLineEdit()
        self.podcast_search.setPlaceholderText("Search podcasts")
        self.podcast_search.setMinimumHeight(40)
        self.podcast_search.returnPressed.connect(self.search_podcasts)
        self.podcast_search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 0 16px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        
        search_btn = QPushButton("Search")
        search_btn.setMinimumHeight(40)
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.clicked.connect(self.search_podcasts)
        search_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        
        search_layout.addWidget(self.podcast_search)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        # Progress section - Move it here, right after search
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        self.podcast_progress = QProgressBar()
        self.podcast_progress.setVisible(False)
        self.podcast_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #f3f4f6;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #2196F3;
                border-radius: 4px;
            }
        """)

        self.podcast_status = QLabel()
        self.podcast_status.setStyleSheet("color: #6b7280; font-size: 13px;")
        self.podcast_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        progress_layout.addWidget(self.podcast_progress)
        progress_layout.addWidget(self.podcast_status)
        layout.addWidget(progress_container)

        # Results area
        results_layout = QHBoxLayout()
        
        # Podcasts list
        podcasts_widget = QWidget()
        podcasts_layout = QVBoxLayout(podcasts_widget)
        podcasts_layout.setContentsMargins(0, 0, 0, 0)
        
        podcasts_label = QLabel("Podcasts")
        podcasts_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #1f2937;
            margin-bottom: 8px;
        """)
        podcasts_layout.addWidget(podcasts_label)
        
        self.podcasts_list = QListWidget()
        self.podcasts_list.itemClicked.connect(self.load_episodes)
        self.podcasts_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px;
                background: white;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background: #2196F3;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background: #f3f4f6;
            }
        """)
        podcasts_layout.addWidget(self.podcasts_list)
        
        # Episodes list
        episodes_widget = QWidget()
        episodes_layout = QVBoxLayout(episodes_widget)
        episodes_layout.setContentsMargins(0, 0, 0, 0)
        
        episodes_label = QLabel("Episodes")
        episodes_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #1f2937;
            margin-bottom: 8px;
        """)
        episodes_layout.addWidget(episodes_label)
        
        self.episodes_list = QWidget()
        self.episodes_layout = QVBoxLayout(self.episodes_list)
        self.episodes_layout.setSpacing(8)
        
        episodes_scroll = QScrollArea()
        episodes_scroll.setWidget(self.episodes_list)
        episodes_scroll.setWidgetResizable(True)
        episodes_scroll.setMinimumHeight(500)  # Made taller
        episodes_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: white;
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
        """)
        episodes_layout.addWidget(episodes_scroll)
        
        # Add lists to results layout
        results_layout.addWidget(podcasts_widget)
        results_layout.addWidget(episodes_widget)
        layout.addLayout(results_layout)

        return view

    def create_stats_view(self):
        """Create the statistics view"""
        return StatsView(self.review_system)

    def create_manage_view(self):
        """Create the manage view"""
        manage_view = ManageSourcesView(self.review_system)
        # Connect the signal to refresh review view
        manage_view.sourcesChanged.connect(self.refresh_all_views)
        return manage_view
    
    def process_youtube(self):
        """Process YouTube URL"""
        url = self.url_input.text().strip()
        if url:
            self.youtube_progress.setVisible(True)
            self.youtube_progress.setRange(0, 0)  # Indeterminate progress
            self.youtube_status.setText("Processing YouTube video...")
            
            self.processing_thread = ProcessingThread(self.media_processor, url)
            self.processing_thread.finished.connect(self.handle_processing_finished)
            self.processing_thread.error.connect(self.handle_processing_error)
            self.processing_thread.progress.connect(self.youtube_status.setText)
            self.processing_thread.start()

    def search_podcasts(self):
        """Search for podcasts"""
        query = self.podcast_search.text().strip()
        if query:
            self.podcast_progress.setVisible(True)
            self.podcast_progress.setRange(0, 0)  # Indeterminate progress
            self.podcast_status.setText("Searching...")
            self.podcasts_list.clear()
            try:
                results = self.media_processor.search_podcasts(query)
                for podcast in results:
                    item = QListWidgetItem(f"{podcast['title']}\n{podcast['author']}")
                    item.setData(Qt.ItemDataRole.UserRole, podcast)
                    self.podcasts_list.addItem(item)
                self.podcast_status.setText("Search complete")
                self.podcast_progress.setRange(0, 100)
                self.podcast_progress.setValue(100)
            except Exception as e:
                self.podcast_progress.setVisible(False)
                self.podcast_status.setText(f"Search failed: {str(e)}")

    def load_episodes(self, item):
        """Load episodes for selected podcast"""
        podcast = item.data(Qt.ItemDataRole.UserRole)
        
        # Clear previous episodes
        while self.episodes_layout.count():
            child = self.episodes_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        try:
            self.podcast_status.setText("Loading episodes...")
            episodes = self.media_processor.get_podcast_episodes(podcast['feed_url'])
            
            for episode in episodes:
                widget = self.create_episode_widget(episode)
                self.episodes_layout.addWidget(widget)
                
            self.podcast_status.clear()
        except Exception as e:
            self.podcast_status.setText(f"Failed to load episodes: {str(e)}")

    def create_episode_widget(self, episode):
        """Create widget for podcast episode"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        
        title = QLabel(episode['title'])
        title.setWordWrap(True)
        title.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #1f2937;
        """)
        layout.addWidget(title)
        
        if episode.get('duration'):
            duration = QLabel(f"Duration: {episode['duration']}")
            duration.setStyleSheet("color: #6b7280; font-size: 12px;")
            layout.addWidget(duration)
        
        buttons = QHBoxLayout()
        process_btn = QPushButton("Process")
        process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        process_btn.clicked.connect(lambda: self.process_episode(episode))
        process_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        
        buttons.addWidget(process_btn)
        buttons.addStretch()
        layout.addLayout(buttons)
        
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        
        return widget

    def process_episode(self, episode):
        """Process podcast episode"""
        try:
            self.podcast_progress.setVisible(True)
            self.podcast_progress.setRange(0, 0)
            self.podcast_status.setText("Processing episode...")
            
            self.processing_thread = ProcessingThread(
                self.media_processor, episode, 'podcast')
            self.processing_thread.finished.connect(self.handle_processing_finished)
            self.processing_thread.error.connect(self.handle_processing_error)
            self.processing_thread.progress.connect(self.podcast_status.setText)
            self.processing_thread.start()
        except Exception as e:
            self.podcast_progress.setVisible(False)
            self.podcast_status.setText(f"Error: {str(e)}")

    def handle_processing_finished(self, data):
        """Handle successful processing"""
        try:
            self.review_system.add_source(data['source'], data['segments'])
            self.update_stats()
            self.load_due_cards()
            
            msg = f"Processing complete! Added {len(data['segments'])} segments for review."
            
            # Update UI based on current view
            if self.content_stack.currentIndex() == 2:  # YouTube view
                self.youtube_progress.setRange(0, 100)
                self.youtube_progress.setValue(100)
                self.youtube_status.setText(msg)
                self.url_input.clear()
            else:  # Podcast view
                self.podcast_progress.setRange(0, 100)
                self.podcast_progress.setValue(100)
                self.podcast_status.setText(msg)
                
            QMessageBox.information(self, "Success", msg)
            self.switch_view("Review")
            
        except Exception as e:
            self.handle_processing_error(f"Error finalizing processing: {str(e)}")

    def handle_processing_error(self, error_msg):
        """Handle processing error"""
        if self.content_stack.currentIndex() == 2:  # YouTube view
            self.youtube_progress.setVisible(False)
            self.youtube_status.setText(f"Error: {error_msg}")
        else:  # Podcast view
            self.podcast_progress.setVisible(False)
            self.podcast_status.setText(f"Error: {error_msg}")
            
        QMessageBox.critical(self, "Error", f"Processing failed: {error_msg}")

    def create_card_preview(self, card):
        """Create a preview widget for a card"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Card text
        text = QLabel(card['text'])
        text.setWordWrap(True)
        text.setStyleSheet("font-size: 14px; color: #1f2937;")
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedWidth(80)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_card_with_refresh(card['id'], widget))
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        
        layout.addWidget(text)
        layout.addWidget(delete_btn)
        
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        
        return widget

    def delete_card_with_refresh(self, card_id: str, widget: QWidget):
        """Delete a card and refresh the UI"""
        try:
            reply = QMessageBox.question(
                self, 
                'Confirm Deletion',
                'Delete this card permanently?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.review_system.delete_card(card_id)
                widget.deleteLater()
                self.update_stats()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete card: {str(e)}")

    def create_manage_view(self):
        """Create the manage view"""
        from .components.manage_view import ManageSourcesView
        return ManageSourcesView(self.review_system)

    def load_due_cards(self):
        """Load cards due for review"""
        try:
            # Clear existing cards
            while self.review_layout.count() > 1:
                item = self.review_layout.takeAt(0)
                if item.widget():
                    if isinstance(item.widget(), AudioCard):
                        item.widget().cleanup()
                    item.widget().deleteLater()

            # Get stats
            stats = self.review_system.get_stats()
            print(f"Loading cards with stats: {stats}")  # Debug print
            
            # Always show done message if no cards
            if stats['total'] == 0:
                self.show_done_message(stats)
                return

            # Get due items
            due_items = self.review_system.get_due_items()
            print(f"Got {len(due_items)} due items")  # Debug print
            
            if not due_items:
                self.show_done_message(stats)
                return
                
            for item in due_items:
                card = AudioCard(item, item['audio_path'], self.review_system)
                card.reviewed.connect(self.handle_review)
                card.deleted.connect(lambda cid: self.handle_card_action(cid, 'delete'))
                card.skipped.connect(lambda cid: self.handle_card_action(cid, 'skip'))
                card.edited.connect(lambda cid, text: self.handle_card_action(cid, 'edit', text))
                self.review_layout.insertWidget(self.review_layout.count() - 1, card)
                        
        except Exception as e:
            print(f"Error loading cards: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load review cards: {str(e)}")

    def show_done_message(self, stats):
        """Show done message with appropriate context"""
        done_widget = QWidget()
        done_layout = QVBoxLayout(done_widget)
        done_layout.setContentsMargins(32, 32, 32, 32)
        done_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Different icon and message based on if there are any cards at all
        if stats['total'] == 0:
            # Show "Get Started" message
            icon = QLabel("📚")  # Book emoji
            message = "No cards yet!"
            sub_message = "Add some content to start learning"
        else:
            # Show completion message
            icon = QLabel("✅")  # Checkmark emoji
            message = "All done for today!"
            sub_message = "Great job! Come back tomorrow for more cards."

        icon.setStyleSheet("""
            font-size: 48px;
            margin-bottom: 16px;
        """)
        done_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        # Main message
        done_message = QLabel(message)
        done_message.setStyleSheet("""
            color: #1f2937;
            font-size: 24px;
            font-weight: 500;
            margin-bottom: 8px;
        """)
        done_layout.addWidget(done_message, alignment=Qt.AlignmentFlag.AlignCenter)

        # Sub message
        sub_message_label = QLabel(sub_message)
        sub_message_label.setStyleSheet("""
            color: #6b7280;
            font-size: 14px;
        """)
        done_layout.addWidget(sub_message_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Container styling
        done_widget.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
        """)

        self.review_layout.insertWidget(
            self.review_layout.count() - 1,
            done_widget,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

    def handle_card_action(self, card_id: str, action: str, data: str = None):
        """Handle card actions"""
        try:
            if action == 'delete':
                self.review_system.delete_card(card_id)
                # Force immediate refresh of the review feed
                self.refresh_all_views()
                # If no cards left, show done message
                stats = self.review_system.get_stats()
                if stats['total'] == 0:
                    self.show_done_message(stats)
            elif action == 'skip':
                self.review_system.skip_card(card_id)
                self.refresh_all_views()
            elif action == 'edit':
                self.review_system.edit_card_text(card_id, data)
                self.refresh_all_views()
            
            # Update stats
            self.update_stats()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to {action} card: {str(e)}")

    def handle_review(self, item_id: str, response: str):
        """Handle card review response"""
        try:
            self.review_system.process_review(item_id, response)
            self.update_stats()
            self.load_due_cards()  # This will now respect all limits
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process review: {str(e)}")

    def update_stats(self):
        """Update statistics display"""
        stats = self.review_system.get_stats()
        for key, label in self.stats_labels.items():
            label.setText(str(stats[key]))

    def refresh_all_views(self):
        """Refresh all relevant views"""
        try:
            print("Refreshing all views...")  # Debug print
            
            # Clear existing cards from review layout
            while self.review_layout.count() > 1:
                item = self.review_layout.takeAt(0)
                if item.widget():
                    if isinstance(item.widget(), AudioCard):
                        item.widget().cleanup()
                    item.widget().deleteLater()
            
            # Force UI update
            QApplication.processEvents()
            
            # Update stats
            self.update_stats()
            QApplication.processEvents()
            
            # Get current stats
            stats = self.review_system.get_stats()
            print(f"Current stats after refresh: {stats}")  # Debug print
            
            # If no cards, show done message
            if stats['total'] == 0:
                self.show_done_message(stats)
                QApplication.processEvents()
                return
            
            # Reload due cards
            self.load_due_cards()
            QApplication.processEvents()
            
            # Update stats view if it exists
            stats_view = self.content_stack.widget(4)  # Index 4 is Stats view
            if stats_view and hasattr(stats_view, 'update_stats'):
                stats_view.update_stats()
                QApplication.processEvents()
            
            # Force layout update
            self.review_layout.parentWidget().update()
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Error in refresh_all_views: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to refresh views: {str(e)}"
            )

    def closeEvent(self, event):
        """Handle application closure"""
        try:
            # End the review session
            self.review_system.end_session()
            
            # Clean up upload view workers
            upload_view = self.content_stack.widget(1)  # Index 1 is Upload view
            if isinstance(upload_view, UploadView):
                upload_view.cleanup()
            
            # Clean up any playing audio
            for i in range(self.review_layout.count()):
                item = self.review_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), AudioCard):
                    item.widget().cleanup()
            
            # Clean up any processing threads
            if hasattr(self, 'processing_thread') and self.processing_thread is not None:
                self.processing_thread.quit()
                self.processing_thread.wait()
                self.processing_thread = None

            # Clean up media processor
            if hasattr(self, 'media_processor'):
                if hasattr(self.media_processor.whisper, 'model'):
                    del self.media_processor.whisper.model
                del self.media_processor

            event.accept()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            event.accept()