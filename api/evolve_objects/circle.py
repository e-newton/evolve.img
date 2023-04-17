from __future__ import annotations
from PIL import ImageDraw
from PIL import Image
from evolve_objects.object import BaseObject
from evolve_objects.rectangle import clamp
import random

class Circle(BaseObject):
    def __init__(self, create_new: bool, image: Image.Image, color_palette: list[tuple[int, int, int]]):
        if create_new:
            self.color = random.choice(color_palette)
            self.x = random.randint(0, image.width - 1)
            self.y = random.randint(0, image.height - 1)
            self.r = random.randint(0, min(image.width, image.height))
        self.image = image
        self.color_palette = color_palette

    def deviate(self, percent: float, max_width: int, max_height: int) -> Circle:
        radius_range = int(percent * min(max_width, max_height))
        widthRange = int(percent * max_width)
        heightRange = int(percent * max_height)
        colorRange = int((percent / 10) * 255)
        x = clamp(self.x + random.randint(-widthRange, widthRange), 0, max_width - 1)
        y = clamp(self.y + random.randint(-heightRange, heightRange), 0, max_height - 1)
        r = clamp(self.r + random.randint(-radius_range, radius_range), 0, min(max_width, max_height))
        new_r = clamp(self.color[0] + random.randint(-colorRange, colorRange), 0, 255)
        new_g = clamp(self.color[1] + random.randint(-colorRange, colorRange), 0, 255)
        new_b = clamp(self.color[2] + random.randint(-colorRange, colorRange), 0, 255)
        return_circle = Circle(False, self.image, self.color_palette)
        return_circle.x = x
        return_circle.y = y
        return_circle.r = r
        return_circle.color = (new_r, new_g, new_b)
        return return_circle

    def __to_tuple(self) -> tuple[int, int, int, int]:
        return (self.x - self.r, self.y - self.r, self.x + self.r, self.y + self.r)


    def place_on_image(self, image: Image.Image):
        ImageDraw.ImageDraw(image).ellipse(self.__to_tuple(), self.color)
