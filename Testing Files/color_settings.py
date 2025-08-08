"""
Color settings system for SAS Music Player
Allows users to customize the green theme throughout the application
"""

from PyQt6.QtWidgets import QColorDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QDialog, QDialogButtonBox
from PyQt6.QtCore import QSettings, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPalette

class ColorSettings:
    """Manages color settings for the music player"""
    
    def __init__(self):
        self.settings = QSettings('SASMusicPlayer', 'ColorSettings')
        self.auto_color_from_album = self.settings.value('auto_color_from_album', True, bool)
        self.load_colors()
    
    def set_auto_color_from_album(self, enabled):
        """Enable or disable automatic color extraction from album art"""
        self.auto_color_from_album = enabled
        self.settings.setValue('auto_color_from_album', enabled)
    
    def get_auto_color_from_album(self):
        """Get whether auto color from album art is enabled"""
        return self.auto_color_from_album
    
    def load_colors(self):
        """Load saved colors or use defaults"""
        # Primary green color (main theme color)
        self.primary_green = self.settings.value('primary_green', '#1DB954', str)
        self.primary_green = QColor(self.primary_green)
        
        # Hover green color (darker/lighter variant)
        self.hover_green = self.settings.value('hover_green', '#25e06a', str)
        self.hover_green = QColor(self.hover_green)
        
        # Accent green color (for highlights and effects)
        self.accent_green = self.settings.value('accent_green', '#48fa6c', str)
        self.accent_green = QColor(self.accent_green)
    
    def save_colors(self):
        """Save current colors to settings"""
        self.settings.setValue('primary_green', self.primary_green.name())
        self.settings.setValue('hover_green', self.hover_green.name())
        self.settings.setValue('accent_green', self.accent_green.name())
    
    def get_primary_green(self):
        """Get primary green color"""
        return self.primary_green
    
    def get_hover_green(self):
        """Get hover green color"""
        return self.hover_green
    
    def get_accent_green(self):
        """Get accent green color"""
        return self.accent_green
    
    def set_primary_green(self, color):
        """Set primary green color"""
        self.primary_green = color
        self.save_colors()
    
    def set_hover_green(self, color):
        """Set hover green color"""
        self.hover_green = color
        self.save_colors()
    
    def set_accent_green(self, color):
        """Set accent green color"""
        self.accent_green = color
        self.save_colors()

class CustomColorDialog(QColorDialog):
    """Custom color dialog with OK/Cancel buttons and modern styling"""
    
    def __init__(self, initial_color, parent=None):
        super().__init__(parent)
        self.setCurrentColor(initial_color)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setFixedSize(400, 550)
        
        # Connect color changed signal to update OK button
        self.currentColorChanged.connect(self.update_ok_button_color)
        
        # Apply modern styling
        self.setStyleSheet("""
        QColorDialog {
            background-color: #2a2a2a;
            color: white;
            border: 2px solid #444;
            border-radius: 12px;
        }
        QColorDialog QWidget {
            background-color: #2a2a2a;
            color: white;
        }
        QColorDialog QSlider {
            background-color: #444;
            border-radius: 6px;
        }
        QColorDialog QSlider::groove:horizontal {
            background-color: #555;
            border-radius: 6px;
            height: 8px;
        }
        QColorDialog QSlider::handle:horizontal {
            background-color: #1DB954;
            border-radius: 8px;
            width: 16px;
            margin: -4px 0;
        }
        QColorDialog QSpinBox {
            background-color: #444;
            border: 1px solid #666;
            border-radius: 6px;
            padding: 4px;
            color: white;
        }
        QColorDialog QLabel {
            color: #ccc;
            font-weight: bold;
        }
        QColorDialog QPushButton {
            background-color: #444;
            border: 1px solid #666;
            border-radius: 6px;
            padding: 6px 12px;
            color: white;
            font-weight: bold;
        }
        QColorDialog QPushButton:hover {
            background-color: #555;
            border-color: #777;
        }
        QColorDialog QDialogButtonBox {
            background-color: #2a2a2a;
            border-top: 1px solid #444;
            padding: 10px;
        }
        QColorDialog QDialogButtonBox QPushButton {
            min-width: 80px;
            padding: 8px 16px;
            margin: 0 5px;
        }
        """)
        
        # Set initial OK button style
        self.update_ok_button_color(initial_color)

    def update_ok_button_color(self, color):
        """Update OK button color to match selected color"""
        # Find the button box and OK button
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            for button in button_box.buttons():
                if button.text() == "OK":
                    # Calculate text color based on background brightness
                    text_color = 'white' if color.lightness() < 128 else 'black'
                    hover_color = color.lighter(120)
                    
                    button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color.name()};
                        color: {text_color};
                        border: 2px solid {hover_color.name()};
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-width: 80px;
                    }}
                    QPushButton:hover {{
                        background-color: {hover_color.name()};
                        border-color: {color.lighter(140).name()};
                    }}
                    """)
                elif button.text() == "Cancel":
                    button.setStyleSheet("""
                    QPushButton {
                        background-color: #666;
                        color: white;
                        border: 2px solid #888;
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #888;
                        border-color: #aaa;
                    }
                    """)

        


class ColorButton(QPushButton):
    """Color button that responds to single-click"""
    color_selected = pyqtSignal(QColor)

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(32, 32)
        self.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            border: 2px solid #444;
            border-radius: 16px;
        }}
        QPushButton:hover {{
            border: 2px solid #fff;
        }}
        QPushButton:pressed {{
            border: 3px solid #fff;
            transform: scale(0.95);
        }}
        """)
        # Use clicked signal instead of mouseDoubleClickEvent
        self.clicked.connect(self.emit_color_selected)

    def emit_color_selected(self):
        """Emit color selected signal"""
        self.color_selected.emit(QColor(self.color))


