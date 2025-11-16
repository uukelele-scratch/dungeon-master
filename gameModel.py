from pydantic import BaseModel

class GameModel(BaseModel):
    class InventoryItem(BaseModel):
        name: str
        options: list[str]

    class GameChoice(BaseModel):
        text: str

    class Stats(BaseModel):
        STRENGTH: int
        AGILITY: int
        INTELLIGENCE: int
        CHARISMA: int

    class Quest(BaseModel):
        title: str
        description: str
        completed_percentage: int

    chapterText: str

    inventory: list[InventoryItem]

    health: int
    maxHealth: int

    imagePrompt: str

    choices: list[GameChoice]

    stats: Stats

    currentQuest: Quest
