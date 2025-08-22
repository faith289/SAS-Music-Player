# color_dialog_manager.py - Color Dialog Management System for SAS Music Player
# Extracted color management logic from main application

import os
import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QWidget
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from color_settings import CustomColorDialog

class ColorDialogManager:
    """Handles all color dialog creation and management for the SAS Music Player"""
    
    def __init__(self, parent):
        """Initialize ColorDialogManager with reference to parent SASPlayer instance"""
        self.parent = parent
        self.color_settings = parent.color_settings
    
    def show_color_settings(self):
        """Show color settings dialog - directly open quick color picker"""
        # Create the quick color picker dialog directly
        dialog = QDialog(self.parent)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        dialog.setFixedSize(350, 450)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: white;
                border: 2px solid #444;
                border-radius: 12px;
            }
        """)

        # START WITH DIALOG INVISIBLE
        dialog.setWindowOpacity(0.0)

        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Add auto-color toggle at the top
        auto_color_row = QHBoxLayout()
        auto_color_row.setContentsMargins(0, 0, 0, 5)

        auto_color_label = QLabel("🎨 Auto-extract from album art:")
        auto_color_label.setStyleSheet("color: #ccc; font-size: 12px; font-weight: 500;")

        auto_color_toggle = QPushButton("ON" if self.color_settings.get_auto_color_from_album() else "OFF")
        auto_color_toggle.setFixedSize(60, 28)

        def update_auto_color_toggle_style():
            if self.color_settings.get_auto_color_from_album():
                auto_color_toggle.setText("ON")
                auto_color_toggle.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.color_settings.get_primary_green().name()};
                        color: white;
                        border: none;
                        border-radius: 12px;
                        font-weight: bold;
                        font-size: 10px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.color_settings.get_hover_green().name()};
                    }}
                """)
            else:
                auto_color_toggle.setText("OFF")
                auto_color_toggle.setStyleSheet("""
                    QPushButton {
                        background-color: #666;
                        color: white;
                        border: none;
                        border-radius: 12px;
                        font-weight: bold;
                        font-size: 10px;
                    }
                    QPushButton:hover {
                        background-color: #888;
                    }
                """)

        # CREATE QUICK COLOR OPTIONS (before defining toggle function)
        quick_colors_container = QWidget()
        quick_colors_container.setStyleSheet("QWidget { background-color: rgba(255,255,255,0.02); border-radius: 8px; padding: 8px; }")
        quick_colors_layout = QVBoxLayout(quick_colors_container)
        quick_colors_layout.setContentsMargins(12, 8, 12, 12)
        quick_colors_layout.setSpacing(6)

        # Quick colors label
        quick_colors_label = QLabel("⚡ Quick Colors:")
        quick_colors_label.setStyleSheet("""color: #e0e0e0; font-size: 13px; font-weight: bold; margin: 0px; padding: 0px 0px 4px 0px; """)
        quick_colors_layout.addWidget(quick_colors_label)

        # Create color grid with multiple rows
        color_grid = QGridLayout()
        color_grid.setSpacing(6)
        color_grid.setContentsMargins(4, 4, 4, 4)
        color_grid.setRowStretch(0, 0)
        color_grid.setRowStretch(1, 0)
        color_grid.setRowStretch(2, 0)

        # Define your color palette (multiple rows of colors)
        quick_color_sets = [
            # Row 1 - Greens and Blues
            [("#4CAF50", "Default Green"), ("#2E7D32", "Dark Green"), ("#81C784", "Light Green"),
             ("#2196F3", "Blue"), ("#1976D2", "Dark Blue"), ("#64B5F6", "Light Blue")],
            # Row 2 - Purples and Reds
            [("#9C27B0", "Purple"), ("#7B1FA2", "Dark Purple"), ("#BA68C8", "Light Purple"),
             ("#F44336", "Red"), ("#D32F2F", "Dark Red"), ("#EF5350", "Light Red")],
            # Row 3 - Oranges and Others
            [("#FF9800", "Orange"), ("#F57C00", "Dark Orange"), ("#FFB74D", "Light Orange"),
             ("#607D8B", "Blue Gray"), ("#455A64", "Dark Gray"), ("#90A4AE", "Light Gray")]
        ]

        # Function to update quick colors state based on auto-extract setting
        def update_quick_colors_state():
            is_auto_enabled = self.color_settings.get_auto_color_from_album()
            quick_colors_container.setEnabled(not is_auto_enabled)
            opacity = "0.4" if is_auto_enabled else "1.0"
            quick_colors_container.setStyleSheet(f"QWidget {{ opacity: {opacity}; }}")

        # Create color buttons in grid layout
        color_buttons = []
        for row_idx, color_row in enumerate(quick_color_sets):
            for col_idx, (color_hex, color_name) in enumerate(color_row):
                color_btn = QPushButton()
                color_btn.setFixedSize(34, 34)
                color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color_hex};
                        border: 2px solid #444;
                        border-radius: 16px;
                    }}
                    QPushButton:hover {{
                        border-color: #888;
                        border-width: 3px;
                    }}
                    QPushButton:pressed {{
                        border-color: #fff;
                        border-width: 4px;
                    }}
                """)
                color_btn.setToolTip(f"{color_name} - {color_hex}")

                # Connect to color selection (disable auto-extract when manual color is selected)
                def make_color_handler(hex_color):
                    def handle_color_selection():
                        # Disable auto-extract when manual color is selected
                        self.color_settings.set_auto_color_from_album(False)
                        update_auto_color_toggle_style()
                        update_quick_colors_state()
                        # Apply the selected color
                        self.on_manual_color_selected(QColor(hex_color))
                    return handle_color_selection

                color_btn.clicked.connect(make_color_handler(color_hex))
                color_grid.addWidget(color_btn, row_idx, col_idx)
                color_buttons.append(color_btn)

        quick_colors_layout.addLayout(color_grid)

        def toggle_auto_color():
            current = self.color_settings.get_auto_color_from_album()
            self.color_settings.set_auto_color_from_album(not current)
            update_auto_color_toggle_style()
            update_quick_colors_state()

            # If turning on and we have album art, immediately apply it
            if not current and hasattr(self.parent, 'album_original_image') and self.parent.album_original_image is not None:
                try:
                    # IMPORTANT: Temporarily store blur state to restore it after color update
                    dialog_blur_active = hasattr(self.parent, '_blur_overlay_widget') and self.parent._blur_overlay_widget is not None
                    blur_overlay_widget = getattr(self.parent, '_blur_overlay_widget', None)
                    blur_overlay = getattr(self.parent, '_blur_overlay', None)

                    # Apply the album art colors
                    self.parent.set_album_art(self.parent.album_original_image)

                    # RESTORE the blur overlay if it was active
                    if dialog_blur_active and blur_overlay_widget is not None:
                        self.parent._blur_overlay_widget = blur_overlay_widget
                        self.parent._blur_overlay = blur_overlay

                        # Make sure the blur overlay is visible and properly positioned
                        self.parent._blur_overlay_widget.setGeometry(self.parent.rect())
                        self.parent._blur_overlay_widget.show()
                        self.parent._blur_overlay_widget.raise_()

                        # Restore the click-blocking overlay
                        if blur_overlay:
                            blur_overlay.popup = dialog
                            blur_overlay.setGeometry(self.parent.rect())
                            blur_overlay.show()

                except Exception as e:
                    print(f"Error applying auto-extracted color: {e}")
                    # Fall back to default behavior - just update toggle style
                    pass

        # CONNECT AND LAYOUT THE AUTO-COLOR TOGGLE
        update_auto_color_toggle_style()
        auto_color_toggle.clicked.connect(toggle_auto_color)

        auto_color_row.addWidget(auto_color_label)
        auto_color_row.addStretch()
        auto_color_row.addWidget(auto_color_toggle)

        main_layout.addLayout(auto_color_row)

        # Add separator
        separator = QLabel()
        separator.setStyleSheet("background-color: #444; height: 1px; margin: 2px 0;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)

        # Add quick colors container
        main_layout.addWidget(quick_colors_container)

        # Initialize quick colors state
        update_quick_colors_state()

        # Add separator line before buttons
        separator2 = QLabel()
        separator2.setStyleSheet("background-color: #555; height: 1px; margin: 8px 4px;")
        separator2.setFixedHeight(1)
        main_layout.addWidget(separator2)

        # Add the three buttons at the bottom
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 4, 0, 0)

        # Custom Color button
        custom_btn = QPushButton("🎨 Custom Color")
        custom_btn.setFixedHeight(38)
        custom_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border: 2px solid #666;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555;
                border-color: #777;
            }
        """)
        custom_btn.clicked.connect(lambda: self.show_direct_custom_color_picker(dialog))
        button_layout.addWidget(custom_btn)

        # Reset to Default button
        reset_btn = QPushButton("🔄 Reset to Default")
        reset_btn.setFixedHeight(38)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: 2px solid #888;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #888;
                border-color: #aaa;
            }
        """)
        reset_btn.clicked.connect(lambda: self.reset_to_default_direct(dialog))
        button_layout.addWidget(reset_btn)

        # Done button with dynamic colors
        done_btn = QPushButton("✓ Done")
        def update_done_button_style():
            primary_color = self.color_settings.get_primary_green()
            hover_color = self.color_settings.get_hover_green()
            done_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {primary_color.name()};
                    color: white;
                    border: 2px solid {hover_color.name()};
                    border-radius: 8px;
                    padding: 10px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {hover_color.name()};
                    border-color: {primary_color.lighter(160).name()};
                }}
            """)

        # Set initial style and store reference for updates
        update_done_button_style()
        self.parent._current_color_dialog_done_btn = update_done_button_style

        # MODIFY DONE BUTTON TO FADE OUT BEFORE CLOSING
        def close_with_fade():
            self.parent.fade_out_dialog(dialog)

        done_btn.clicked.connect(close_with_fade)
        button_layout.addWidget(done_btn)

        main_layout.addLayout(button_layout)

        # Position dialog in center of parent window
        parent_center = self.parent.geometry().center()
        dialog_rect = dialog.rect()
        dialog.move(parent_center - dialog_rect.center())

        # Show with blur effect
        self.parent.set_blur(True, popup=dialog)

        # SHOW DIALOG AND FADE IN
        dialog.show()
        self.parent.fade_in_dialog(dialog)

        result = dialog.exec()
        self.parent.set_blur(False)

        # Clean up reference
        if hasattr(self.parent, '_current_color_dialog_done_btn'):
            delattr(self.parent, '_current_color_dialog_done_btn')

        if hasattr(self.parent, '_blur_overlay'):
            self.parent._blur_overlay.hide()

    def on_direct_color_selected(self, color):
        """Handle direct color selection from quick palette"""
        # Set primary color as the chosen color
        self.color_settings.set_primary_green(color)

        # Set hover color as a lighter version of the chosen color
        hover_color = color.lighter(120)  # 20% lighter
        self.color_settings.set_hover_green(hover_color)

        # Set accent color as an even lighter version for highlights
        accent_color = color.lighter(140)  # 40% lighter
        self.color_settings.set_accent_green(accent_color)

        # Apply changes immediately with force refresh
        self.parent.update_colors()

        # Force immediate update of all background elements
        self.parent.update_green_overlay_color()
        self.parent.update_bottom_shadow()

        # Force repaint of all widgets
        self.parent.repaint()

        # Update Done button color if it exists in the current dialog
        if hasattr(self.parent, '_current_color_dialog_done_btn'):
            self.parent._current_color_dialog_done_btn()

    def on_manual_color_selected(self, color):
        """Handle manual color selection (disables auto-color)"""
        # Disable auto-color when user manually selects a color
        self.color_settings.set_auto_color_from_album(False)

        # Apply the manually selected color
        self.on_direct_color_selected(color)
        self.parent.update_playlist_colors()  # Update playlist colors after manual selection

    def show_direct_custom_color_picker(self, parent_dialog):
        """Show the custom color picker dialog directly"""
        # Disable auto-color when using custom color picker
        self.color_settings.set_auto_color_from_album(False)

        custom_dialog = CustomColorDialog(self.color_settings.get_primary_green(), parent_dialog)
        if custom_dialog.exec() == QDialog.DialogCode.Accepted:
            color = custom_dialog.currentColor()
            if color.isValid():
                self.on_direct_color_selected(color)

    def reset_to_default_direct(self, parent_dialog):
        """Reset to default green color directly"""
        # Disable auto-color when resetting to default
        self.color_settings.set_auto_color_from_album(False)
        default_color = QColor('#1DB954')
        self.on_direct_color_selected(default_color)
