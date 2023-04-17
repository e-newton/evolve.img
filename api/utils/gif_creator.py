from __future__ import annotations
from typing import Type
from PIL.Image import Image, NEAREST
from PIL.Image import open as img_open
import pathlib

FRAME_DIRECTORY = '.tmp/gif_frames/'
FPS = 12
FRAME_DURATION = 1000/FPS

class GifCreator():
    _instance: GifCreator
    path: pathlib.Path = pathlib.Path(FRAME_DIRECTORY)

    @classmethod
    def instance(cls: Type[GifCreator]) -> GifCreator:
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
            cls._instance._setup_directory()
        return cls._instance

    def _setup_directory(self) -> None:
        if not self.path.exists():
            self.path.mkdir(parents=True)
        else:
            [file.unlink() for file in self.path.glob('*')]

    def save_frame(self, frame: Image, frame_num: int) -> None:
        filename = f"{frame_num}.png"
        frame.save(self.path/filename)

    def create_gif(self, path: str, size: tuple[int, int]) -> None:
        def extract_number(file_path: pathlib.Path) -> int:
            return int(file_path.stem)
        frames: list[Image] = []
        frame_names = sorted(list(self.path.glob('*.png')), key=extract_number)
        for frame_name in frame_names:
            with img_open(frame_name) as f:
                frames.append(f.convert('P').resize(size, NEAREST))
        if len(frames) == 0:
            raise Exception('No Frames Found')
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=FRAME_DURATION, loop=0)

