from __future__ import annotations
from abc import ABC, abstractmethod
from PIL import Image

class BaseObject(ABC):
    
    score = 0
    @abstractmethod
    def __init__(self, image: Image.Image, color_palette: list[tuple[int, int, int]]) -> None:
        pass

    @abstractmethod
    def deviate(self, percent: float, max_width: int, max_height: int) -> BaseObject:
        pass

    @abstractmethod
    def place_on_image(self, image: Image.Image):
        pass
