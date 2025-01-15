# ui/styles.py

class StyleSheet:
    # Color Palette
    COLORS = {
        'primary': '#2196F3',
        'primary_dark': '#1976D2',
        'success': '#4CAF50',
        'warning': '#FFC107',
        'danger': '#F44336',
        'background': '#FFFFFF',
        'surface': '#F8F9FA',
        'text': '#212529',
        'text_secondary': '#6C757D',
        'border': '#E9ECEF'
    }

    # Common Styles
    COMMON = f"""
        QWidget {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
            color: {COLORS['text']};
        }}
        
        QLabel {{
            background: transparent;
        }}
    """

    # Input Fields
    INPUT = f"""
        QLineEdit {{
            padding: 12px 16px;
            background: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            font-size: 14px;
        }}
        
        QLineEdit:focus {{
            border: 2px solid {COLORS['primary']};
        }}
    """

    # Buttons
    BUTTON = f"""
        QPushButton {{
            padding: 12px 24px;
            background: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            background: {COLORS['primary_dark']};
        }}
        
        QPushButton:disabled {{
            background: {COLORS['border']};
        }}
    """

    # Cards
    CARD = f"""
        QWidget#card {{
            background: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 20px;
        }}
    """

    # Lists
    LIST = f"""
        QListWidget {{
            background: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 8px;
        }}
        
        QListWidget::item {{
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 4px;
        }}
        
        QListWidget::item:selected {{
            background: {COLORS['primary']};
            color: white;
        }}
    """

    # Scroll Areas
    SCROLL = f"""
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        
        QScrollBar:vertical {{
            border: none;
            background: {COLORS['surface']};
            width: 8px;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {COLORS['border']};
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {COLORS['text_secondary']};
        }}
    """

    @classmethod
    def get_all(cls):
        return cls.COMMON + cls.INPUT + cls.BUTTON + cls.CARD + cls.LIST + cls.SCROLL