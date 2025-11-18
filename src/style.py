# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QLabel, QMainWindow, QApplication, QSizePolicy
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt

text = QFont("Helvetica")

stylesheet = """
            * {
                font-family: "Helvetica";
            }

            QPushButton {
                background-color: rgba(0,0,0,0.2);
                color: white;
                border: rgba(0,0,0,0);
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                text-align: left;
            }

            QPushButton:hover {
                background-color:rgba(0,0,0,0.3);
            }

            Button {
                font-family: "Lucida Console", monospace, sans-serif;
                background-color: rgba(0,0,0,0.2);
                color: white;
                border: rgba(0,0,0,0);
                border-radius: 10px;
                padding: 10px;
                font-size: 32px;
                text-align: left;
            }

            Button:hover {
                background-color:rgba(0,0,0,0.3);
                padding-left: 10px;
            }

            QLabel {
                background: rgba(0,0,0,0.2);
                color: white;
                border: rgba(0,0,0,0);
                border-radius: 10px;
                padding:10px;
                text-align:center;
            }

            QTextEdit {
                background:rgba(0,0,0,0.5);
                color:white;
                border: rgba(0,0,0,0);
                border-radius:10px;
                padding:10px;
            }

            QListWidget {
                background:rgba(0,0,0,0.4);
                color:white;
                border: rgba(0,0,0,0);
                border-radius:10px;
                padding:10px;
            }

            QListWidget::item {
                background:rgba(0,0,0,0.3);
                color:white;
                border: rgba(0,0,0,0);
                border-radius:10px;
                padding:0px;
            }

            QLabel[labelType="inventory"] {
                padding:0px;
                background: rgba(0,0,0,0);
            }

            QPushButton[buttonType="inventory"] {
                padding:0px;
            }

            QSplitter::handle {
                background: rgba(0,0,0,0);
            }

            QProgressBar {
                text-align: center;
                background-color: rgba(0,0,0,0.5);
                border: 3px solid white;
                border-radius: 10px;
                color: white;
            }

            QProgressBar::chunk {
                background-color: #4287f511;
                border-radius: 10px;
                text-align: center;
            }

            QCheckBox {
                color:white;
            }
"""


image_friendly = """
QLabel {
    padding:0;
    background:rgba(0,0,0,0);
}
"""

def init_window(win: QMainWindow, autosize: bool = True):
    if autosize:
        geom = QApplication.primaryScreen().availableGeometry()
        width, height = geom.width(), geom.height()
        res = (1024, 640)
        scale = 0.8
        scaled_w, scaled_h = int(scale*width), int(scale*height)

        # if width >= 1920 and height >= 1080:
        #     res = (1920, 1080)
        # elif width >= 1366 and height >= 768:
        #     res = (1366, 768)

        w = max(scaled_w, res[0])
        h = max(scaled_h, res[1])


        x = geom.x() + (width - w) // 2
        y = geom.y() + (height - h) // 2
        
        win.setGeometry(x, y, w, h)
    

    icon_path = "assets/icon.png"
    background_path = "assets/background.jpeg"

    pixmap = QPixmap(icon_path)
    win.setWindowIcon(QIcon(pixmap))

    pixmap = QPixmap(background_path)
    win.background = QLabel(win)
    win.background.setPixmap(pixmap)
    win.background.setGeometry(win.rect())
    win.background.setScaledContents(True)
    win.background.lower()
    if hasattr(win, "image_label"):
        win.image_label.setStyleSheet(image_friendly)
    if hasattr(win, "icon_label"):
        win.icon_label.setStyleSheet(image_friendly)
    win.background.setStyleSheet(image_friendly)
    win.setStyleSheet(stylesheet)

class AutoResizingLabel(QLabel):
    def __init__(self, pixmap=None):
        super().__init__()
        self._original_pixmap = pixmap
        self.setScaledContents(False)
        if pixmap:
            self.setPixmap(pixmap)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setPixmap(self, pixmap):
        self._original_pixmap = pixmap
        super().setPixmap(pixmap)
    
    def resizeEvent(self, event):
        if not self._original_pixmap: return super().resizeEvent(event)
        scaled_pixmap = self._original_pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        super().setPixmap(scaled_pixmap)
        super().resizeEvent(event)


def validate_file(file):
    if type(file) == "BytesIO":
        file.seek(0)


if __name__ == '__main__':
    print("This file is not to be run as a standalone program.")
    sys.exit(1)
