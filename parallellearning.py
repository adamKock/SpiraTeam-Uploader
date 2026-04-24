import time
from concurrent.futures import ThreadPoolExecutor


def worker(number):
    number = number*3
    print(f"This number is {number}")
    time.sleep(2)
    return number


pool = ThreadPoolExecutor(1)
workOne = pool.submit(worker,1)
workOn = pool.submit(worker,2)
