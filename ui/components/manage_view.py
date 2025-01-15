# ui/components/manage_view.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QScrollArea, QGroupBox, QProgressBar, QDialog,
                           QMessageBox)
from PyQt6.QtCore import Qt
from .content_player import ContentPlayer

class ManageSourcesView(QWidget):
    def __init__(self, review_system):
        super().__init__()
        self.review_system = review_system
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header with title and refresh button
        header = QHBoxLayout()
        title = QLabel("Manage Sources")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        """)
        header.addWidget(title)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_sources)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Scrollable sources list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        """)
        
        content = QWidget()
        self.sources_layout = QVBoxLayout(content)
        self.sources_layout.setSpacing(12)
        self.sources_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Initial load
        self.refresh_sources()

    def create_source_item(self, source):
        """Create widget for source item"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header row with title and type
        header = QHBoxLayout()
        
        # Title and metadata
        info_layout = QVBoxLayout()
        title = QLabel(source['title'])
        title.setWordWrap(True)
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: 500;
            color: #1f2937;
        """)
        
        metadata = QLabel(f"Type: {source['type']}")
        metadata.setStyleSheet("color: #6b7280; font-size: 13px;")
        
        info_layout.addWidget(title)
        info_layout.addWidget(metadata)
        header.addLayout(info_layout)
        
        # Progress indicator
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        progress_label = QLabel(f"{source['reviewed_count']}/{source['card_count']} cards reviewed")
        progress_label.setStyleSheet("color: #6b7280; font-size: 13px;")
        progress_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        progress = QProgressBar()
        progress.setRange(0, source['card_count'])
        progress.setValue(source['reviewed_count'])
        progress.setFixedWidth(100)
        progress.setFixedHeight(4)
        progress.setTextVisible(False)
        progress.setStyleSheet("""
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
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(progress)
        header.addWidget(progress_container)
        layout.addLayout(header)
        
        # Actions row
        actions = QHBoxLayout()
        actions.setSpacing(8)
        
        # Play button
        play_btn = QPushButton("Play Content")
        play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        play_btn.clicked.connect(lambda: self.play_content(source))
        play_btn.setStyleSheet("""
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
        
        # Browse button
        browse_btn = QPushButton("Browse Cards")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(lambda: self.browse_cards(source))
        browse_btn.setStyleSheet(play_btn.styleSheet())
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_source(source))
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        
        actions.addWidget(play_btn)
        actions.addWidget(browse_btn)
        actions.addWidget(delete_btn)
        actions.addStretch()
        layout.addLayout(actions)
        
        # Widget styling
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        
        return widget

    def refresh_sources(self):
        """Refresh the sources list"""
        # Clear existing items
        while self.sources_layout.count() > 1:  # Keep the stretch
            item = self.sources_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add sources
        for source in self.review_system.get_sources():
            self.sources_layout.insertWidget(
                self.sources_layout.count() - 1,
                self.create_source_item(source)
            )

# In manage_view.py

    def play_content(self, source):
        """Play full content"""
        try:
            # Get segments for this source
            segments = self.review_system.get_source_segments(source['audio_path'])
            
            # Create player dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Playing: {source['title']}")
            dialog.resize(1000, 600)  # Make dialog bigger
            
            # Create layout
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(16, 16, 16, 16)
            
            # Create and add player
            player = ContentPlayer(source['audio_path'], segments)
            layout.addWidget(player)
            
            # Show dialog
            try:
                dialog.exec()
            finally:
                # Ensure cleanup happens
                player.cleanup()
                
        except Exception as e:
            print(f"Error playing content: {str(e)}")  # Add debug print
            QMessageBox.critical(
                self,
                "Playback Error",
                f"Failed to play content: {str(e)}"
            )

    def browse_cards(self, source):
        """Show dialog with cards from source"""
        try:
            from .card_browser import CardBrowserDialog
            dialog = CardBrowserDialog(self.review_system, source['audio_path'], self)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to browse cards: {str(e)}"
            )

    def delete_source(self, source):
        """Delete source and its cards"""
        reply = QMessageBox.question(
            self, 
            'Confirm Deletion',
            'Delete this source and all its cards?\nThis cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.review_system.delete_source(source['audio_path'])
                self.refresh_sources()
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Source and associated cards deleted successfully!"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete source: {str(e)}"
                )