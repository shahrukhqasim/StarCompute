import argh
import numpy as np
from starcompute.star_manager import StarProcessingManager


def main(port=7777):
    manager = StarProcessingManager(port)
    manager.run_manager()

    results = manager.run_tasks([np.array([10, 10, 11]),
                                np.array([7, 1, 4]),
                                np.array([11, 9, 99]),
                                np.array([30, 110, 101])])

    print("Got back the results")
    print(results)
    manager.close()
    manager.join()


if __name__ == "__main__":
    argh.dispatch_command(main)

