"""
Style and icon constants for the music player UI.
"""

SIDEBAR_BG_COLOR: str = "rgba(20, 20, 20, 200)"
SIDEBAR_HOVER_COLOR: str = "rgba(50, 50, 50, 200)"
SPOTIFY_GREEN: str = "#1DB954"
SPOTIFY_GREEN_HOVER: str = "#25e06a"
WHITE: str = "white"
BLACK: str = "black"

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