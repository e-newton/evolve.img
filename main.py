from math import floor, sqrt
from multiprocessing.pool import Pool
from PIL import Image
import multiprocessing
from typing import cast
from evolve_objects.rectangle import Rectangle
from evolve_objects.circle import Circle
from evolve_objects.object import BaseObject
import numpy
from numpy._typing import NDArray

ROUNDS = 2000
SUB_ROUNDS = 10
NUM_BASE_RECTANGLES = 100
NUM_SUB_RECTANGLES = floor(sqrt(NUM_BASE_RECTANGLES))
NUM_BEST = floor(sqrt(NUM_BASE_RECTANGLES))
BASE_PERCENT = 0.7
MAX_IMAGE_SIZE=128

# Images must be same size
def compare_images(image1: NDArray[numpy.int64], image2: NDArray[numpy.int64]) -> int:
    assert(image1.shape == image2.shape)
    return numpy.sum(numpy.abs(image1 - image2))

def score_object(object: BaseObject, new_image_array: NDArray[numpy.int64], base_image_array: NDArray[numpy.int64]) -> BaseObject:
    # Until I can figure out how to properally add a rectangle to the array this is just how it be
    temp_img = Image.fromarray(new_image_array.astype(numpy.uint8))
    object.place_on_image(temp_img)
    object.score = compare_images(numpy.array(temp_img).astype(numpy.int64), base_image_array)
    return object

def start_multi_object_scores(
        pool_data: list[tuple[BaseObject, NDArray[numpy.int64], NDArray[numpy.int64]]],
        pool: Pool,
        num_processess: int
        ) -> list[BaseObject]:
    results: list[BaseObject] = []
    chunk_size = len(pool_data)//num_processess
    main_thread_chunk = pool_data[:chunk_size]
    async_results = pool.starmap_async(score_object, pool_data[chunk_size + 1:], chunksize=chunk_size)
    for d in main_thread_chunk:
        results.append(score_object(d[0], d[1], d[2]))
    async_results.wait()
    results += async_results.get()
    return results
    


def main():
    base_image = Image.open('finn.jpg').convert('RGB')
    base_image_size = base_image.size
    base_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.LANCZOS)
    base_image_colors = cast(list[tuple[int, int, int]], [color[1] for color in base_image.getcolors(maxcolors=base_image.height * base_image.width)])
    new_image = Image.new('RGB', base_image.size)
    new_image_array = numpy.array(new_image).astype(numpy.int64)
    base_image_array = numpy.array(base_image).astype(numpy.int64)
    round = 0
    prev_best_score = 0
    num_processess = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(num_processess)
    # Cast to parent class to make abstract
    object: type[BaseObject] = cast(type[BaseObject], Circle)
    while round < ROUNDS:
        print('Creating base objects for round', round)
        base_objects = [object(new_image, base_image_colors) for _ in range(NUM_BASE_RECTANGLES)]
        pool_data = [(o, new_image_array, base_image_array) for o in base_objects]
        print('Scoring base objects')
        base_results = start_multi_object_scores(pool_data, pool, num_processess)
        base_results.sort(key=lambda r: r.score)
        top_objects: list[BaseObject] = base_results[:NUM_BEST]
        percent = BASE_PERCENT
        for j in range(SUB_ROUNDS):
            deviated_objects = top_objects + [o for obj in top_objects for o in [obj.deviate(percent, new_image.width, new_image.height) for _ in range(NUM_SUB_RECTANGLES)]]
            deiviated_pool_data = [(r, new_image_array, base_image_array) for r in deviated_objects]
            print('Scoring deviated objects for sub round', j)
            deviated_objects = start_multi_object_scores(deiviated_pool_data, pool, num_processess)
            deviated_objects.sort(key=lambda r: r.score)
            top_objects = deviated_objects[:NUM_BEST]
            percent -= (percent/(SUB_ROUNDS - 1))
        best_rect = top_objects[0]
        if not prev_best_score or best_rect.score < prev_best_score:
            round += 1
            prev_best_score = best_rect.score
            best_rect.place_on_image(new_image);
            new_image_array = numpy.array(new_image).astype(numpy.int64)
            print('Best object score:', best_rect.score, 'iteration:', round)
        else:
            print('Round did not end with a good enough score')
    pool.close()
    new_image.resize(base_image_size, Image.NEAREST).save('hot-mess-final.png')

if __name__ == '__main__':
    main()









