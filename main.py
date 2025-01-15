# main.py
import sys
from pathlib import Path
import multiprocessing

# Add the project root directory to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from PyQt6.QtWidgets import QApplication
from models.review import ReviewSystem
from ui.main_window import MainWindow

def main():
    # Use spawn method instead of fork
    multiprocessing.set_start_method('spawn', force=True)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    review_system = ReviewSystem()
    window = MainWindow.create(review_system)
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()