import asyncio
import time
import numpy as np
from starcompute.star_https_worker import StarHttpsProcessingWorker
import argh
import starcompute


def process(el):
    # In the example, el is a numpy array, this process functions sums up the element and returns it after waiting
    # 3 seconds to mimic a complex calculation
    time.sleep(0.5)
    return np.sum(el)

def main(port=7778, url='ws://localhost'):
    print("Will run on", port, url)
    print(starcompute.__version__, starcompute.__file__)
    worker = StarHttpsProcessingWorker(port, processing_fn=process, url=url)
    worker.start(num_tries_max=-1)
    print("Execution finished.")


if __name__ == "__main__":
    argh.dispatch_command(main)
