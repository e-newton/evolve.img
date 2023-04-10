from __future__ import annotations
from evolve_objects.object import BaseObject
from evolve_objects.rectangle import clamp
from evolve_objects.factories.emoji_factory import EmojiFactory
from evolve_objects.factories.emoji_factory import EmojiData
import random
from PIL.Image import Image, NEAREST
from multiprocessing.synchronize import Lock as LockBase

class Emoji(BaseObject):
    scale = 1
    rotation = 0
    x: int
    y: int
    data: EmojiData
    _disk_lock: LockBase
    _emoji_image = Image
    _image: Image
    def __init__(self,
                 create_new: bool,
                 image: Image,
                 _: list[tuple[int, int, int]]) -> None:
        if create_new:
            self.data = EmojiFactory.instance().get_random_emoji()
            self._emoji_image = EmojiFactory.instance().get_emoji_image(self.data)
            self.x = random.randint(0, image.width - 1)
            self.y = random.randint(0, image.height - 1)
            self.rotation = random.randint(0, 360)
            self.scale = (image.width / self._emoji_image.width) / 10
        self._image = image


    def deviate(self, percent: float, max_width: int, max_height: int) -> BaseObject:
        assert(isinstance(self._emoji_image, Image))
        widthRange = int(percent * max_width)
        heightRange = int(percent * max_height)
        rotationRange = int((percent / 10) * 360)
        scaleRange = (max_width / self._emoji_image.width) * percent
        x = clamp(self.x + random.randint(-widthRange, widthRange), 0, max_width - 1)
        y = clamp(self.y + random.randint(-heightRange, heightRange), 0, max_height - 1)
        rotation = (self.rotation + random.randint(-rotationRange, rotationRange)) % 360
        scale = max(0.001, self.scale + ((random.random() - 0.5) * 2) * scaleRange)
        new_emoji = Emoji(False, self._image, [])
        new_emoji.x = x
        new_emoji.y = y
        new_emoji.rotation = rotation
        new_emoji.scale = scale
        new_emoji._emoji_image = self._emoji_image
        return new_emoji

    def place_on_image(self, image: Image) -> None:
        if not isinstance(self._emoji_image, Image):
            raise Exception("Emoji Image missing")
        temp_image: Image = self._emoji_image.copy()
        width = max(1, int(self._emoji_image.width * self.scale)) 
        height = max(1, int(self._emoji_image.height * self.scale)) 
        temp_image: Image = temp_image.resize((width, height))
        temp_image.rotate(self.rotation, NEAREST, expand=True)
        image.paste(temp_image, (self.x, self.y), temp_image.convert('RGBA'))

