from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore import QPropertyAnimation, QRect, QTimer
from PyQt5.QtGui import QFont
import random

class Button(QPushButton):
    def __init__(self, text, *args, **kwargs):
        self.full_text = "> " + text.lower()
        super().__init__("", *args, **kwargs)
        self.setFixedWidth(350)
        self.setFont(QFont("Lucida Console"))
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.original_position = self.geometry()
        self.setStyleSheet("""

            Button {
                background-color: rgba(0,0,0,0.2);
                color: white;
                border: rgba(0,0,0,0);
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                text-align: left;
            }

            Button:hover {
                background-color:rgba(0,0,0,0.3);
                padding-left: 10px;
            }

        """)
        self.start_animation()
    
    def enterEvent(self, event):
        self.original_position = self.geometry()
        self.animate_move(10)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_move(0)
        super().leaveEvent(event)

    def animate_move(self, offset):
        self.animation.stop()
        self.animation.setDuration(100)
        start = self.geometry()
        end = QRect(self.original_position.x() + offset, self.original_position.y(), self.original_position.width(), self.original_position.height())
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.start()

    def start_animation(self):
        self.current_index = 0
        self.done = ""
        self.setText("")
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_text)
        self.timer.start(random.randint(100,300))

        self.cursor_on = True
        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self.toggle_cursor)
        self.cursor_timer.start(500)
        
    def update_text(self):
        if self.current_index < len(self.full_text):
            self.done += self.full_text[self.current_index]
            self.setText(self.done + ("_" if self.cursor_on else ""))
            self.current_index += 1
            self.timer.start(random.randint(100, 300))
        else:
            self.timer.stop()

    def toggle_cursor(self):
        self.cursor_on = not self.cursor_on
        self.setText(self.done + ("_" if self.cursor_on else ""))
