from __future__ import annotations
from enum import Enum
from math import floor, sqrt
from multiprocessing.pool import Pool
from multiprocessing.queues import Queue
from re import VERBOSE
from PIL import Image
import multiprocessing
import threading
import time
from typing import Optional, Type, cast
from evolve_objects.factories.emoji_factory import EmojiFactory
from evolve_objects.object import BaseObject
from utils.gif_creator import GifCreator
import numpy
import pathlib
from numpy._typing import NDArray
from typing import Union

ROUNDS = 50
SUB_ROUNDS = 20
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

def start_generator_watch(queue: Queue):
    EvolveGenerator(queue).watch_queue()

class GeneratorMessageContent(Enum):
    STOP = 'STOP',
    GENERATE = 'GENERATE'
    VERBOSE = 'VERBOSE'
    NON_VERBOSE = 'NON_VERBOSE'

class GeneratorMessage():
    def __init__(self, message: GeneratorMessageContent, path: Optional[str], object: Optional[Type[BaseObject]]):
        self.message = message
        self.path = path
        self.object = object

    @classmethod
    def stop(cls) -> GeneratorMessage:
        return GeneratorMessage(GeneratorMessageContent.STOP, None, None)

    @classmethod
    def generate(cls, path: str, object: Type[BaseObject]) -> GeneratorMessage:
        return GeneratorMessage(GeneratorMessageContent.GENERATE, path, object)

    @classmethod
    def set_verbose(cls, value: bool) -> GeneratorMessage:
        return GeneratorMessage(GeneratorMessageContent.VERBOSE if value else GeneratorMessageContent.NON_VERBOSE, None, None)

class EvolveGenerator():

    _queue: Queue[GeneratorMessage]
    _verbose = True
    _generating_thread = Optional[threading.Thread]
    _generating_job_queue: list[GeneratorMessage] = []
    _stop_thread = False
    def __init__(self, queue: Queue[GeneratorMessage]):
        self._queue = queue

    def watch_queue(self):
        if self._verbose: print('Generator queue watch started')
        while True:
            if self._verbose: print('Waiting for message')
            current_message = self._queue.get()
            if self._verbose: print('Message recieved', current_message.message)
            if current_message.message == GeneratorMessageContent.STOP:
                if self._generating_thread is not None and isinstance(self._generating_thread, threading.Thread):
                    self._stop_thread = True
                    self._generating_thread.join()
                    self._stop_thread = False
            elif current_message.message == GeneratorMessageContent.VERBOSE:
                self._verbose = True
            elif current_message.message == GeneratorMessageContent.NON_VERBOSE:
                self._verbose = False
            elif current_message.message == GeneratorMessageContent.GENERATE:
                if not isinstance(self._generating_thread, threading.Thread):
                    if self._verbose: print('Starting generation thread')
                    self._generating_thread = threading.Thread(target = self._watch_generatoring_queue)
                    self._generating_thread.start()
                self._generating_job_queue.append(current_message)
            time.sleep(0.1)




    def _watch_generatoring_queue(self):
        if self._verbose: print('Generating queue watch thread started')
        while True:
            if len(self._generating_job_queue) > 0:
                if self._verbose: print('Starting generation job')
                current_processing_request = self._generating_job_queue[0]
                assert(current_processing_request.path is not None)
                assert(current_processing_request.object is not None)
                self.generate_image(current_processing_request.path, current_processing_request.object)
                self._generating_job_queue.remove(current_processing_request)
            else:
                if self._verbose: print('No processing job availble')
            time.sleep(1)


    def start_multi_object_scores(
            self,
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

    def generate_image(self, base_image_path: Union[str, pathlib.Path], evolve_object: type[BaseObject]) -> None:
        base_image = Image.open(base_image_path).convert('RGB')
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
        while round < ROUNDS:
            if self._stop_thread: return
            if self._verbose: print('Creating base objects for round', round)
            base_objects = [evolve_object(True, new_image, base_image_colors) for _ in range(NUM_BASE_RECTANGLES)]
            pool_data = [(o, new_image_array, base_image_array) for o in base_objects]
            if self._verbose: print('Scoring base objects')
            base_results = self.start_multi_object_scores(pool_data, pool, num_processess)
            base_results.sort(key=lambda r: r.score)
            top_objects: list[BaseObject] = base_results[:NUM_BEST]
            percent = BASE_PERCENT
            for j in range(SUB_ROUNDS):
                if self._stop_thread: return
                deviated_objects = top_objects + [o for obj in top_objects for o in [obj.deviate(percent, new_image.width, new_image.height) for _ in range(NUM_SUB_RECTANGLES)]]
                deiviated_pool_data = [(r, new_image_array, base_image_array) for r in deviated_objects]
                if self._verbose: print('Scoring deviated objects for sub round', j)
                deviated_objects = self.start_multi_object_scores(deiviated_pool_data, pool, num_processess)
                deviated_objects.sort(key=lambda r: r.score)
                top_objects = deviated_objects[:NUM_BEST]
                percent -= (percent/(SUB_ROUNDS - 1))
            best_rect = top_objects[0]
            if not prev_best_score or best_rect.score < prev_best_score:
                round += 1
                prev_best_score = best_rect.score
                best_rect.place_on_image(new_image);
                GifCreator.instance().save_frame(new_image.resize(base_image_size, Image.NEAREST), round)
                new_image_array = numpy.array(new_image).astype(numpy.int64)
                if self._verbose: print('Best object score:', best_rect.score, 'iteration:', round)
            else:
                if self._verbose: print('Round did not end with a good enough score')
        pool.close()
        new_image.resize(base_image_size, Image.NEAREST).save('hot-mess-final.png')
        GifCreator.instance().create_gif('hot-mess-gif.gif', base_image_size)
        EmojiFactory.instance().destroy()

