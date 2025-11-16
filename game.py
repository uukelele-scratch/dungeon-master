import sys
import json
import time
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QProgressBar,
    QLabel,
    QHBoxLayout,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QFileDialog,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor, QFont, QPixmap, QImage, QTextOption, QIcon
from PIL import Image
from style import init_window, AutoResizingLabel
from settings import loadSettings
from google import genai
from google.genai import types
from pydantic import BaseModel
import pickle
import together, base64
from io import BytesIO
from generate_dmt import system_instruction
from chat import Chat
from gameModel import GameModel

# Worker thread classes
class GenerateThread(QThread):
    result_ready = pyqtSignal(GameModel)

    def __init__(self, chat, message: types.Part):
        super().__init__()
        self.chat = chat
        self.message = message

    def run(self):
        res = self.chat.send_message(content=self.message)
        data = res.parsed
        self.result_ready.emit(data)

class ImageThread(QThread):
    result_ready = pyqtSignal(object)

    def __init__(self, client: together.client.Client, imagePrompt):
        super().__init__()
        self.image_prompt = imagePrompt
        self.client = client
    
    def run(self):
        runs = 0
        res = None
        while runs < 3: # After 3 attempts, give up.
            try:
                runs += 1
                res = self.client.images.generate(
                    prompt = self.image_prompt,
                    model = "black-forest-labs/FLUX.1-schnell-Free",
                    width = 1024,
                    height = 768,
                    steps = 2,
                    n = 1,
                    response_format = "b64_json",
                )
                break
            except:
                pass
        
        if not runs:
            res

        image = Image.open(BytesIO(base64.b64decode(res.data[0].b64_json)))
        self.result_ready.emit(image)


