import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QThread
from game import GameWindow
from generate_dmt import DMTEditor
from about import About
from settings import Settings, loadSettings
from style import *
from button import Button

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dungeon Master")
        self.setGeometry(100, 100, 1366, 768)

        self.main_widget = QWidget()
        self.layout = QVBoxLayout()

        pixmap = QPixmap("assets/icon.png")
        pixmap = pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label = AutoResizingLabel(pixmap)
        self.icon_label.setMaximumSize(500, 500)
        self.icon_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.icon_layout = QHBoxLayout()
        self.icon_layout.addWidget(self.icon_label)
        self.icon_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.layout.addLayout(self.icon_layout)


        self.button_layout = QVBoxLayout()

        self.play_button = Button("New Game")
        self.play_button.clicked.connect(self.play)
        self.button_layout.addWidget(self.play_button)

        self.load_dms_button = Button("Load a saved session")
        self.load_dms_button.clicked.connect(self.load_dms)
        self.button_layout.addWidget(self.load_dms_button)

        self.load_dmt_button = Button("Load a DMT")
        self.load_dmt_button.clicked.connect(self.load_dmt)
        self.button_layout.addWidget(self.load_dmt_button)

        self.dmt_editor_button = Button("DMT Editor")
        self.dmt_editor_button.clicked.connect(self.dmt_editor)
        self.button_layout.addWidget(self.dmt_editor_button)

        self.about_button = Button("About")
        self.about_button.clicked.connect(self.about)
        self.button_layout.addWidget(self.about_button)

        self.settings_button = Button("Settings")
        self.settings_button.clicked.connect(self.settings)
        self.button_layout.addWidget(self.settings_button)

        self.exit_button = Button("Exit")
        self.exit_button.clicked.connect(self.close)
        self.button_layout.addWidget(self.exit_button)

        self.button_layout.addStretch(1)

        self.bottom = QWidget()
        self.bottom_layout = QHBoxLayout(self.bottom)
        self.bottom_layout.addLayout(self.button_layout)
        self.bottom_layout.addStretch(1)

        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.layout.addWidget(self.bottom)

        init_window(self)

        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)


    def play(self):
        if not loadSettings():
            QMessageBox.critical(self,
                "Settings Error",
                "Settings not configured!\nBefore starting the game, go back and hit the 'Settings' option, then enter your API keys."
            )
            return
        self.game_window = GameWindow(self)
        self.game_window.show()
        self.hide()

    def load_dms(self):
        if not loadSettings():
            QMessageBox.critical(self,
                "Settings Error",
                "Settings not configured!\nBefore starting the game, go back and hit the 'Settings' option, then enter your API keys."
            )
            return
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load DMS", "", "Dungeon Master Session Files (*.dms)", options=options)
        self.game_window = GameWindow(self, file=file_name)
        self.game_window.show()
        self.hide()

    def load_dmt(self):
        if not loadSettings():
            QMessageBox.critical(self,
                "Settings Error",
                "Settings not configured!\nBefore starting the game, go back and hit the 'Settings' option, then enter your API keys."
            )
            return
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load DMT", "", "Dungeon Master World Files (*.dmt)", options=options)
        self.game_window = GameWindow(self, file=file_name)
        self.game_window.show()
        self.hide()

    def dmt_editor(self):
        self.dmt_window = DMTEditor(self)
        self.dmt_window.show()
        self.hide()

    def about(self):
        self.about_window = About()
        self.about_window.show()

    def settings(self):
        self.settings_window = Settings()
        self.settings_window.show()

    def resizeEvent(self, event):
        self.background.setGeometry(self.rect())
        super().resizeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setDesktopFileName("dev.uukelele.dungeonmaster")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())