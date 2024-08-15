import time

import argh
import numpy as np
from starcompute.star_manager import StarProcessingManager
from starcompute.star_https_manager import StarHttpsManager
import datetime

def main(port=7778, num_tasks=10):
    manager = StarHttpsManager(port)
    manager.run_manager()

    tasks = []
    for i in range(num_tasks):
        tasks.append(np.random.normal(size=10))

    print("Got", len(tasks), "tasks to run...")
    results = manager.run_tasks(tasks)


    print("Got back the results")
    print(results)

    time.sleep(15)
    print("Will try to close now.")

    # while True:
    #     print("Server running:", datetime.datetime.fromtimestamp(time.time()))
    #     time.sleep(10)

    manager.close()
    manager.join()


if __name__ == "__main__":
    argh.dispatch_command(main)

