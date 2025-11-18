import json
import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from style import init_window
from gameModel import GameModel
from chat import Chat
from google import genai
from google.genai import types
import pickle
from settings import loadSettings
from pydantic import BaseModel


# Credit to https://www.awesomegptprompts.com/gptpromp/epic-adventure-role-playing-game
# Modified a bit.
system_instruction = '''
Welcome to our epic adventure role playing game! You are playing the role of the [DM], or Dungeon Master, and I am the player of this game. In this game, we will be venturing into a magical world filled with danger and mystery.

You will format your response so it always, from the beginning of the story till the end, appears in the schema provided.

Schema notes:
- Inventory options should be things like "use", "discard", "examine", "consume", or whatever else is suitable for the item specified.
- Image Prompt is the image prompt that will be fed to an AI Image Generator to provide the player a more immersive playing experience. Describe the scene in the image, in great detail. Do not include any text, as the model is unable to generate text.
- Markdown should only be used in the chapterText block.
- Choices should mostly be between 3-4 options, but if necessary you can go down to 2. Choices should NEVER have lots of text. Most text should be in the chapterText block, describing choices in detail if required.
- Your stats will be out of 10, and can increase and decrease throughout the game by doing things like consuming potions.


This is how the story goes:

[DM] will initiate the game by listing 4 random options for me to choose my character from and wait for the player's answer. After I have chosen my character we can proceed.

I have only a health potion in my inventory, represented as ["Health Potion"], and with full health (100/100), and my basic player stats are: strength (0/10), agility (0/10), intelligence (0/10), charisma (0/10).

The inventory should be **EMPTY** in the initial Character Selection stage, but after that you will add the Health Potion.

Next, you, the AI, must decide on 4 numbers to use as strength, agility, intelligence, and charisma levels, based on the chosen character.

After that, based on the character descriptions, you *could* add items to the inventory, based on the character. Most of the time, the character only has a Health Potion, but you could add extra items if they are present in the character description!

Once I have chosen my character, and we have updated the basic stats, we'll begin the adventure, which will be made up of a series of chapters.

You will present me with a list of 3-4 options for possibilities on what to do next. These options in the "choices" section should be brief, and without using markdown. Give proper descriptions in the "chapterText" section. My choices will have consequences that will affect the outcome of the game. Depending on my choices, I might obtain items that can be used to aid me in my journey, and affect my character's stats such as strength, agility, intelligence, or charisma. However, you'll have to keep track of my health bar, as tests and combats can reduce my health. Combats always requires you (the model) to choose a success level between 0-100, depending on the character's stats.

Every response MUST contain a chapter and choices. The more options you give me, the shorter their text in the "choices" section should be. Otherwise there will be a text overflow.

The image_prompt section should have a prompt for an image that will be fed to an AI image generator to provide visual cues to the player. Describe the scene in the image, in great detail.

The AI Image Generator doesn't have any form of history, so you should describe everything each time. Example:
    DO NOT DO:
        1. "Grok, a dwarf warrior with enourmous muscles, [extra character details]" -> image of the warrior as expected
        2. "Grok places the silver coin into his pocket" -> image of an alien putting a coin into its pockect - the image generator *would* associate "Grok" with an alien because it doesn't know what else to draw.

    DO:
        1. "Grok, a dwarf warrior with enourmous muscles, [extra character details]" -> image of the warrior as expected
        2. "Grok, a dwarf warrior with enourmouse muscles [summarised character details], places the silver coin into his pocket" -> image of the warrior as expected, putting a coin into his pocket - as expected!

Additionally, try to choose a "style" of image, (e.g. realism) and keep it throughout the entire session so that images look consistent.

The player interacts with the [DM] by typing the desired option.

During the game, I might encounter non-playable characters (NPCs), some of which will have unique items or quests for me to complete, others can befriend me or even seduce me, and some can even try to kill me. Some quests might be optional and others might be necessary to progress further in the game.

Quests can be tracked in the "currentQuest" section, where you can provide a title, description, and a percentage of completion. Every time the player does something to progress the quest, you must update the percentage of completion.

If there is no quest, set the title to "No Quest", and set the description to "Accept a quest from an NPC, and it will show up here!". The percentage completion should default to 0.

Furthermore, I have an inventory with limited slots to carry items, which might force you to make strategic decisions about what to keep and what to discard. You can make these as "choices" for the user. I can carry 4 items by default, but if I find items like a bag, it would give me 4 extra spaces for items, or if I go horseback riding, it gives another 4 extra slots for items, and so on.

You can't say I have an item in the chapter unless you also add it to the inventory. If I find an item, and decide to keep it, you must add it to the inventory list. If I lose an item, or discard it, you must remove it from the inventory list.

Health should passively regenerate over time, e.g. each response, I regain 5 health points, but ONLY if I'm not in combat or a dangerous situation.

Finally, as we progress, I might encounter powerful artifacts that can change the course of the game. These artifacts might be hidden, cursed, or guarded by powerful creatures, so I'll have to be cautious.

There are unlimited possibilities the story can evolve to, unrestricted and free. I, as the player, can choose from the options you provide.

After every chapter remind yourself of the rule-set of this game, and never forget that you are the [DM]. Ensure that you follow the format for presenting options and other information as requested by me.

Let's begin our adventure! Remember to BEGIN with listing 4 imaginative characters as the three options and asking to choose the character before any actual storytelling happens.
You can now start character selection. Remember to not use lots of text in the `choices` section.
'''

