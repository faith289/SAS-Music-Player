# sleep_timer_dialog.py - Sleep Timer Dialog for SAS Music Player
# Extracted sleep timer dialog functionality from main application

import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
)
from PyQt6.QtGui import QRegion, QPainterPath
from PyQt6.QtCore import Qt, QTimer

class SleepTimerDialog(QDialog):
    """Sleep Timer Dialog for setting and managing sleep timers"""
    
    def __init__(self, parent=None, timer_active=False, remaining_min=0, remaining_sec=0):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        
        if not timer_active:
            self.setFixedSize(240, 120)
            self.setStyleSheet("font-size: 12px; background: #232323; border-radius: 16px;\n"
                             "border: 3px solid #444;")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 20)  # Extra bottom margin
        else:
            self.setFixedSize(240, 90)
            self.setStyleSheet("font-size: 12px; background: #232323; border-radius: 14px;\n"
                             "border: 2px solid #444;")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8)

        self.setWindowTitle("")
        self.use_end_of_song = False
        self.stop_clicked = False
        self.timer_active = timer_active
        self.parent = parent

        button_style = """
            QPushButton {
                border: 2px solid #888;
                border-radius: 7px;
                background: #292929;
                color: white;
                font-size: 12px;
                padding: 2px 12px;
                min-width: 0px;
                min-height: 18px;
                max-height: 18px;
            }
            QPushButton:hover {
                background: #333;
                border: 2px solid #aaa;
            }
        """

        plusminus_style = """
            QPushButton {
                border: 2px solid #888;
                border-radius: 7px;
                background: #292929;
                color: white;
                font-size: 14px;
                padding: 0px 6px;
                min-width: 16px;
                min-height: 16px;
                max-width: 16px;
                max-height: 16px;
            }
            QPushButton:hover {
                background: #333;
                border: 2px solid #aaa;
            }
        """

        if timer_active:
            total_seconds = remaining_min * 60 + remaining_sec
            self.adjusted_seconds = total_seconds

            time_row = QHBoxLayout()
            time_row.setSpacing(6)  # Add space between -, timer, +

            self.minus_btn = QPushButton("-", self)
            self.minus_btn.setFixedSize(20, 20)
            self.minus_btn.setStyleSheet(plusminus_style)

            self.time_display = QLabel(self.format_time(self.adjusted_seconds), self)
            self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.time_display.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent; border: none; padding-left:2px; padding-right:2px;")

            self.plus_btn = QPushButton("+", self)
            self.plus_btn.setFixedSize(20, 20)
            self.plus_btn.setStyleSheet(plusminus_style)

            time_row.addStretch(1)
            time_row.addWidget(self.minus_btn)
            time_row.addSpacing(1)
            time_row.addWidget(self.time_display)
            time_row.addSpacing(1)
            time_row.addWidget(self.plus_btn)
            time_row.addStretch(1)

            layout.addSpacing(8)
            layout.addLayout(time_row)
            layout.addSpacing(4)

            btn_row = QHBoxLayout()
            self.stop_btn = QPushButton("Stop", self)
            self.stop_btn.setStyleSheet(button_style)
            self.done_btn = QPushButton("Done", self)
            self.done_btn.setStyleSheet(button_style)

            btn_row.addWidget(self.stop_btn)
            btn_row.addWidget(self.done_btn)
            layout.addLayout(btn_row)

            self.minus_btn.clicked.connect(self.decrease_time)
            self.plus_btn.clicked.connect(self.increase_time)
            self.stop_btn.clicked.connect(self.stop_timer)
            self.done_btn.clicked.connect(lambda: self.parent.fade_out_dialog(self) if hasattr(self.parent, 'fade_out_dialog') else self.accept())

            self.update_timer = QTimer(self)
            self.update_timer.timeout.connect(self.update_remaining_time)
            self.update_timer.start(1000)

        else:
            self.slider = QSlider(Qt.Orientation.Horizontal, self)
            self.slider.setRange(5, 120)
            self.slider.setValue(30)
            self.slider.setTickInterval(5)
            self.slider.setSingleStep(1)
            self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.slider.setStyleSheet("""
                QSlider { border: none; background: transparent; min-height: 12px; }
                QSlider::groove:horizontal { border: none; height: 6px; background: #333; border-radius: 3px; }
                QSlider::handle:horizontal { background: #fff; border: none; width: 12px; height: 12px; margin: -3px 0; border-radius: 6px; }
                QSlider::sub-page:horizontal { background: #48fa6c; border-radius: 3px; }
                QSlider::add-page:horizontal { background: #232323; border-radius: 3px; }
            """)

            self.label = QLabel(f"Sleep in: {self.slider.value()} min", self)
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.label.setStyleSheet("background: transparent; border: none; color: white; font-size: 14px; font-weight: bold;")

            layout.addSpacing(4)
            layout.addWidget(self.label)
            layout.addSpacing(2)
            layout.addWidget(self.slider)
            layout.addSpacing(4)

            btn_row = QHBoxLayout()
            self.start_btn = QPushButton("Start", self)
            self.start_btn.setStyleSheet(button_style)
            self.end_btn = QPushButton("End of Song", self)
            self.end_btn.setStyleSheet(button_style)
            self.cancel_btn = QPushButton("Cancel", self)
            self.cancel_btn.setStyleSheet(button_style)

            btn_row.addWidget(self.start_btn)
            btn_row.addWidget(self.end_btn)
            btn_row.addWidget(self.cancel_btn)
            layout.addLayout(btn_row)

            self.start_btn.clicked.connect(lambda: self.parent.fade_out_dialog(self) if hasattr(self.parent, 'fade_out_dialog') else self.accept())
            def handle_cancel():
                self.result_code = 'cancelled'  # Set explicit cancel result
                if hasattr(self.parent, 'fade_out_dialog'):
                    self.parent.fade_out_dialog(self)
                else:
                    self.reject()

            self.start_btn.clicked.connect(lambda: self.parent.fade_out_dialog(self) if hasattr(self.parent, 'fade_out_dialog') else self.accept())
            self.cancel_btn.clicked.connect(handle_cancel)


            self.end_btn.clicked.connect(self.end_of_song)

            self.slider.valueChanged.connect(self.update_label)

    def update_label(self, val):
        """Update slider value label"""
        self.label.setText(f"Sleep in: {val} min")

    def get_minutes(self):
        """Get timer minutes"""
        if hasattr(self, 'slider'):
            return self.slider.value()
        return max(1, self.adjusted_seconds // 60)

    def end_of_song(self):
        """Handle end of song timer option"""
        self.use_end_of_song = True
        if hasattr(self.parent, 'fade_out_dialog'):
            self.parent.fade_out_dialog(self)
        else:
            self.accept()

    def stop_timer(self):
        """Stop the active timer"""
        self.stop_clicked = True
        # Instead of self.reject(), fade out first
        if hasattr(self.parent, 'fade_out_dialog'):
            self.parent.fade_out_dialog(self)
        else:
            self.reject()

    def increase_time(self):
        """Increase timer time by 1 minute"""
        self.adjusted_seconds = min(120*60, self.adjusted_seconds + 60)
        # Directly update the main timer
        if self.parent:
            self.parent.sleep_timer.start(self.adjusted_seconds * 1000)
        self.time_display.setText(self.format_time(self.adjusted_seconds))

    def decrease_time(self):
        """Decrease timer time by 1 minute"""
        self.adjusted_seconds = max(0, self.adjusted_seconds - 60)
        if self.parent:
            self.parent.sleep_timer.start(self.adjusted_seconds * 1000)
        self.time_display.setText(self.format_time(self.adjusted_seconds))

    def format_time(self, total_seconds):
        """Format seconds into MM:SS format"""
        m, s = divmod(int(total_seconds), 60)
        return f"{m:02}:{s:02}"

    def update_remaining_time(self):
        """Update remaining time display for active timer"""
        if self.timer_active and self.parent and self.parent.sleep_timer.isActive():
            remaining_ms = self.parent.sleep_timer.remainingTime()
            self.adjusted_seconds = max(0, remaining_ms // 1000)
            self.time_display.setText(self.format_time(self.adjusted_seconds))
        else:
            self.update_timer.stop()

    def showEvent(self, event):
        """Handle show event with rounded corners"""
        super().showEvent(event)
        # Enforce rounded corners with a mask
        path = QPainterPath()
        if not self.timer_active:
            path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        else:
            path.addRoundedRect(0, 0, self.width(), self.height(), 14, 14)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
