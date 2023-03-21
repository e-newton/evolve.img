from PIL import Image
from PIL import ImageChops
from PIL import ImageDraw
import requests
import random
from typing import Tuple
from io import BytesIO

ROUNDS = 500
SUB_ROUNDS = 10
NUM_BASE_RECTANGLES = 1000
NUM_SUB_RECTANGLES = 10
BASE_PERCENT = 0.7
MAX_IMAGE_SIZE=128
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
        colorRange = int(percent * 255)
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

def random_rectangle_from_image(image: Image.Image) -> Rectangle:
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
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
    combined_image = ImageChops.difference(image1, image2)
    for i in range(image1.width):
        for j in range(image1.height):
            score += sum(combined_image.getpixel((i, j)))
    return score

def main():
    res = requests.get(url)
    # base_image = Image.open(BytesIO(res.content)).convert('RGB')
    base_image = Image.open('finn.jpg').convert('RGB')
    base_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.LANCZOS)
    new_image = Image.new('RGB', base_image.size)
    new_image_draw = ImageDraw.Draw(new_image)
    for i in range(ROUNDS):
        base_rectangles = [random_rectangle_from_image(new_image) for r in range(NUM_BASE_RECTANGLES)]
        score_count = 0
        for rect in base_rectangles:
            score_count += 1
            temp_img = new_image.copy()
            draw_image = ImageDraw.Draw(temp_img)
            draw_image.rectangle(rect.to_tuple(), fill=rect.color)
            rect.score = compare_images(temp_img, base_image)
            print('score for rect', score_count, rect.score)
            temp_img.close()
        base_rectangles.sort(key=lambda r: r.score)
        top_rectangles: list[Rectangle] = base_rectangles[:10]
        percent = BASE_PERCENT
        for j in range(SUB_ROUNDS):
            deviated_rects = top_rectangles + [r for rect in top_rectangles for r in [rect.deviate(percent, new_image.width, new_image.height) for i in range(NUM_SUB_RECTANGLES)]]
            sub_score_count = 0
            for rect in deviated_rects:
                sub_score_count += 1
                if rect.score == 0:
                    temp_img = new_image.copy()
                    draw_image = ImageDraw.Draw(temp_img)
                    draw_image.rectangle(rect.to_tuple(), fill=rect.color)
                    rect.score = compare_images(temp_img, base_image)
                    temp_img.close()
                print('score for round', j,'rect', sub_score_count, rect.score)
            deviated_rects.sort(key=lambda r: r.score)
            top_rectangles = deviated_rects[:10]
            percent -= (percent/(SUB_ROUNDS - 1))
        best_rect = top_rectangles[0]
        new_image_draw.rectangle(best_rect.to_tuple(), fill=best_rect.color)
        new_image.save('hot-mess-{0}.png'.format(i))
    new_image.save('hot-mess.png')

main()