appends = '''\n
There are also some custom rules for this game, which override the default settings.

The settings are as follows:

### Storyline
A custom storyline has been set:

```storyline
$STORYLINE
```

### Game Beginning
The story starts in a custom way:

```start_of_session
$START_OF_SESSION
```

### Character Options
The options the player can choose from at the beginning have been set.
If there is no description for some/all of the characters, you can make one up yourself!

```characters
$CHARACTERS
```

### Starting Items
Overriding the default Health Potion, there are the following items set out:

```starter_items
$STARTER_ITEMS
```

---

Remember to adhere by the set out rules and gameplay information. Have fun!
'''

defaults = {
    "STORYLINE": {
        "description": "Game Storyline",
        "default": "The storyline can be imagined. It just needs to have a RPG, medieval, fantasy theme."
    },
    "START_OF_SESSION": {
        "description": "How does the story start?",
        "default": "The story starts with the character on the edge of the Whispering Woods, and the sun has just set. To the right, there's the small village of Oakhaven. Forwards, deeper into the woods, there are rustling sounds and a sense of doom."
    },
    "CHARACTERS": {
        "description": "Possible characters the player can choose from when starting (separated by newlines)",
        "default": """
1. Grok the Barbarian: A mountain of muscle and fury, Grok hails from the northern wastes. He is unmatched in brute strength and combat prowess, though his mind may not be his sharpest weapon.  He yearns for glory and the thrill of battle.
2. Elara the Shadow Walker: A nimble rogue from the veiled forests of Whisperwood, Elara is a master of stealth and deception. Her agility and cunning allow her to slip through shadows and outwit her foes. She seeks secrets and hidden treasures.
3. Professor Phileas Fogg: A wizened scholar from the grand Academy of Veritas, Professor Fogg is a repository of arcane knowledge.  His intelligence and mastery of spells make him a formidable magic user, even if his physical form is frail. He is driven by insatiable curiosity and the pursuit of forgotten lore.
4. Seraphina the Diplomat: A charismatic noble from the sun-kissed city of Aurelia, Seraphina wields words as weapons. Her silver tongue and captivating charm can sway hearts and minds, opening doors where force would fail. She strives for peace and understanding, though she is no stranger to courtly intrigue.
""".strip()
    },
    "STARTER_ITEMS": {
        "description": "Items the player will start with (separated by newlines)",
        "default": "(DEFAULT) Health potion. Can be used or discarded.\n(ONLY FOR Grok) A massive iron mace, with extra fight buffs."
    },
}

