import asyncio
import time
import numpy as np
from starcompute.star_client import StarProcessingClient
import argh

def process(el):
    # In the example, el is a numpy array, this process functions sums up the element and returns it after waiting
    # 3 seconds to mimic a complex calculation
    time.sleep(3)
    return np.sum(el)


def main(port=8757):
    client = StarProcessingClient(port, processing_fn=process)
    asyncio.run(client.start())
    print("Execution finished.")


if __name__ == "__main__":
    argh.dispatch_command(main)

