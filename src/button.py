from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore import QPropertyAnimation, QRect, QTimer, pyqtProperty
from PyQt5.QtGui import QFont, QFontDatabase
import random

class Button(QPushButton):
    def __init__(self, text, *args, **kwargs):
        self.full_text = "> " + text.lower()
        super().__init__("", *args, **kwargs)
        self.setFixedWidth(350)
        self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self._anim_offset = 0
        self.animation = QPropertyAnimation(self, b"anim_offset")
        # self.original_position = self.geometry()
        self.update_style()
        self.start_animation()

    @pyqtProperty(int)
    def anim_offset(self):
        return self._anim_offset

    @anim_offset.setter
    def anim_offset(self, value):
        self._anim_offset = value
        self.update_style()

    def update_style(self):
        padding = 10 + self._anim_offset
        self.setStyleSheet(f"""

            Button {{
                background-color: rgba(0,0,0,0.2);
                color: white;
                border: rgba(0,0,0,0);
                border-radius: 10px;
                padding: 10px;
                margin-left: {padding}px;
                font-size: 16px;
                text-align: left;
            }}

            Button:hover {{
                background-color:rgba(0,0,0,0.3);
                /* padding-left: 10px; */
            }}

        """)
    
    def enterEvent(self, event):
        # self.original_position = self.geometry()
        self.animate_move(10)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_move(0)
        super().leaveEvent(event)

    def animate_move(self, offset):
        self.animation.stop()
        self.animation.setDuration(100)
        # start = self.geometry()
        # end = QRect(self.original_position.x() + offset, self.original_position.y(), self.original_position.width(), self.original_position.height())
        self.animation.setStartValue(self._anim_offset)
        self.animation.setEndValue(offset)
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
