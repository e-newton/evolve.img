from math import floor, sqrt
from PIL import Image
from PIL import ImageChops
from PIL import ImageDraw
import random
import multiprocessing
from typing import Tuple, cast
import numpy

ROUNDS = 1000
SUB_ROUNDS = 10
NUM_BASE_RECTANGLES = 100
NUM_SUB_RECTANGLES = floor(sqrt(NUM_BASE_RECTANGLES))
NUM_BEST = floor(sqrt(NUM_BASE_RECTANGLES))
BASE_PERCENT = 0.7
MAX_IMAGE_SIZE=512
url = 'https://hips.hearstapps.com/hmg-prod/images/domestic-cat-lies-in-a-basket-with-a-knitted-royalty-free-image-1592337336.jpg?crop=0.88889xw:1xh;center,top&resize=1200:*'

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
        new_x1 = clamp(self.x1 + random.randint(-widthRange, widthRange), 0, max_width - 1)
        new_x2 = clamp(self.x2 + random.randint(-widthRange, widthRange), 0, max_width - 1)
        new_y1 = clamp(self.y1 + random.randint(-heightRange, heightRange), 0, max_height - 1)
        new_y2 = clamp(self.y2 +random.randint(-heightRange, heightRange), 0, max_height - 1)
        new_r = clamp(self.color[0] + random.randint(-colorRange, colorRange), 0, 255)
        new_g = clamp(self.color[1] + random.randint(-colorRange, colorRange), 0, 255)
        new_b = clamp(self.color[2] + random.randint(-colorRange, colorRange), 0, 255)
        return Rectangle(new_x1, new_y1, new_x2, new_y2, (new_r, new_b, new_g))

    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)

def random_rectangle_from_image(image: Image.Image, color_palette: list[tuple[int, int, int]]) -> Rectangle:
    color = random.choice(color_palette)
    return Rectangle(
            random.randint(0, image.width - 1),
            random.randint(0, image.height - 1),
            random.randint(0, image.width - 1),
            random.randint(0, image.height - 1), color)

# Images must be same size
def compare_images(image1: Image.Image, image2: Image.Image) -> int:
    score = 0
    assert(image1.width == image2.width)
    assert(image1.height == image2.height)
    score = numpy.sum(numpy.array(ImageChops.difference(image1, image2)))
    return score

def score_rectangle(rectangle: Rectangle, new_image: Image.Image, base_image: Image.Image) -> Rectangle:
    temp_img = new_image.copy()
    draw_image = ImageDraw.Draw(temp_img)
    draw_image.rectangle(rectangle.to_tuple(), fill=rectangle.color)
    rectangle.score = compare_images(temp_img, base_image)
    temp_img.close()
    return rectangle

def main():
    base_image = Image.open('IMG_0749.jpeg').convert('RGB')
    base_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.LANCZOS)
    base_image_colors = cast(list[tuple[int, int, int]], [color[1] for color in base_image.getcolors(maxcolors=base_image.height * base_image.width)])
    new_image = Image.new('RGB', base_image.size)
    new_image_draw = ImageDraw.Draw(new_image)
    round = 0
    prev_best_score = 0
    while round < ROUNDS:
        print('Creating base rectangles for round', round)
        base_rectangles = [random_rectangle_from_image(new_image, base_image_colors) for _ in range(NUM_BASE_RECTANGLES)]
        pool_data = [(r, new_image, base_image) for r in base_rectangles]
        print('Scoring base rectangles')
        with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
            base_rectangles = pool.starmap(score_rectangle, pool_data)
        base_rectangles.sort(key=lambda r: r.score)
        top_rectangles: list[Rectangle] = base_rectangles[:NUM_BEST]
        percent = BASE_PERCENT
        for j in range(SUB_ROUNDS):
            print('Creating deviated rectangles for sub round', j)
            deviated_rects = top_rectangles + [r for rect in top_rectangles for r in [rect.deviate(percent, new_image.width, new_image.height) for _ in range(NUM_SUB_RECTANGLES)]]
            deiviated_pool_data = [(r, new_image, base_image) for r in deviated_rects]
            print('Scoring deviated rectangles')
            with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
                deviated_rects = pool.starmap(score_rectangle, deiviated_pool_data)
            deviated_rects.sort(key=lambda r: r.score)
            top_rectangles = deviated_rects[:NUM_BEST]
            percent -= (percent/(SUB_ROUNDS - 1))
        best_rect = top_rectangles[0]
        if not prev_best_score or best_rect.score < prev_best_score:
            round += 1
            prev_best_score = best_rect.score
            new_image_draw.rectangle(best_rect.to_tuple(), fill=best_rect.color)
            new_image.save('hot-mess-{0}.png'.format(round))
            print('Best rectangle score:', best_rect.score, 'iteration:', round)
        else:
            print('Round did not end with a good enough score')
    new_image.save('hot-mess.png')

if __name__ == '__main__':
    main()









