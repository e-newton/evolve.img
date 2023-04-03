from typing import Tuple
from PIL import ImageDraw
from PIL import Image
import random

def clamp(n: int, min_num: int, max_num: int) -> int:
    return max(min_num, min(n, max_num))

class Rectangle:
    def __init__(self, x1: int, y1: int, x2: int, y2: int, color: Tuple[int, int, int]):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.color = color
        self.score = 0


    def deviate(self, percent: float, max_width: int, max_height: int) -> 'Rectangle':
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
        new_x1 = min(x1, x2)
        new_x2 = max(x1, x2)
        new_y1 = min(y1, y2)
        new_y2 = max(y1, y2)
        return Rectangle(new_x1, new_y1, new_x2, new_y2, (new_r, new_b, new_g))

    def __to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)

    def place_on_image(self, image: Image.Image) -> None:
        ImageDraw.ImageDraw(image).rectangle(self.__to_tuple(), self.color)

