# ui_builder.py - UI Builder Class for SAS Music Player
# Extracted UI setup logic from main application

import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QListWidget, QSlider, QHBoxLayout, 
    QSizePolicy, QVBoxLayout, QGraphicsBlurEffect, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QSpacerItem
)
from PyQt6.QtGui import QPixmap, QIcon, QFont, QColor
from PyQt6.QtCore import Qt, QSize, QTimer

from widgets import ScrollingLabel, GlowButton, ReorderablePlaylist, PulsingDelegate, AlbumArtWidget
from styles import (
    SIDEBAR_BG_COLOR, SIDEBAR_HOVER_COLOR, SPOTIFY_GREEN, SPOTIFY_GREEN_HOVER, WHITE, BLACK,
    ICON_PLAY, ICON_PAUSE, ICON_NEXT, ICON_PREV, ICON_BRIGHTNESS, ICON_APP,
    BUTTON_STYLE_TRANSPARENT, BUTTON_STYLE_SIDEBAR, BUTTON_STYLE_SIDEBAR_ACTIVE, VOLUME_BUTTON_STYLE,
    get_button_style_sidebar_active, get_seek_slider_style, get_volume_slider_style
)
from utils import format_time, get_safe_basename
from math import cos, sin  # Add this import for the trigonometric functions







def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller .exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

