from evolve_objects.emoji import Emoji
from generator import GeneratorMessageContent, multiprocessing, start_generator_watch, GeneratorMessage
import time

if __name__ == '__main__':
    queue: multiprocessing.Queue = multiprocessing.Queue()
    queue.join_thread
    generator_process = multiprocessing.Process(target=start_generator_watch, args=(queue,))
    generator_process.start()
    time.sleep(1)
    queue.put(GeneratorMessage.send_status())
    status: GeneratorMessage = queue.get()
    if status:
        print('status 1', status.status)
    queue.put(GeneratorMessage.generate('finn.jpg', Emoji))
    while generator_process.is_alive():
        time.sleep(1)
        print('In main process')
        queue.put(GeneratorMessage.send_status())
        status: GeneratorMessage = queue.get()
        if status.message != GeneratorMessageContent.RECIEVED_STATUS:
            queue.put(status)
        else:
            print('status loop', status.status)


    









