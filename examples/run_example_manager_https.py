import time

import argh
import numpy as np
from starcompute.star_manager import StarProcessingManager
from starcompute.star_https_manager import StarHttpsManager
import datetime

def main(port=7778, port_clients=7779):
    manager = StarHttpsManager(port, port_clients)
    manager.run_manager()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    argh.dispatch_command(main)

