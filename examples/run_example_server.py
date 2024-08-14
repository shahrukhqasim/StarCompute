import argh
import numpy as np
from starcompute.star_server import StarProcessingServer


def main(port=7777):
    server = StarProcessingServer(port)
    server.run_server()

    results = server.run_tasks([np.array([10, 10, 11]),
                                np.array([7, 1, 4]),
                                np.array([11, 9, 99]),
                                np.array([30, 110, 101])])

    print("Got back the results")
    print(results)
    server.close()
    server.server_thread.join()


if __name__ == "__main__":
    argh.dispatch_command(main)

