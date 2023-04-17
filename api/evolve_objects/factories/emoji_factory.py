from __future__ import annotations
from typing import Type
import requests
import pathlib
from PIL.Image import Image
from PIL.Image import open as image_open
import shutil
import random

EMOJI_IMAGE_URL = 'https://api.github.com/repos/iamcal/emoji-data/contents/img-apple-64'
IMAGE_DIRECTORY = './.tmp/emojis/'

class EmojiData():
    name: str
    download_url: str
    def __init__(self, name: str, download_url: str):
        self.name = name
        self.download_url = download_url

class EmojiFactory():
    _instance: EmojiFactory
    _emoji_data: list[EmojiData] = []
    path: pathlib.Path = pathlib.Path(IMAGE_DIRECTORY)

    @classmethod
    def instance(cls: Type[EmojiFactory]) -> EmojiFactory:
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._setup_directory()
        self._get_emoji_links()

    def _setup_directory(self) -> None:
        if not self.path.exists():
            self.path.mkdir(parents=True)

    def get_emoji_image(self, data: EmojiData) -> Image:
        if (self.path / data.name).is_file():
            return image_open(self.path/data.name)
        res = requests.get(data.download_url)
        with open(self.path/data.name, 'wb') as f:
            f.write(res.content)
        return image_open(self.path/data.name).convert('RGBA')

    def get_random_emoji(self) -> EmojiData:
        return random.choice(self._emoji_data)

    def destroy(self) -> None:
        if self.path.exists():
            shutil.rmtree(self.path)

    def _get_emoji_links(self) -> None:
        response = requests.get(EMOJI_IMAGE_URL)
        if response.status_code == 200:
            for d in response.json():
                self._emoji_data.append(EmojiData(d['name'], d['download_url']))
        else:
            raise Exception("An error has orrcued while getting GitHub information: " + str(response.status_code))

