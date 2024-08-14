import asyncio
import pickle
import time

import websockets
import threading
import ssl
import threading
import numpy as np
from star_server import StarProcessingServer


if __name__ == "__main__":
    server = StarProcessingServer(8757)
    server.run_server()

    print("Here!")

    results = server.run_tasks([np.array([10,10,11]),
                                np.array([7,1,4]),
                                np.array([11,9,99]),
                                np.array([30,110,101])])

    print("Got back the results")
    print(results)
    server.close()
    server.server_thread.join()