class UIBuilder:
    """Handles all UI setup and construction for the SAS Music Player"""
    
    def __init__(self, parent):
        """Initialize UIBuilder with reference to parent SASPlayer instance"""
        self.parent = parent
        self.central_widget = parent.centralWidget()
        self.color_settings = parent.color_settings
    
    def setup_ui(self):
        """Main UI setup coordinator - calls all setup methods in order"""
        self._setup_background_layers()
        self._setup_sidebar()
        self._setup_main_area()
        self._setup_seek_bar()
        self._setup_control_buttons()
        self._setup_volume_controls()
        self._compose_layouts()
        self.central_widget.raise_()
        self.parent.brightness_btn.raise_()
        self._setup_bottom_shadow()
        self.fix_color_button_parent()
        self.position_color_below_brightness()  # ADD this line
        self.parent.ensure_proper_layer_order()

    
    def _setup_background_layers(self):
        """Create background elements (blur labels, overlays)"""
        # Create background elements first (lowest layer)
        self.parent.bg_blur_label_1 = QLabel(self.central_widget)
        self.parent.bg_blur_label_1.setGeometry(0, 0, self.parent.width(), self.parent.height())
        self.parent.bg_blur_label_1.setScaledContents(True)
        self.parent.bg_blur_label_1.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.parent.bg_blur_label_2 = QLabel(self.central_widget)
        self.parent.bg_blur_label_2.setGeometry(0, 0, self.parent.width(), self.parent.height())
        self.parent.bg_blur_label_2.setScaledContents(True)
        self.parent.bg_blur_label_2.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.parent.dark_overlay = QLabel(self.central_widget)
        self.parent.dark_overlay.setGeometry(0, 0, self.parent.width(), self.parent.height())
        self.parent.dark_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.parent.dark_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.parent.dark_overlay_opacity_effect = QGraphicsOpacityEffect(self.parent.dark_overlay)
        self.parent.dark_overlay.setGraphicsEffect(self.parent.dark_overlay_opacity_effect)
        self.parent.dark_overlay_opacity_effect.setOpacity(0.6)

        self.parent.playlist_glass = QLabel(self.central_widget)
        self.parent.playlist_glass.setGeometry(0, 0, 200, self.parent.height())
        self.parent.playlist_glass.setStyleSheet("border-radius: 0px;")

        self.parent.green_overlay = QLabel(self.central_widget)
        self.parent.green_overlay.setGeometry(0, 0, self.parent.width(), self.parent.height())
        self.parent.green_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Set initial green overlay color
        self.parent.update_green_overlay_color()

        # IMPORTANT: Ensure all background elements stay in the back
        self.parent.bg_blur_label_1.lower()
        self.parent.bg_blur_label_2.lower()
        self.parent.dark_overlay.lower()
        self.parent.playlist_glass.lower()
        self.parent.green_overlay.lower()

        # Create brightness button last (highest layer)
        self.parent.brightness_btn = GlowButton(self.central_widget)
        self.parent.brightness_btn.setIcon(QIcon(resource_path(ICON_BRIGHTNESS)))
        self.parent.brightness_btn.setIconSize(QSize(20, 20))
        self.parent.brightness_btn.setFixedSize(28, 28)
        self.parent.brightness_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        self.parent.brightness_btn.clicked.connect(self.parent.toggle_darkness)

        # IMPORTANT: Ensure it's always on the absolute top
        self.parent.brightness_btn.raise_()
        self.parent.brightness_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # ADD COLOR BUTTON RIGHT BELOW BRIGHTNESS BUTTON
        # ADD COLOR BUTTON RIGHT BELOW BRIGHTNESS BUTTON with custom icon
        self.parent.color_btn = QPushButton(self.central_widget)
        self.setup_color_button_icon()  # Custom icon loading method
        # ADD THIS LINE to match brightness button styling:
        self.match_brightness_button_styling()
        # Move from sidebar to main area
        self.parent.color_btn.setFixedSize(28, 28)  # Same size as brightness button
        self.parent.color_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        # Connect to color dialog (you'll need to ensure this connection exists in muuusic.py)
        # self.parent.color_btn.clicked.connect(self.parent.show_color_dialog)

        # Position color button below brightness button
        self.parent.color_btn.raise_()
        self.parent.color_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        

    def _setup_sidebar(self):
        """Setup sidebar with buttons and playlist"""
        self.parent.sidebar = QVBoxLayout()

        self.parent.load_btn = QPushButton("Load Songs")
        self.parent.shuffle_btn = QPushButton("Shuffle: OFF")
        self.parent.repeat_btn = QPushButton("Repeat: OFF")
        

        button_container = QWidget()
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 20, 10, 10)

        self.parent.load_btn.setFixedHeight(40)
        self.parent.load_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.parent.load_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)
        button_layout.addWidget(self.parent.load_btn)

        for btn in [self.parent.shuffle_btn, self.parent.repeat_btn]:  # Remove color_btn from sidebar
            btn.setFixedHeight(40)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)
            button_layout.addWidget(btn)


        button_container.setLayout(button_layout)

        self.parent.playlist_widget = ReorderablePlaylist(on_reorder_callback=self.parent.sync_playlist_order)
        self.parent.playlist_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.parent.playlist_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.parent.playlist_widget.customContextMenuRequested.connect(self.parent.show_playlist_context_menu)
        self.parent.playlist_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.parent.playlist_widget.setAlternatingRowColors(True)

        # Ensure PulsingDelegate is set with correct lambda for current index
        self.parent.playlist_widget.setItemDelegate(PulsingDelegate(
            self.parent.playlist_widget, 
            lambda: self.parent.current_index, 
            self.color_settings
        ))

        # Initialize playlist colors dynamically
        self.parent.update_playlist_colors()

        self.parent.sidebar.addWidget(button_container)
        self.parent.sidebar.addSpacing(10)
        self.parent.sidebar.addWidget(self.parent.playlist_widget)
    
    def _setup_main_area(self):
        """Setup main area with album art, song labels, and metadata"""
        self.parent.main_layout = QVBoxLayout()

        self.parent.album_art_label = AlbumArtWidget()

        # Add a soft, more visible drop shadow effect to the album art
        soft_shadow = QGraphicsDropShadowEffect(self.parent.album_art_label)
        soft_shadow.setBlurRadius(60)
        soft_shadow.setOffset(0, 12)
        soft_shadow.setColor(QColor(0, 0, 0, 180))
        self.parent.album_art_label.setGraphicsEffect(soft_shadow)

        self.parent.song_label = ScrollingLabel("No song loaded")
        self.parent.song_label.setFont(QFont("Segoe UI", 14))
        self.parent.song_label.setStyleSheet("color: white;")
        self.parent.song_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        shadow = QGraphicsDropShadowEffect(self.parent.song_label)
        shadow.setBlurRadius(25)
        shadow.setOffset(3, 3)
        shadow.setColor(QColor(0, 0, 0, 220))
        self.parent.song_label.setGraphicsEffect(shadow)

        self.parent.meta_label = ScrollingLabel("")
        self.parent.meta_label.setFont(QFont("Segoe UI", 10))
        self.parent.meta_label.setStyleSheet("color: white;")
        self.parent.meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parent.apply_shadow(self.parent.meta_label, 8, 1, 1)

        self.parent.meta_layout = QVBoxLayout()
        self.parent.meta_layout.setSpacing(8)
        self.parent.meta_layout.setContentsMargins(0, 16, 0, 0)  # Add top margin for shadow
        self.parent.meta_layout.addWidget(self.parent.album_art_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.parent.meta_layout.addWidget(self.parent.song_label)
        self.parent.meta_layout.addWidget(self.parent.meta_label)

        self.parent.main_layout.addLayout(self.parent.meta_layout)
        self.parent.main_layout.addSpacing(15)
    
    def _setup_seek_bar(self):
        """Setup seek bar with time labels and slider"""
        self.parent.elapsed_label = QLabel("00:00")
        self.parent.elapsed_label.setFont(QFont("Segoe UI", 9))
        self.parent.elapsed_label.setStyleSheet("color: lightgray;")
        self.parent.apply_shadow(self.parent.elapsed_label, 6, 1, 1)

        self.parent.duration_label = QLabel("00:00")
        self.parent.duration_label.setFont(QFont("Segoe UI", 9))
        self.parent.duration_label.setStyleSheet("color: lightgray;")
        self.parent.apply_shadow(self.parent.duration_label, 6, 1, 1)

        self.parent.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.seek_slider.setSingleStep(1)
        self.parent.seek_slider.setRange(0, 1000)
        self.parent.seek_slider.setStyleSheet(get_seek_slider_style(self.color_settings.get_accent_green().name()))

        self.parent.seek_row = QHBoxLayout()
        self.parent.seek_row.addWidget(self.parent.elapsed_label)
        self.parent.seek_row.addWidget(self.parent.seek_slider)
        self.parent.seek_row.addWidget(self.parent.duration_label)

        self.parent.main_layout.addLayout(self.parent.seek_row)
    
    def _setup_control_buttons(self):
        """Setup play/pause/next/prev control buttons and volume controls"""
        self.parent.controls = QHBoxLayout()
        self.parent.controls.setContentsMargins(0, 0, 0, 0)
        self.parent.controls.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.parent.play_icon = QIcon(resource_path(ICON_PLAY))
        self.parent.pause_icon = QIcon(resource_path(ICON_PAUSE))
        self.parent.next_icon = QIcon(resource_path(ICON_NEXT))
        self.parent.prev_icon = QIcon(resource_path(ICON_PREV))

        def make_button(icon):
            btn = QPushButton()
            btn.setIcon(icon)
            btn.setIconSize(QSize(24, 24))
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(BUTTON_STYLE_TRANSPARENT)
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(12)
            glow.setColor(QColor(0, 255, 150, 180))
            glow.setOffset(0, 2)
            btn.setGraphicsEffect(glow)
            return btn

        self.parent.prev_btn = make_button(self.parent.prev_icon)
        self.parent.play_btn = make_button(self.parent.play_icon)
        self.parent.next_btn = make_button(self.parent.next_icon)

        self.parent.controls.addWidget(self.parent.prev_btn)
        self.parent.controls.addSpacerItem(QSpacerItem(12, 1, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.parent.controls.addWidget(self.parent.play_btn)
        self.parent.controls.addSpacerItem(QSpacerItem(12, 1, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.parent.controls.addWidget(self.parent.next_btn)

        controls_holder = QWidget()
        controls_holder.setLayout(self.parent.controls)

        controls_wrapper = QVBoxLayout()
        controls_wrapper.setContentsMargins(0, 0, 0, 0)
        controls_wrapper.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        controls_wrapper.addWidget(controls_holder)

        # Add volume slider with - and + buttons below the play/pause button
        volume_row = QHBoxLayout()
        volume_row.setContentsMargins(0, 0, 0, 0)
        volume_row.setSpacing(8)
        volume_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.parent.vol_down_btn = QPushButton("−")
        self.parent.vol_down_btn.setFixedSize(24, 24)
        self.parent.vol_down_btn.setStyleSheet("""
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
        """)

        self.parent.vol_up_btn = QPushButton("+")
        self.parent.vol_up_btn.setFixedSize(24, 24)
        self.parent.vol_up_btn.setStyleSheet("""
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
        """)

        self.parent.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.volume_slider.setRange(0, 100)
        self.parent.volume_slider.setValue(70)
        self.parent.volume_slider.setFixedWidth(120)
        self.parent.volume_slider.setStyleSheet(get_volume_slider_style(self.color_settings.get_accent_green().name()))
        self.parent.volume_slider.valueChanged.connect(self.parent.change_volume)

        self.parent.vol_down_btn.clicked.connect(lambda: self.parent.volume_slider.setValue(max(0, self.parent.volume_slider.value() - 5)))
        self.parent.vol_up_btn.clicked.connect(lambda: self.parent.volume_slider.setValue(min(100, self.parent.volume_slider.value() + 5)))

        volume_row.addWidget(self.parent.vol_down_btn)
        volume_row.addWidget(self.parent.volume_slider)
        volume_row.addWidget(self.parent.vol_up_btn)

        controls_wrapper.addSpacing(8)
        controls_wrapper.addLayout(volume_row)

        self.parent.main_layout.addLayout(controls_wrapper)
    
    def _setup_volume_controls(self):
        """Setup additional controls (sleep, lyrics, mini player buttons)"""
        # Sleep timer button
        self.parent.sleep_btn = QPushButton("🌙")
        self.parent.sleep_btn.setFixedSize(28, 28)
        self.parent.sleep_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                border: none;
                border-radius: 8px;
                font-size: 11px;
                color: white;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.18);
            }
        """)
        self.parent.sleep_btn.clicked.connect(self.parent.show_sleep_timer_menu)

        # Lyrics button
        self.parent.lyrics_btn = QPushButton('"')
        self.parent.lyrics_btn.setFixedSize(28, 28)
        self.parent.lyrics_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                border: none;
                border-radius: 8px;
                font-weight: 900;
                font-size: 20px;
                color: white;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.18);
            }
        """)
        self.parent.lyrics_btn.clicked.connect(self.parent.show_lyrics_panel)

        # Mini player button
        self.parent.mini_btn = QPushButton()
        mini_icon_path = resource_path('assets/New folder/Alecive-Flatwoken-Apps-Player-Audio-B.512.png')
        if os.path.exists(mini_icon_path):
            self.parent.mini_btn.setIcon(QIcon(mini_icon_path))
        else:
            self.parent.mini_btn.setIcon(QIcon(resource_path(ICON_APP)))  # fallback

        self.parent.mini_btn.setIconSize(QSize(20, 20))
        self.parent.mini_btn.setFixedSize(28, 28)
        self.parent.mini_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.18);
            }
        """)
        self.parent.mini_btn.clicked.connect(self.parent.show_mini_player)

        # Sleep timer
        self.parent.sleep_timer = QTimer()
        self.parent.sleep_timer.timeout.connect(self.parent.stop_playback)
        self.parent.sleep_timer.setSingleShot(True)

        # Create main row with lyrics button, mini player button, and sleep button
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(8)
        bottom_row.addWidget(self.parent.lyrics_btn)
        bottom_row.addWidget(self.parent.mini_btn)
        bottom_row.addStretch(1)
        bottom_row.addWidget(self.parent.sleep_btn)

        self.parent.main_layout.addLayout(bottom_row)
    
    def _compose_layouts(self):
        """Compose final layouts and organize widget hierarchy"""
        self.parent.main_layout_container = QHBoxLayout()
        self.parent.main_layout_container.setContentsMargins(0, 0, 0, 0)
        self.parent.main_layout_container.setSpacing(0)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(self.parent.sidebar)
        sidebar_widget.setFixedWidth(200)

        main_widget = QWidget()
        main_widget.setLayout(self.parent.main_layout)
        main_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.parent.main_layout_container.addWidget(sidebar_widget, 0)
        self.parent.main_layout_container.addWidget(main_widget, 1)

        self.central_widget.setLayout(self.parent.main_layout_container)
    
    def _setup_bottom_shadow(self):
        """Setup bottom shadow element"""
        self.parent.bottom_shadow = QLabel(self.central_widget)
        self.parent.bottom_shadow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.parent.bottom_shadow.setStyleSheet("background: transparent;")
        self.parent.bottom_shadow.lower()

    def position_control_buttons(self):
        """Position brightness and color buttons with proper spacing"""
        if hasattr(self.parent, 'brightness_btn') and hasattr(self.parent, 'color_btn'):
            # Get current brightness button position
            brightness_pos = self.parent.brightness_btn.pos()
            brightness_x = brightness_pos.x()
            brightness_y = brightness_pos.y()
            
            # Position color button directly below brightness button
            color_x = brightness_x  # Same X position as brightness button
            color_y = brightness_y + 28 + 12  # brightness height + 12px spacing
            
            self.parent.color_btn.move(color_x, color_y)
            print(f"Brightness button at: ({brightness_x}, {brightness_y})")
            print(f"Color button positioned at: ({color_x}, {color_y})")


    def position_color_below_brightness(self):
        """Position color button below brightness button with boundary checking"""
        if hasattr(self.parent, 'brightness_btn') and hasattr(self.parent, 'color_btn'):
            # Get brightness button position
            brightness_pos = self.parent.brightness_btn.pos()
            brightness_x = brightness_pos.x()
            brightness_y = brightness_pos.y()
            
            # Get window dimensions for boundary checking
            window_width = self.parent.width()
            window_height = self.parent.height()
            
            print(f"Window size: {window_width}x{window_height}")
            print(f"Brightness button at: ({brightness_x}, {brightness_y})")
            
            # Calculate color button position with boundary checking
            color_x = brightness_x
            color_y = brightness_y + 28 + 12  # brightness height + spacing
            
            # BOUNDARY CHECKS:
            # Ensure color button doesn't go outside window bounds
            if color_x + 28 > window_width:  # Check right edge
                color_x = window_width - 28 - 4  # 4px margin from edge
                
            if color_y + 28 > window_height:  # Check bottom edge
                color_y = window_height - 28 - 4  # 4px margin from bottom
                
            # Ensure minimum margins
            if color_x < 4:  # Check left edge
                color_x = 4
            if color_y < 4:  # Check top edge
                color_y = 4
            
            print(f"Safe position for color button: ({color_x}, {color_y})")
            
            # Move the color button to safe position
            self.parent.color_btn.move(color_x, color_y)
            self.parent.color_btn.show()
            self.parent.color_btn.raise_()
            
            # Verify final position
            final_pos = self.parent.color_btn.pos()
            print(f"Color button final position: ({final_pos.x()}, {final_pos.y()})")

    def fix_color_button_parent(self):
        """Ensure color button has correct parent for manual positioning"""
        if hasattr(self.parent, 'color_btn'):
            # Set parent to the main central widget for free positioning
            self.parent.color_btn.setParent(self.central_widget)
            print("Color button parent set to central widget")
    
    def setup_color_button_icon(self):
        """Load custom color icon from assets folder"""
        from PyQt6.QtGui import QIcon, QPixmap
        from PyQt6.QtCore import QSize
        import os
        
        try:
            # Try to load custom icon from assets folder
            # Adjust the path based on your assets folder structure
            icon_paths = [
                "assets/color_icon.png",      # Primary option
                "assets/icons/color.png",     # Alternative structure
                "assets/palette.png",         # Another option
                "assets/color_palette.svg",   # SVG option
            ]
            
            icon_loaded = False
            
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        # Scale icon to appropriate size
                        scaled_pixmap = pixmap.scaled(
                            20, 20,  # Icon size within the 28x28 button
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        
                        self.parent.color_btn.setIcon(QIcon(scaled_pixmap))
                        self.parent.color_btn.setIconSize(QSize(20, 20))
                        icon_loaded = True
                        print(f"✅ Custom color icon loaded from: {icon_path}")
                        break
            
            if not icon_loaded:
                print("❌ No custom icon found, creating default color palette icon")
                self.create_default_color_icon()
                
        except Exception as e:
            print(f"❌ Error loading custom icon: {e}")
            self.create_default_color_icon()

    def create_default_color_icon(self):
        """Create a default color palette icon if custom icon not found"""
        from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QPen
        from PyQt6.QtCore import Qt, QSize, QRect
        
        # Create custom color palette icon
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a more sophisticated color palette
        colors = [
            QColor(255, 100, 100),  # Red
            QColor(100, 255, 100),  # Green  
            QColor(100, 150, 255),  # Blue
            QColor(255, 200, 100),  # Orange
            QColor(255, 100, 255),  # Magenta
            QColor(100, 255, 255),  # Cyan
        ]
        
        # Draw circular color palette
        center_x, center_y = 12, 12
        radius = 8
        
        for i, color in enumerate(colors):
            angle = (i * 60) * 3.14159 / 180  # Convert to radians
            x = center_x + int(radius * 0.7 * cos(angle)) - 2
            y = center_y + int(radius * 0.7 * sin(angle)) - 2
            
            painter.fillRect(x, y, 4, 4, QBrush(color))
        
        # Draw center circle
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawEllipse(center_x - 2, center_y - 2, 4, 4)
        
        painter.end()
        
        self.parent.color_btn.setIcon(QIcon(pixmap))
        self.parent.color_btn.setIconSize(QSize(20, 20))

    def match_brightness_button_styling(self):
        """Apply the same styling as brightness button to color button"""
        if hasattr(self.parent, 'brightness_btn'):
            # Get brightness button's stylesheet
            brightness_style = self.parent.brightness_btn.styleSheet()
            
            # Apply the same style to color button
            self.parent.color_btn.setStyleSheet(brightness_style)
            print("✅ Color button styling matched to brightness button")






