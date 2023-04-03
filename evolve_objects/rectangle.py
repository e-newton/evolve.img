from __future__ import annotations
from typing import Tuple
from PIL import ImageDraw
from PIL import Image
from evolve_objects.object import BaseObject
import random

def clamp(n: int, min_num: int, max_num: int) -> int:
    return max(min_num, min(n, max_num))

class Rectangle(BaseObject):
    def __init__(self, image: Image.Image, color_palette: list[tuple[int, int, int]]):
        self.color = random.choice(color_palette)
        self.x1 = random.randint(0, image.width - 1)
        self.x2 = random.randint(self.x1, image.width - 1)
        self.y1 = random.randint(0, image.height - 1)
        self.y2 = random.randint(self.y1, image.height - 1)
        self.image = image
        self.color_palette = color_palette
        self.score = 0


    def deviate(self, percent: float, max_width: int, max_height: int) -> Rectangle:
        widthRange = int(percent * max_width)
        heightRange = int(percent * max_height)
        colorRange = int((percent / 10) * 255)
        x1 = clamp(self.x1 + random.randint(-widthRange, widthRange), 0, max_width - 1)
        x2 = clamp(self.x2 + random.randint(-widthRange, widthRange), 0, max_width - 1)
        y1 = clamp(self.y1 + random.randint(-heightRange, heightRange), 0, max_height - 1)
        y2 = clamp(self.y2 +random.randint(-heightRange, heightRange), 0, max_height - 1)
        new_r = clamp(self.color[0] + random.randint(-colorRange, colorRange), 0, 255)
        new_g = clamp(self.color[1] + random.randint(-colorRange, colorRange), 0, 255)
        new_b = clamp(self.color[2] + random.randint(-colorRange, colorRange), 0, 255)
        return_rect = Rectangle(self.image, self.color_palette)
        return_rect.x1 = min(x1, x2)
        return_rect.x2 = max(x1, x2)
        return_rect.y1 = min(y1, y2)
        return_rect.y2 = max(y1, y2)
        return_rect.color = (new_r, new_g, new_b)
        return return_rect

    def __to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)

    def place_on_image(self, image: Image.Image) -> None:
        ImageDraw.ImageDraw(image).rectangle(self.__to_tuple(), self.color)

