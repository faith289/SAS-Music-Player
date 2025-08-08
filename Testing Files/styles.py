"""
Style and icon constants for the music player UI.
"""

SIDEBAR_BG_COLOR: str = "rgba(20, 20, 20, 200)"
SIDEBAR_HOVER_COLOR: str = "rgba(50, 50, 50, 200)"
SPOTIFY_GREEN: str = "#1DB954"
SPOTIFY_GREEN_HOVER: str = "#25e06a"
WHITE: str = "white"
BLACK: str = "black"

def get_button_style_sidebar_active(primary_color="#1DB954", hover_color="#25e06a"):
    """Get sidebar active button style with custom colors"""
    # Calculate text color based on background brightness
    from PyQt6.QtGui import QColor
    bg_color = QColor(primary_color)
    text_color = "white" if bg_color.lightness() < 128 else "black"
    
    return f"""
        QPushButton {{
            background-color: {primary_color};
            color: {text_color};
            font-weight: bold;
            border-radius: 8px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
    """

def get_seek_slider_style(accent_color="#48fa6c"):
    """Get seek slider style with custom accent color"""
    return f"""
        QSlider::groove:horizontal {{
            border: none;
            height: 10px;
            background: rgba(255, 255, 255, 0.07);
            border-radius: 5px;
        }}
        QSlider::sub-page:horizontal {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {accent_color},
                stop:1 {accent_color}
            );
            border-radius: 5px;
        }}
        QSlider::handle:horizontal {{
            background: white;
            border: 1px solid rgba(0, 0, 0, 0.15);
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }}
    """

def get_volume_slider_style(accent_color="#48fa6c"):
    """Get volume slider style with custom accent color"""
    return f"""
        QSlider::groove:horizontal {{
            border: none;
            height: 6px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.2);
            width: 14px;
            height: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }}
        QSlider::sub-page:horizontal {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {accent_color},
                stop:1 {accent_color}
            );
            border-radius: 3px;
        }}
    """

ICON_PLAY: str = "assets/play.png"
ICON_PAUSE: str = "assets/pause.png"
ICON_NEXT: str = "assets/next.png"
ICON_PREV: str = "assets/prev.png"
ICON_BRIGHTNESS: str = "assets/brightness.png"
ICON_APP: str = "assets/icon.ico"

BUTTON_STYLE_TRANSPARENT: str = """
    QPushButton {
        background-color: transparent;
        border: none;
        padding: 4px;
    }
    QPushButton:hover {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 6px;
    }
    QPushButton:pressed {
        background-color: rgba(255, 255, 255, 0.2);
    }
"""

BUTTON_STYLE_SIDEBAR: str = f"""
    QPushButton {{
        background-color: {SIDEBAR_BG_COLOR};
        color: {WHITE};
        font-weight: bold;
        border-radius: 8px;
    }}
    QPushButton:hover {{
        background-color: {SIDEBAR_HOVER_COLOR};
    }}
"""

BUTTON_STYLE_SIDEBAR_ACTIVE: str = f"""
    QPushButton {{
        background-color: {SPOTIFY_GREEN};
        color: {BLACK};
        font-weight: bold;
        border-radius: 8px;
    }}
    QPushButton:hover {{
        background-color: {SPOTIFY_GREEN_HOVER};
    }}
"""

VOLUME_BUTTON_STYLE: str = """
    QPushButton {
        background-color: rgba(255, 255, 255, 30);
        color: white;
        font-weight: bold;
        font-size: 14px;
        border: none;
        border-radius: 6px;
    }
    QPushButton:hover {
        background-color: rgba(255, 255, 255, 60);
    }
""" 

#FAiTH