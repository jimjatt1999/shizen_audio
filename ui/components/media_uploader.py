# Create NEW FILE: ui/components/media_uploader.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                           QProgressBar, QFileDialog)
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

class MediaUploader(QWidget):
    uploadComplete = pyqtSignal(dict)
    uploadFailed = pyqtSignal(str)

    def __init__(self, media_processor):
        super().__init__()
        self.media_processor = media_processor
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Drop area
        self.drop_area = DropArea()
        self.drop_area.fileDropped.connect(self.process_file)
        layout.addWidget(self.drop_area)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
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
        layout.addWidget(self.progress)

        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #6b7280; font-size: 13px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def process_file(self, file_path: str):
        """Process uploaded file"""
        try:
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)  # Indeterminate progress
            self.status_label.setText("Processing file...")

            path = Path(file_path)
            if path.suffix.lower() in ['.mp4', '.mov', '.mkv']:
                self.status_label.setText("Converting video to audio...")
            
            result = self.media_processor.process_upload(path)
            
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            self.status_label.setText("Upload complete!")
            
            self.uploadComplete.emit(result)

        except Exception as e:
            self.progress.setVisible(False)
            self.status_label.setText(f"Error: {str(e)}")
            self.uploadFailed.emit(str(e))