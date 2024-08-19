import os
import time

import argh
import numpy as np

from starcompute.star_client import StarClient

def get_tasks(num_tasks):
    tasks = []
    for i in range(num_tasks):
        tasks.append(np.random.normal(size=100))
    return tasks



def main(manager_ip='34.65.93.244', port=445):
    server_url = 'wss://%s:%s'%(manager_ip, port)

    manager_cert_path = os.getenv('STARCOMPUTE_MANAGER_CERT_PATH')
    client_cert_path = os.getenv('STARCOMPUTE_CLIENT_CERT_PATH')
    client_key_path = os.getenv('STARCOMPUTE_CLIENT_KEY_PATH')


    t1 = time.time()
    # Instantiate the client
    star_client = StarClient(server_url, manager_cert_path, client_cert_path, client_key_path)

    # Generate tasks
    tasks = get_tasks(50)

    # Run the tasks on the server
    result = star_client.run(tasks)

    # Print the results
    print("The result:")
    print(result)
    t2 = time.time()
    print("Took", t2 - t1, "seconds")


# Usage
if __name__ == "__main__":
    argh.dispatch_command(main)