class GameWindow(QMainWindow):
    def __init__(self, main_window: QMainWindow, file=None):
        super().__init__()
        self.setWindowTitle("Dungeon Master")
        self.setGeometry(100, 100, 1366, 768)
        self.message_history = []

        self.file = file

        self.main_window = main_window

        self.main_widget = QWidget()
        self.splitter = QSplitter(Qt.Horizontal)

        self.game_layout = QVBoxLayout()

        self.game_widget = QWidget()
        self.game_widget.setLayout(self.game_layout)

        # Font for the game text
        self.font = QFont()
        self.font.setPointSize(12)

        self.inventory_layout = QVBoxLayout()
        self.inventory_label = QLabel("Inventory:")
        self.inventory_list = QListWidget()
        self.inventory_list.setFont(self.font)
        self.inventory_label.setFont(self.font)
        self.inventory_layout.addWidget(self.inventory_label)
        self.inventory_layout.addWidget(self.inventory_list)

        self.quest_widget = QWidget()
        self.quest_widget.setFont(self.font)
        self.quest_title = QLabel("No Quest")
        self.quest_description = QTextEdit("")
        self.quest_description.setReadOnly(True)
        self.quest_description.acceptRichText()
        self.quest_description.setMarkdown("Accept a quest from an NPC, and it will show up here!")
        self.quest_progress = QProgressBar()
        self.quest_progress.setValue(0)
        self.quest_progress.setMaximum(100)

        self.quest_layout = QVBoxLayout()
        self.quest_layout.addWidget(self.quest_title)
        self.quest_layout.addWidget(self.quest_description)
        self.quest_layout.addWidget(self.quest_progress)

        self.quest_widget.setLayout(self.quest_layout)
        self.inventory_layout.addWidget(self.quest_widget)

        self.save_button = QPushButton("Save Game Session")
        self.save_button.clicked.connect(self.save_game)
        self.inventory_layout.addWidget(self.save_button)

        self.autosave_location = None
        self.autosave_toggle = QCheckBox()
        self.autosave_toggle.setTristate(False)
        self.autosave_toggle.setText("Autosave")
        self.autosave_toggle.setDisabled(True)
        self.autosave_toggle.setToolTip("Save your session before you can enable autosave.")
        self.inventory_layout.addWidget(self.autosave_toggle)

        self.inventory_widget = QWidget()
        self.inventory_widget.setLayout(self.inventory_layout)

        self.game_widget.setFixedWidth(int(self.width() * 0.6))
        self.inventory_widget.setFixedWidth(int(self.width() * 0.4))

        self.splitter.setStretchFactor(0, 6)
        self.splitter.setStretchFactor(1, 4)
        self.splitter.addWidget(self.game_widget)
        self.splitter.addWidget(self.inventory_widget)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.splitter)

        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        # Progress bar for health

        self.health_bar = QProgressBar()
        self.health_bar.setMaximum(100)
        self.health_bar.setFormat("Health: %v/%m")
        self.game_layout.addWidget(self.health_bar)
        # self.health_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.health_bar.setFixedHeight(20)

        # Labels for stats
        self.stats_layout = QHBoxLayout()
        self.stats_labels = {}
        for stat in ["Strength", "Agility", "Intelligence", "Charisma"]:
            label = QLabel(f"{stat}: 0")
            label.setFont(self.font)
            # label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            label.setFixedHeight(30)
            self.stats_labels[stat.lower()] = label
            self.stats_layout.addWidget(label)

        self.status_layout = QVBoxLayout()
        self.status_layout.addWidget(self.health_bar)
        self.status_layout.addLayout(self.stats_layout)

        self.status_widget = QWidget()
        self.status_widget.setLayout(self.status_layout)
        # self.status_widget.setFixedHeight(50)

        self.game_layout.addWidget(self.status_widget)

        # Response box for the chapter text
        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setAcceptRichText(True)
        self.response_box.setFont(self.font)
        self.response_box.setMaximumHeight(int(self.height() * 0.4))
        self.response_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.response_box.setWordWrapMode(QTextOption.WordWrap)
        self.response_box.textChanged.connect(self.adjust_response_box_height)

        self.chapter_layout = QVBoxLayout()
        self.chapter_layout.addWidget(self.response_box)

        # Image display
        self.image_label = AutoResizingLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(400, 300)
        self.image_label.setText("Loading Image...")
        # self.image_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.image_layout = QHBoxLayout()
        self.image_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.image_layout.addWidget(self.image_label) # Center the image with two spacers on either side.
        self.image_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.chapter_layout.addLayout(self.image_layout)
        self.game_layout.addLayout(self.chapter_layout)

        # Choice buttons
        self.choice_buttons = []
        self.buttons_layout = QHBoxLayout()

        for idx in range(4):
            button = QPushButton()
            button.clicked.connect(self.handle_choice)
            button.setFont(self.font)
            self.choice_buttons.append(button)
            self.buttons_layout.addWidget(button)

        self.game_layout.addLayout(self.buttons_layout)

        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        init_window(self)

        # Initialize game
        self.init_game()

    def set_window_icon(self):
        pixmap = QPixmap("assets/icon.png")
        self.setWindowIcon(QIcon(pixmap))
        pixmap = QPixmap("assets/background.jpeg")
        self.background = QLabel(self)
        self.background.setPixmap(pixmap)
        self.background.setGeometry(self.rect())
        self.background.setScaledContents(True)
        self.background.lower()

    def adjust_response_box_height(self):
        doc_height = self.response_box.document().size().height() - 50
        max_height = self.response_box.maximumHeight()
        new_height = int(min(doc_height, max_height, 20))
        self.response_box.setFixedHeight(new_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.response_box.setMaximumHeight(int(self.height() * 0.4))
        self.adjust_response_box_height()
    
        # Calculate the scaling factor based on the new window size
        width_factor = self.width() / 1920
        height_factor = self.height() / 1080
        scale_factor = min(width_factor, height_factor)
    
        # Calculate the new font size based on the scale factor
        new_font_size = max(8, int(8 * scale_factor))  # Ensure a minimum font size of 8
    
        # Set the new font size
        font = QFont()
        font.setPointSize(new_font_size)
        for button in self.choice_buttons:
            button.setFont(font)
        self.health_bar.setFont(font)
        for label in self.stats_labels.values():
            label.setFont(font)


        game_width = int(self.width() * 0.6)
        self.game_widget.setFixedWidth(game_width)
        
        self.image_label.setFixedSize(int(400 * width_factor), int(300 * height_factor))
        self.display_image()

        self.background.setGeometry(self.rect())

    def init_game(self):
        self.settings = loadSettings()
        self.genaiClient = genai.Client(api_key=self.settings.gemini_api_key)
        self.togetherClient = together.Together(api_key=self.settings.together_api_key)
        
        if self.file:
            self.load_game()
        else:
            self.chat = Chat(
                config = types.GenerateContentConfig(
                    temperature = 2.0,
                    response_mime_type = "application/json",
                    response_schema = GameModel,
                    system_instruction = system_instruction,
                ),
                client = self.genaiClient,
            )
            # Start the generate thread
            self.start_generate_thread("...")

    def start_generate_thread(self, message=None):
        self.response_box.setMarkdown("# Loading...")
        self.resizeEvent(None)
        if not hasattr(self.chat, "client"):
            self.chat.client = self.genaiClient
        self.generate_thread = GenerateThread(self.chat, message)
        self.generate_thread.result_ready.connect(self.update_game)
        self.generate_thread.start()

    def regenerate_response(self, message):
        self.response_box.setMarkdown("## Hold on, something went wrong.\n\n### We're trying to fix it, please wait a moment.\n`Technical Details: {message}`")
        message = types.Part(text=f"Please regenerate your response. What you need to fix: {message}")
        self.start_generate_thread(message)
    
    def update_game(self, game: GameModel):
        
        if len(game.choices) == 0:
            self.regenerate_response(f"Choices are empty")
            return
        
        if self.autosave_toggle.isEnabled() and self.autosave_location:
            self.save_game(self.autosave_location)

        # Update the chapter text with markdown
        chapter_text = game.chapterText.replace("\\n", "\n")
        self.response_box.setMarkdown(chapter_text)
        self.response_box.moveCursor(QTextCursor.Start)
        self.resizeEvent(None)

        # Update the health bar
        self.health_bar.setMaximum(game.maxHealth)
        self.health_bar.setValue(game.health)


        # Update the stats labels
        stats = game.stats
        for stat_name, value in vars(stats).items():
            key = stat_name.lower()
            if key in self.stats_labels:
                self.stats_labels[key].setText(f"{stat_name.capitalize()}: {value}")

        # Update the inventory display
        self.inventory_list.clear()
        inventory = game.inventory
        for item in inventory:
            item_listwidget = QListWidgetItem(self.inventory_list)
            item_widget = QWidget()
            item_widget.setFixedHeight(60)
            layout = QHBoxLayout()
            label = QLabel(item.name)
            label.setProperty("labelType", "inventory")
            label_layout = QHBoxLayout()
            label_layout.addWidget(label)
            label_layout.addStretch()
            layout.addLayout(label_layout)

            button_layout = QHBoxLayout()
            button_layout.addStretch()
            for option in item.options:
                button = QPushButton(option)
                button.setProperty("buttonType", "inventory")
                button.setFixedHeight(30)
                button.clicked.connect(lambda _, item_name=item.name, option=option: self.use_item(item_name, option))
                button_layout.addWidget(button)

            layout.addLayout(button_layout)
            item_widget.setLayout(layout)
            item_listwidget.setSizeHint(item_widget.sizeHint())
            self.inventory_list.setItemWidget(item_listwidget, item_widget)

        # Update the Quest Display
        self.quest_title.setText(game.currentQuest.title)
        self.quest_description.setMarkdown(game.currentQuest.description)
        self.quest_progress.setValue(game.currentQuest.completed_percentage)

        # Update the choice buttons
        choices = game.choices
        for idx, button in enumerate(self.choice_buttons):
            try:
                choice_text = choices[idx].text
            except:
                choice_text = ""

            if choice_text:
                button.setText(choice_text)
                button.setEnabled(True)
                button.show()
            else:
                button.hide()
        
        self.image_prompt = game.imagePrompt
        if self.image_prompt:
            self.start_image_thread(self.image_prompt)
    
    def start_image_thread(self, image_prompt):
        self.image_label.setText("Loading Image...")
        self.image_thread = ImageThread(self.togetherClient, image_prompt)
        self.image_thread.result_ready.connect(self.display_image)
        self.image = None
        self.image_thread.start()

    def display_image(self, pil_image=None):
        if not hasattr(self, "image") and not pil_image:
            return
        
        if self.image == None and not pil_image:
            return
        
        if not pil_image and hasattr(self, "image") and self.image:
            pil_image = self.image

        if not hasattr(self, "image"):
            self.image = pil_image
        
        self.image_label.setText("")  # Clear the text



        pil_image = pil_image.convert("RGBA")
        data = pil_image.tobytes("raw", "RGBA")
        qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        scaled = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.setToolTip(self.image_prompt)

    def use_item(self, item_name, option):
        # Add the choice to the message history
        choice = f"Use item '{item_name}' - Option '{option}'"
        message = types.Part(
            text = choice
        )
        self.response_box.setMarkdown("# Loading...")
        for button in self.choice_buttons:
            button.setEnabled(False)

        self.start_generate_thread(message)
        
    def handle_choice(self):
        sender = self.sender()
        choice_text = sender.text()

        # Add the choice to the message history
        message = types.Part(
            text = f"I have chosen: {choice_text}",
        )

        # Display loading message
        self.response_box.setMarkdown("# Loading...")

        # Disable buttons while loading
        for button in self.choice_buttons:
            button.setEnabled(False)

        # Start the generate thread
        self.start_generate_thread(message)

    def save_game(self, saveLocation=None):
        if not saveLocation and not self.autosave_location:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "Save Game", "", "Dungeon Master Session Files (*.dms)", options=options)
            if file_name:
                clean_chat = self.chat
                clean_chat.client = None # Remove the client to avoid storing sensitive information in the client.
                with open(file_name, "wb") as file:
                    pickle.dump(clean_chat, file)
            self.autosave_location = file_name
            self.autosave_toggle.setDisabled(False)
            self.autosave_toggle.setToolTip("")
        else:
            self.autosave_toggle.setText("Autosave - Saving...")
            with open(saveLocation or self.autosave_location, "wb") as file:
                pickle.dump(self.chat, file)
            self.autosave_toggle.setText("Autosave - Saved!")

    def load_game(self):
        if self.file:
            self.autosave_location = self.file
            with open(self.file, "rb") as file:
                self.chat = pickle.load(file)

            self.chat.client = self.genaiClient

            if isinstance(self.chat.history[-1], types.Content): # Last message was user-sent
                self.start_generate_thread()
            else:
                self.update_game(self.chat.history[-1].parsed) # Update the game based on the model response.

    def closeEvent(self, event):
        # Ensure threads are properly terminated
        if hasattr(self, 'generate_thread') and self.generate_thread.isRunning():
            self.generate_thread.quit()
            self.generate_thread.wait()

        self.main_window.show()
        event.accept()

if __name__ == "__main__":
    print("This file is not to be run as a standalone program.")
    sys.exit(1)