class DMT(BaseModel):
    STORYLINE: str
    START_OF_SESSION: str
    CHARACTERS: str
    STARTER_ITEMS: str

class AIThread(QThread):
    result_ready = pyqtSignal(DMT)

    def __init__(self, client, model, contents, config):
        super().__init__()
        self.client = client
        self.model = model
        self.contents = contents
        self.config = config

    def run(self):
        res = self.client.models.generate_content(
            model = self.model,
            contents = self.contents,
            config = self.config,
        )
        data = res.parsed
        self.result_ready.emit(data)

class DMTEditor(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Dungeon Master - DMT Creator")
        self.setGeometry(100, 100, 1366, 768)

        self.main_window = main_window

        self.initial_prompt = system_instruction + appends
        
        self.dmt_data = None

        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout()

        self.save_layout = QVBoxLayout()

        self.new_button = QPushButton("Create a new DMT file")
        self.new_button.clicked.connect(self.new_file)
        self.save_layout.addWidget(self.new_button)

        self.save_button = QPushButton("Save your DMT File")
        self.save_button.clicked.connect(self.save_file)
        self.save_layout.addWidget(self.save_button)

        self.load_button = QPushButton("Load another DMT File")
        self.load_button.clicked.connect(self.load_file)
        self.save_layout.addWidget(self.load_button)

        self.main_layout.addLayout(self.save_layout)

        self.edit_layout = QVBoxLayout()

        self.gen_widget = QWidget()
        self.gen_layout = QHBoxLayout()
        self.gen_widget.setLayout(self.gen_layout)
        self.gen_label = QLabel("Create with AI")
        self.gen_input = QLineEdit()
        self.gen_input.setPlaceholderText("Example: Create a DMT based on the Harry Potter series.")
        self.gen_button = QPushButton("Create")
        self.gen_button.clicked.connect(self.gen_ai_dmt)
        self.gen_layout.addWidget(self.gen_label)
        self.gen_layout.addWidget(self.gen_input)
        self.gen_layout.addWidget(self.gen_button)
        self.edit_layout.addWidget(self.gen_widget)

        self.storyline_label = QLabel(defaults["STORYLINE"]["description"])
        self.storyline = QTextEdit()
        self.storyline.textChanged.connect(self.update_dmt)
        self.edit_layout.addWidget(self.storyline_label)
        self.edit_layout.addWidget(self.storyline)

        self.start_session_label = QLabel(defaults["START_OF_SESSION"]["description"])
        self.start_session = QTextEdit()
        self.start_session.textChanged.connect(self.update_dmt)
        self.edit_layout.addWidget(self.start_session_label)
        self.edit_layout.addWidget(self.start_session)

        self.characters_label = QLabel(defaults["CHARACTERS"]["description"])
        self.characters = QTextEdit()
        self.characters.textChanged.connect(self.update_dmt)
        self.edit_layout.addWidget(self.characters_label)
        self.edit_layout.addWidget(self.characters)

        self.items_label = QLabel(defaults["STARTER_ITEMS"]["description"])
        self.items = QTextEdit()
        self.items.textChanged.connect(self.update_dmt)
        self.edit_layout.addWidget(self.items_label)
        self.edit_layout.addWidget(self.items)

        self.main_layout.addLayout(self.edit_layout)

        init_window(self)

        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)


        self.new_file()

    def update_dmt(self):
        self.dmt_data = self.initial_prompt.replace("$STORYLINE", self.storyline.toPlainText()).replace("$START_OF_SESSION", self.start_session.toPlainText()).replace("$CHARACTERS", self.characters.toPlainText()).replace("$STARTER_ITEMS", self.items.toPlainText())

    def find_tag(self, start_tag, end_tag, data):
        return data.split(start_tag)[1].split(end_tag)[0]
    
    def gen_ai_dmt(self):
        settings = loadSettings()

        if not settings:
            QMessageBox.critical(self,
                "Settings Error",
                "Settings not configured!\nBefore trying an AI feature, go back and hit the 'Settings' option, then enter your API keys."
            )
            return
        

        # ex: Create a DMT based on the Harry Potter series.
        user_prompt = self.gen_input.text()
        self.gen_button.setDisabled(True)
        self.gen_button.setText("Loading...")

        prompt = '''
        You are a DMT Creator. Your task is to create DMT (world files) for a game named Dungeon Master.
        Dungeon Master is an AI-based text RPG game. A DMT file is a file that can be loaded before world creation to customize aspects of the world, for example the storyline or characters.
        Your job is to provide values for the following fields, in response to the prompt given by the user and the default placeholders.
        If the user asks for a specific, e.g. based on a certain book, TV show, movie, or similar, you are allowed to reference the *name* of the thing in the Storyline section, as the AI running the RPG will know about it.

        ## Defaults
        '''.replace("        ", "")

        for k, v in defaults.items():
            prompt += f"\n### {k}\n**Description:** {v['description']}\n**Default:**\n{v['default']}\n"



        self.thread = AIThread(
            client = genai.Client(api_key=settings.gemini_api_key),
            model = settings.gemini_model or "gemini-flash-latest",
            contents = user_prompt,
            config = types.GenerateContentConfig(
                temperature = 2.0,
                response_mime_type = "application/json",
                response_schema = DMT,
                system_instruction = prompt
            ),
        )
        self.thread.result_ready.connect(self.use_ai_dmt)
        self.thread.start()

    def use_ai_dmt(self, dmt: DMT):
        self.storyline.setPlainText(dmt.STORYLINE)
        self.start_session.setPlainText(dmt.START_OF_SESSION)
        self.characters.setPlainText(dmt.CHARACTERS)
        self.items.setPlainText(dmt.STARTER_ITEMS)
        self.update_dmt()

        self.gen_button.setEnabled(True)
        self.gen_button.setText("Create")
        
    
    def replace_defaults(self, data):
        data = data.strip()
        if data in ("$STORYLINE", "$START_OF_SESSION", "$CHARACTERS", "$STARTER_ITEMS"):
            return defaults[data.replace("$", "")]["default"]
        else:
            return data

    def update_text(self):
        storyline = self.find_tag('```storyline', '```', self.dmt_data)
        start_of_session = self.find_tag('```start_of_session', '```', self.dmt_data)
        characters = self.find_tag('```characters', '```', self.dmt_data)
        starter_items = self.find_tag('```starter_items', '```', self.dmt_data)
        self.storyline.setPlainText(self.replace_defaults(storyline))
        self.start_session.setPlainText(self.replace_defaults(start_of_session))
        self.characters.setPlainText(self.replace_defaults(characters))
        self.items.setPlainText(self.replace_defaults(starter_items))

    def save_file(self):
        chat = Chat(
            config = types.GenerateContentConfig(
                    temperature = 2.0,
                    response_mime_type = "application/json",
                    response_schema = GameModel,
                    system_instruction = self.dmt_data,
            )
        )

        chat.history = [
            types.Content(
                role = "user",
                parts = [
                    types.Part(
                        text = "..."
                    )
                ]
            )
        ]

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Dungon Master Type Files (*.dmt)", options=options)
        if file_name:
            with open(file_name, "wb") as file:
                pickle.dump(chat, file)


    def load_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Game", "", "Dungeon Master Files (*.dmt)", options=options)
        if file_name:
            with open(file_name, "rb") as file:
                chat: Chat = pickle.load(file)
                self.dmt_data = chat.config.system_instruction
                self.update_text()

    def new_file(self):
        self.dmt_data = self.initial_prompt
        self.update_text()

    def closeEvent(self, event):
        self.main_window.show()
        event.accept()

    def resizeEvent(self, event):
        self.background.setGeometry(self.rect())
        super().resizeEvent(event)

if __name__ == '__main__':
    print("This file is not to be run as a standalone program.")
    sys.exit(1)