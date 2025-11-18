from google import genai
from google.genai import types
from google.genai import Client
from gameModel import GameModel
from typing import Union
from settings import loadSettings

settings = loadSettings()

class Chat:
    def __init__(self, config: types.GenerateContentConfig, client: Client=None):
        self.history: list[Union[types.GenerateContentResponse, types.Content]] = []
        self.model = settings.gemini_model or "gemini-flash-latest"
        self.config = config
        self.client = client

    def send_message(self, content: types.Part) -> list[types.Content]:
        if content:
            if isinstance(content, str): content = types.Part(text=content)
            self.history.append(
                types.Content(
                    role="user",
                    parts=[content],
                ),
            )
        if self.client:
            history = []
            for res in self.history:
                if isinstance(res, types.GenerateContentResponse):
                    history.append(res.candidates[0].content)
                else:
                    history.append(res)

            res = self.client.models.generate_content(
                model = self.model,
                config = self.config,
                contents = history,
            )
            self.history.append(res)
            return res
        else:
            raise RuntimeError("Client not set.")