class ModernColorPalette(QWidget):
    """Modern color palette with predefined colors"""
    
    color_selected = pyqtSignal(QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the modern color palette"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Quick Colors")
        title.setStyleSheet("""
        QLabel {
            color: #ccc;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        """)
        layout.addWidget(title)

        # Modern color palette
        colors = [
            '#1DB954', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471',
            '#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C',
            '#34495E', '#E67E22', '#8E44AD', '#16A085', '#C0392B', '#2980B9'
        ]

        # Create color grid
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(6)

        for i, color in enumerate(colors):
            color_btn = ColorButton(color)
            color_btn.color_selected.connect(self.on_color_selected)
            grid_layout.addWidget(color_btn)

            # Add line break every 6 colors
            if (i + 1) % 6 == 0:
                layout.addLayout(grid_layout)
                grid_layout = QHBoxLayout()
                grid_layout.setSpacing(6)

        # Add any remaining colors
        if grid_layout.count() > 0:
            layout.addLayout(grid_layout)

    def on_color_selected(self, color):
        """Handle color button click - apply immediately without closing dialog"""
        self.color_selected.emit(color)
        # Don't close the dialog here - let user try multiple colors
    
    def show_custom_color_picker(self):
        """Show the custom color picker dialog"""
        dialog = CustomColorDialog(QColor('#1DB954'), self.parent())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            color = dialog.currentColor()
            if color.isValid():
                self.color_selected.emit(color)

