# ui/components/analysis_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QScrollArea, QWidget, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from .details_dialog import DetailsDialog


class AnalysisThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, ai_helper, text, learning_lang, native_lang):
        super().__init__()
        self.ai_helper = ai_helper
        self.text = text
        self.learning_lang = learning_lang
        self.native_lang = native_lang
        self.is_running = True  # Add flag for clean shutdown
        
    def run(self):
        try:
            if not self.text.strip():
                raise ValueError("Text is empty")

            if not self.is_running:
                return

            print(f"Starting analysis for text in {self.learning_lang}")  # Debug print
            
            result = self.ai_helper.generate_analysis(
                self.text, 
                self.learning_lang, 
                self.native_lang
            )
            
            if not self.is_running:
                return

            if not result or not isinstance(result, dict):
                raise ValueError("Invalid analysis result format")

            print(f"Analysis complete, emitting result")  # Debug print
            self.finished.emit(result)
            
        except Exception as e:
            print(f"Analysis error: {str(e)}")  # Debug print
            self.error.emit(str(e))

    def stop(self):
        """Stop the thread cleanly"""
        self.is_running = False

    def __del__(self):
        """Ensure thread is stopped on deletion"""
        self.stop()
        self.wait()

class AnalysisDialog(QDialog):
    def __init__(self, text: str, review_system, parent=None):
        super().__init__(parent)
        self.text = text
        self.review_system = review_system
        self.setup_ui()
        self.start_analysis()
        
        # Set window properties
        self.setWindowTitle("AI Analysis")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Original text
        text_container = QWidget()
        text_container.setStyleSheet("""
            QWidget {
                background: #f3f4f6;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        text_layout = QVBoxLayout(text_container)
        
        original_label = QLabel("Original Text:")
        original_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        text_layout.addWidget(original_label)
        
        original = QLabel(self.text)
        original.setStyleSheet("""
            font-size: 16px;
            color: #1f2937;
            margin-top: 4px;
        """)
        original.setWordWrap(True)
        text_layout.addWidget(original)
        
        layout.addWidget(text_container)
        
        # Loading indicator
        self.loading = QProgressBar()
        self.loading.setTextVisible(False)
        self.loading.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #f3f4f6;
                border-radius: 2px;
                height: 4px;
            }
            QProgressBar::chunk {
                background: #2196F3;
            }
        """)
        layout.addWidget(self.loading)
        
        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setSpacing(16)
        scroll.setWidget(self.content)
        
        self.content.hide()  # Hide until analysis is complete
        layout.addWidget(scroll)
        
        # Buttons container
        buttons_layout = QHBoxLayout()
        
        # Regenerate button
        regenerate_btn = QPushButton("Regenerate Analysis")
        regenerate_btn.setStyleSheet("""
            QPushButton {
                background: #4f46e5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #4338ca;
            }
        """)
        regenerate_btn.clicked.connect(self.regenerate_analysis)
        
        # More Details button
        more_details_btn = QPushButton("Ask for More Details")
        more_details_btn.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #047857;
            }
        """)
        more_details_btn.clicked.connect(self.show_details_chat)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        buttons_layout.addWidget(regenerate_btn)
        buttons_layout.addWidget(more_details_btn)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)

    def add_section(self, title: str, content: str or list or dict):
        """Helper to add a section to the analysis"""
        section = QWidget()
        section.setStyleSheet("""
            QWidget {
                background: #e9e9eb;
                border-radius: 18px;
                margin: 4px 0;
            }
        """)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(16, 16, 16, 16)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #000000;
            margin-bottom: 8px;
        """)
        section_layout.addWidget(title_label)
        
        if isinstance(content, list):
            for item in content:
                item_label = QLabel(f"• {str(item)}")
                item_label.setWordWrap(True)
                item_label.setStyleSheet("""
                    color: #000000;
                    font-size: 15px;
                    line-height: 1.4;
                    margin: 4px 0;
                """)
                section_layout.addWidget(item_label)
        elif isinstance(content, dict):
            for key, value in content.items():
                item_label = QLabel(f"• {key}: {str(value)}")
                item_label.setWordWrap(True)
                item_label.setStyleSheet("""
                    color: #000000;
                    font-size: 15px;
                    line-height: 1.4;
                    margin: 4px 0;
                """)
                section_layout.addWidget(item_label)
        else:
            content_label = QLabel(str(content))
            content_label.setWordWrap(True)
            content_label.setStyleSheet("""
                color: #000000;
                font-size: 15px;
                line-height: 1.4;
            """)
            section_layout.addWidget(content_label)
        
        # Add to layout with proper alignment
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(section)
        container_layout.addStretch()
        
        self.content_layout.addWidget(container)

    def start_analysis(self):
        """Start or retrieve the analysis"""
        try:
            settings = self.review_system.get_settings()
            cache_key = f"{self.text}:{settings['learning_language']}:{settings['native_language']}"
            
            # Try to get from cache first
            if hasattr(self.review_system, 'analysis_cache') and cache_key in self.review_system.analysis_cache:
                print("Using cached analysis")
                self.loading.hide()
                self.show_analysis(self.review_system.analysis_cache[cache_key])
                return

            # If not in cache, start new analysis
            print("Generating new analysis")
            self.loading.setRange(0, 0)  # Indeterminate progress
            self.thread = AnalysisThread(
                self.review_system.ai_helper,
                self.text,
                settings['learning_language'],
                settings['native_language']
            )
            self.thread.finished.connect(self.handle_analysis_complete)
            self.thread.error.connect(self.show_error)
            self.thread.start()

        except Exception as e:
            self.show_error(str(e))

    def handle_analysis_complete(self, result: dict):
        """Handle completed analysis and cache it"""
        try:
            settings = self.review_system.get_settings()
            cache_key = f"{self.text}:{settings['learning_language']}:{settings['native_language']}"
            
            # Initialize cache if it doesn't exist
            if not hasattr(self.review_system, 'analysis_cache'):
                self.review_system.analysis_cache = {}
            
            # Cache the result
            self.review_system.analysis_cache[cache_key] = result
            
            # Show the analysis
            self.show_analysis(result)
            
            # Save state to persist cache
            self.review_system.save_state()
            
        except Exception as e:
            self.show_error(str(e))

    def show_analysis(self, result: dict):
        """Display the analysis results"""
        self.loading.hide()
        
        # Check if the result contains an error
        if result.get('translation', '').startswith('Analysis failed'):
            self.show_error(result.get('notes', ['Unknown error'])[0])
            return
            
        # Add each section
        if result.get('translation'):
            self.add_section("Translation", str(result['translation']))
            
        if result.get('words'):
            if isinstance(result['words'], (list, dict)):
                self.add_section("Vocabulary", result['words'])
            else:
                self.add_section("Vocabulary", str(result['words']))
            
        if result.get('grammar'):
            if isinstance(result['grammar'], (list, dict)):
                self.add_section("Grammar Points", result['grammar'])
            else:
                self.add_section("Grammar Points", str(result['grammar']))
            
        if result.get('notes'):
            if isinstance(result['notes'], (list, dict)):
                self.add_section("Usage Notes", result['notes'])
            else:
                self.add_section("Usage Notes", str(result['notes']))
            
        self.content.show()

    def show_error(self, error: str):
        """Display error message"""
        self.loading.hide()
        
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        
        error_label = QLabel("Analysis Failed")
        error_label.setStyleSheet("""
            color: #ef4444;
            font-weight: bold;
            font-size: 14px;
        """)
        error_layout.addWidget(error_label)
        
        error_msg = QLabel(str(error))
        error_msg.setWordWrap(True)
        error_msg.setStyleSheet("color: #4b5563;")
        error_layout.addWidget(error_msg)
        
        self.content_layout.addWidget(error_widget)
        self.content.show()

        # Add retry button
        retry_btn = QPushButton("Retry Analysis")
        retry_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                margin-top: 16px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        retry_btn.clicked.connect(self.start_analysis)
        error_layout.addWidget(retry_btn)

    def regenerate_analysis(self):
        """Force regenerate the analysis"""
        try:
            # Clear existing content
            while self.content_layout.count():
                item = self.content_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
            # Clear from cache
            settings = self.review_system.get_settings()
            cache_key = f"{self.text}:{settings['learning_language']}:{settings['native_language']}"
            if cache_key in self.review_system.analysis_cache:
                del self.review_system.analysis_cache[cache_key]
        
            # Start new analysis
            self.content.hide()
            self.loading.show()
            self.start_analysis()
        
        except Exception as e:
            self.show_error(str(e))

    def show_details_chat(self):
        """Show chat dialog for more details"""
        dialog = DetailsDialog(
            text=self.text,
            review_system=self.review_system,
            parent=self
        )
        dialog.exec()