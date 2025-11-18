import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from style import init_window

class About(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dungeon Master - About")
        self.setGeometry(500, 500, 600, 400)
        self.setFixedSize(600, 400)
        init_window(self)
        url = "https://uukelele.is-a.dev/dungeon_master"
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(url))
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.browser)
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

if __name__ == '__main__':
    print("This file is not to be run as a standalone program.")
    sys.exit(1)