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
    QLineEdit,
    QComboBox,
)
from style import init_window
import pickle, os

gemini_models = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]

class SettingsObject:
    def __init__(self, gemini_api_key: str="", together_api_key: str="", gemini_model: str=""):
        self.gemini_api_key: str = gemini_api_key
        self.together_api_key: str = together_api_key
        self.gemini_model: str = gemini_model or "gemini-flash-latest"

def loadSettings() -> SettingsObject | None:
    settings_path = os.path.join(os.path.dirname(__file__), "settings.dmx")
    if os.path.exists(settings_path):
        try:
            pkl = pickle.load(open(settings_path, 'rb'))
            if isinstance(pkl, SettingsObject):
                return pkl
            else:
                raise TypeError("Invalid settings type.")
        except Exception as e:
            return None
    return None

class Settings(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dungeon Master - Settings")
        self.setGeometry(500, 500, 600, 200)
        self.setFixedSize(600, 200)
        init_window(self)
        self.main_layout = QVBoxLayout()
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        self.title_label = QLabel("Settings")
        self.field_layout = QVBoxLayout()
        self.main_layout.addLayout(self.field_layout)

        self.settings_loaded = False

        self.gemini_field = QHBoxLayout()
        self.gemini_label = QLabel("Gemini API Key")
        self.gemini_field.addWidget(self.gemini_label)
        self.gemini_input = QLineEdit()
        self.gemini_input.setEchoMode(QLineEdit.Password)
        self.gemini_field.addWidget(self.gemini_input)
        self.field_layout.addLayout(self.gemini_field)

        self.together_field = QHBoxLayout()
        self.together_label = QLabel("together.ai API Key")
        self.together_field.addWidget(self.together_label)
        self.together_input = QLineEdit()
        self.together_input.setEchoMode(QLineEdit.Password)
        self.together_field.addWidget(self.together_input)
        self.field_layout.addLayout(self.together_field)

        self.gemini_model_field = QHBoxLayout()
        self.gemini_model_label = QLabel("Gemini Model")
        self.gemini_model_field.addWidget(self.gemini_model_label)
        self.gemini_model_dropdown = QComboBox()
        self.gemini_model_dropdown.addItems(gemini_models)
        self.gemini_model_field.addWidget(self.gemini_model_dropdown)
        self.field_layout.addLayout(self.gemini_model_field)

        self.gemini_input.textEdited.connect(self.updateSettings)
        self.together_input.textEdited.connect(self.updateSettings)
        self.gemini_model_dropdown.currentTextChanged.connect(self.updateSettings)

        self.autoLoadSettings()
        self.settings_loaded = True

    def autoLoadSettings(self):
        settings = loadSettings()
        if settings:
            self.gemini_input.setText(settings.gemini_api_key)
            self.together_input.setText(settings.together_api_key)
            self.gemini_model_dropdown.setCurrentText(settings.gemini_model)

    def updateSettings(self):
        if self.settings_loaded == False: return
        settings = SettingsObject(
            gemini_api_key = self.gemini_input.text(),
            together_api_key = self.together_input.text(),
            gemini_model = self.gemini_model_dropdown.currentText(),
        )
        settings_path = os.path.join(os.path.dirname(__file__), "settings.dmx")
        pickle.dump(settings, open(settings_path, 'wb'))


if __name__ == '__main__':
    print("This file is not to be run as a standalone program.")
    sys.exit(1)