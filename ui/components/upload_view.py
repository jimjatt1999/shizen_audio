# Create NEW FILE: ui/components/upload_view.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QProgressBar, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

class DropArea(QLabel):
    fileDropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("\n\nDrop media files here\nor click to select\n\n")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 12px;
                padding: 24px;
                background: #f9fafb;
                color: #6b7280;
                min-height: 150px;
            }
            QLabel:hover {
                background: #f3f4f6;
                border-color: #2196F3;
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet(self.styleSheet().replace("#ccc", "#2196F3"))
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("#2196F3", "#ccc"))

    def dropEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("#2196F3", "#ccc"))
        for url in event.mimeData().urls():
            self.fileDropped.emit(url.toLocalFile())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.openFileDialog()

    def openFileDialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Media File",
            "",
            "Media Files (*.mp3 *.mp4 *.mov *.mkv *.m4a *.wav);;All Files (*.*)"
        )
        if file_path:
            self.fileDropped.emit(file_path)

class UploadView(QWidget):
    def __init__(self, review_system, media_processor):
        super().__init__()
        self.review_system = review_system
        self.media_processor = media_processor
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("Upload Media")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        """)
        header.addWidget(title)
        layout.addLayout(header)

        # Description
        desc = QLabel("Upload audio or video files for learning")
        desc.setStyleSheet("color: #6b7280; font-size: 14px;")
        layout.addWidget(desc)

        # Drop area
        self.drop_area = DropArea()
        self.drop_area.fileDropped.connect(self.process_file)
        layout.addWidget(self.drop_area)

        # Progress section
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
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

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #6b7280; font-size: 13px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        layout.addWidget(progress_container)

        # Supported formats info
        formats = QLabel(
            "Supported formats: MP3, MP4, MOV, MKV, M4A, WAV\n"
            "Video files will be automatically converted to audio"
        )
        formats.setStyleSheet("""
            color: #6b7280;
            font-size: 13px;
            font-style: italic;
            margin-top: 16px;
        """)
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(formats)

        # Recent uploads list (optional)
        self.setup_recent_uploads()

        layout.addStretch()

    def setup_recent_uploads(self):
        """Setup recent uploads section"""
        group = QWidget()
        group_layout = QVBoxLayout(group)
        
        # Header
        header = QLabel("Recent Uploads")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: 500;
            color: #1f2937;
            margin-bottom: 8px;
        """)
        group_layout.addWidget(header)
        
        # List container
        self.recent_list = QVBoxLayout()
        group_layout.addLayout(self.recent_list)
        
        self.layout().addWidget(group)

    def add_recent_upload(self, title: str):
        """Add item to recent uploads"""
        item = QWidget()
        item_layout = QHBoxLayout(item)
        
        label = QLabel(title)
        label.setStyleSheet("color: #4b5563; font-size: 13px;")
        
        item_layout.addWidget(label)
        item_layout.addStretch()
        
        self.recent_list.insertWidget(0, item)
        
        # Keep only last 5 items
        if self.recent_list.count() > 5:
            item = self.recent_list.takeAt(self.recent_list.count() - 1)
            if item.widget():
                item.widget().deleteLater()

    def process_file(self, file_path: str):
        """Process uploaded file"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_label.setText("Processing file...")

            path = Path(file_path)
            if path.suffix.lower() in ['.mp4', '.mov', '.mkv']:
                self.status_label.setText("Converting video to audio...")
            
            result = self.media_processor.process_upload(path)
            
            # Add to review system
            self.review_system.add_source(result, result.get('segments', []))
            
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.status_label.setText("Upload complete!")
            
            # Add to recent uploads
            self.add_recent_upload(result['title'])
            
            # Show success message
            QMessageBox.information(
                self,
                "Upload Complete",
                f"Successfully processed {result['title']}\n"
                f"Added {len(result.get('segments', []))} segments for review."
            )

        except Exception as e:
            self.progress_bar.setVisible(False)
            self.status_label.setText(f"Error: {str(e)}")
            QMessageBox.critical(
                self,
                "Upload Error",
                f"Failed to process upload: {str(e)}"
            )