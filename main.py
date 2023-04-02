from math import floor, sqrt
from multiprocessing.pool import Pool
from PIL import Image
from PIL import ImageDraw
import random
import multiprocessing
from typing import Tuple, cast
import numpy
from numpy._typing import NDArray

ROUNDS = 2000
SUB_ROUNDS = 10
NUM_BASE_RECTANGLES = 100
NUM_SUB_RECTANGLES = floor(sqrt(NUM_BASE_RECTANGLES))
NUM_BEST = floor(sqrt(NUM_BASE_RECTANGLES))
BASE_PERCENT = 0.7
MAX_IMAGE_SIZE=128

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

    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)

    def to_array(self, base_image_array: NDArray[numpy.int64]) -> NDArray[numpy.int64]:
        array = numpy.zeros(base_image_array.shape).astype(numpy.int64)
        array[self.x1:self.x2, self.y1:self.y2] = self.color
        return array


def random_rectangle_from_image(image: Image.Image, color_palette: list[tuple[int, int, int]]) -> Rectangle:
    color = random.choice(color_palette)
    x1 = random.randint(0, image.width - 1)
    x2 = random.randint(x1, image.width - 1)
    y1 = random.randint(0, image.height - 1)
    y2 = random.randint(y1, image.height - 1)
    return Rectangle(x1, y1, x2, y2, color)

# Images must be same size
def compare_images(image1: NDArray[numpy.int64], image2: NDArray[numpy.int64]) -> int:
    assert(image1.shape == image2.shape)
    return numpy.sum(numpy.abs(image1 - image2))

def score_rectangle(rectangle: Rectangle, new_image_array: NDArray[numpy.int64], base_image_array: NDArray[numpy.int64]) -> Rectangle:
    temp_img = Image.fromarray(new_image_array.astype(numpy.uint8))
    temp_img_draw = ImageDraw.ImageDraw(temp_img)
    temp_img_draw.rectangle(rectangle.to_tuple(), rectangle.color)
    rectangle.score = compare_images(numpy.array(temp_img).astype(numpy.int64), base_image_array)
    return rectangle

def start_multi_rectangle_scores(
        pool_data: list[tuple[Rectangle, NDArray[numpy.int64], NDArray[numpy.int64]]],
        pool: Pool,
        num_processess: int
        ) -> list[Rectangle]:
    results: list[Rectangle] = []
    chunk_size = len(pool_data)//num_processess
    main_thread_chunk = pool_data[:chunk_size]
    async_results = pool.starmap_async(score_rectangle, pool_data[chunk_size + 1:], chunksize=chunk_size)
    for d in main_thread_chunk:
        results.append(score_rectangle(d[0], d[1], d[2]))
    async_results.wait()
    results += async_results.get()
    return results
    


def main():
    base_image = Image.open('finn.jpg').convert('RGB')
    base_image_size = base_image.size
    base_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.LANCZOS)
    base_image_colors = cast(list[tuple[int, int, int]], [color[1] for color in base_image.getcolors(maxcolors=base_image.height * base_image.width)])
    new_image = Image.new('RGB', base_image.size)
    new_image_draw = ImageDraw.ImageDraw(new_image)
    new_image_array = numpy.array(new_image).astype(numpy.int64)
    base_image_array = numpy.array(base_image).astype(numpy.int64)
    round = 0
    prev_best_score = 0
    num_processess = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(num_processess)
    while round < ROUNDS:
        print('Creating base rectangles for round', round)
        base_rectangles = [random_rectangle_from_image(new_image, base_image_colors) for _ in range(NUM_BASE_RECTANGLES)]
        pool_data = [(r, new_image_array, base_image_array) for r in base_rectangles]
        print('Scoring base rectangles')
        base_results = start_multi_rectangle_scores(pool_data, pool, num_processess)
        base_results.sort(key=lambda r: r.score)
        top_rectangles: list[Rectangle] = base_results[:NUM_BEST]
        percent = BASE_PERCENT
        for j in range(SUB_ROUNDS):
            deviated_rects = top_rectangles + [r for rect in top_rectangles for r in [rect.deviate(percent, new_image.width, new_image.height) for _ in range(NUM_SUB_RECTANGLES)]]
            deiviated_pool_data = [(r, new_image_array, base_image_array) for r in deviated_rects]
            print('Scoring deviated rectangles for sub round', j)
            deviated_rects = start_multi_rectangle_scores(deiviated_pool_data, pool, num_processess)
            deviated_rects.sort(key=lambda r: r.score)
            top_rectangles = deviated_rects[:NUM_BEST]
            percent -= (percent/(SUB_ROUNDS - 1))
        best_rect = top_rectangles[0]
        if not prev_best_score or best_rect.score < prev_best_score:
            round += 1
            prev_best_score = best_rect.score
            new_image_draw.rectangle(best_rect.to_tuple(), fill=best_rect.color)
            new_image_array = numpy.array(new_image).astype(numpy.int64)
            print('Best rectangle score:', best_rect.score, 'iteration:', round)
        else:
            print('Round did not end with a good enough score')
    pool.close()
    new_image.resize(base_image_size, Image.NEAREST).save('hot-mess-final.png')

if __name__ == '__main__':
    main()