class ColorPickerButton(QPushButton):
    """A button that opens a modern color picker when clicked"""
    color_changed = pyqtSignal(QColor)

    def __init__(self, initial_color, label_text, parent=None):
        super().__init__(parent)
        self.current_color = initial_color
        self.label_text = label_text
        self.setText(label_text)
        self.clicked.connect(self.pick_color)
        self.update_button_color()

    def pick_color(self):
        """Open modern color picker dialog with quick colors at top"""
        dialog = QDialog(self.parent())
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        dialog.setFixedSize(350, 400)  # Made taller to fit all buttons
        dialog.setStyleSheet("""
        QDialog {
            background-color: #2a2a2a;
            color: white;
            border: 2px solid #444;
            border-radius: 12px;
        }
        """)
        
        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Add the modern color palette at the top
        palette = ModernColorPalette(dialog)
        palette.color_selected.connect(lambda color: self.on_color_selected(color, dialog))
        main_layout.addWidget(palette)
        
        # Add separator line
        separator = QLabel()
        separator.setStyleSheet("background-color: #444; height: 1px; margin: 5px 0;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Add the three buttons at the bottom
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)
        
        # Custom Color button
        custom_btn = QPushButton("🎨 Custom Color")
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
        custom_btn.clicked.connect(lambda: self.show_custom_color_picker(dialog))
        button_layout.addWidget(custom_btn)
        
        # Reset to Default button
        reset_btn = QPushButton("🔄 Reset to Default")
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
        reset_btn.clicked.connect(lambda: self.reset_to_default(dialog))
        button_layout.addWidget(reset_btn)
        
        # Done button
        done_btn = QPushButton("✓ Done")
        done_btn.setStyleSheet("""
        QPushButton {
            background-color: #1DB954;
            color: white;
            border: 2px solid #25e06a;
            border-radius: 8px;
            padding: 10px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #25e06a;
            border-color: #48fa6c;
        }
        """)
        done_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(done_btn)
        
        main_layout.addLayout(button_layout)
        
        # Position dialog in center of parent window
        if self.parent():
            parent_center = self.parent().geometry().center()
            dialog_rect = dialog.rect()
            dialog.move(parent_center - dialog_rect.center())
        
        dialog.exec()

    def show_custom_color_picker(self, parent_dialog):
        """Show the custom color picker dialog"""
        custom_dialog = CustomColorDialog(self.current_color, parent_dialog)
        if custom_dialog.exec() == QDialog.DialogCode.Accepted:
            color = custom_dialog.currentColor()
            if color.isValid():
                self.on_color_selected(color, parent_dialog)

    def reset_to_default(self, parent_dialog):
        """Reset to default green color"""
        default_color = QColor('#1DB954')
        self.on_color_selected(default_color, parent_dialog)

    def on_color_selected(self, color, dialog):
        """Handle color selection from any source"""
        self.current_color = color
        self.update_button_color()
        self.color_changed.emit(color)
        
        # Apply changes immediately when color is selected
        if hasattr(self.parent(), 'on_color_changed'):
            self.parent().on_color_changed(color)
        
        # Don't close the dialog automatically - let user click Done

    def update_button_color(self):
        """Update button appearance with current color"""
        try:
            # Calculate text color based on background brightness
            text_color = 'white' if self.current_color.lightness() < 128 else 'black'
            
            self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color.name()};
                color: {text_color};
                border: 2px solid #444;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.current_color.lighter(120).name()};
                border: 2px solid #666;
            }}
            """)
        except Exception as e:
            print(f"Error updating button color: {e}")
            # Fallback to default styling
            self.setStyleSheet("")

    def set_color(self, color):
        """Set color programmatically with validation"""
        if not isinstance(color, QColor) or not color.isValid():
            color = QColor('#1DB954')  # Fallback to default
        
        self.current_color = color
        self.update_button_color()



class ColorSettingsDialog(QDialog):
    """Dialog for customizing player colors"""
    
    colors_changed = pyqtSignal()
    
    def __init__(self, color_settings, parent=None):
        super().__init__(parent)
        self.color_settings = color_settings
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setFixedSize(300, 120)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the color picker UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)  # Reduce spacing between elements
        layout.setContentsMargins(15, 10, 15, 10)  # Tighter margins
        
        # Single color picker
        self.color_picker = ColorPickerButton(
            self.color_settings.get_primary_green(), 
            "Choose Color"
        )
        self.color_picker.color_changed.connect(self.on_color_changed)
        
        layout.addWidget(self.color_picker)
        
        # Reset button
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_to_default)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #888;
            }
        """)
        layout.addWidget(reset_btn)
        
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #232323;
                color: white;
            }
        """)
    
    def on_color_changed(self, color):
        """Handle color change - set all three colors and apply immediately"""
        # Set primary color as the chosen color
        self.color_settings.set_primary_green(color)
        
        # Set hover color as a lighter version of the chosen color
        hover_color = color.lighter(120) # 20% lighter
        self.color_settings.set_hover_green(hover_color)
        
        # Set accent color as an even lighter version for highlights
        accent_color = color.lighter(140) # 40% lighter
        self.color_settings.set_accent_green(accent_color)
        
        # Apply changes immediately with live preview
        self.colors_changed.emit()
        
        # Update the color picker button immediately
        self.color_picker.set_color(color)

    
    def reset_to_default(self):
        """Reset colors to default green theme"""
        default_primary = QColor('#1DB954')
        
        self.color_picker.set_color(default_primary)
        
        # Set all three colors based on the default
        self.color_settings.set_primary_green(default_primary)
        hover_color = default_primary.lighter(120)
        self.color_settings.set_hover_green(hover_color)
        accent_color = default_primary.lighter(140)
        self.color_settings.set_accent_green(accent_color)
        # Apply changes immediately when reset is clicked
        self.colors_changed.emit() 