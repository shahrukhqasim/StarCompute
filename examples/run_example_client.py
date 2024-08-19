import pickle
import ssl
import time

import websockets
import asyncio
import logging
import requests
import numpy as np

from starcompute.star_client import StarClient

def get_tasks(num_tasks):
    tasks = []
    for i in range(num_tasks):
        tasks.append(np.random.normal(size=100))
    return tasks


# Usage
if __name__ == "__main__":
    server_url = 'wss://34.65.93.243:444'
    cert_path = '/Users/shahrukhqasim/workspace/uzh/starcompute/crypt/manager_cert.pem'
    client_cert_path = '/Users/shahrukhqasim/workspace/uzh/starcompute/crypt/client_cert.pem'
    client_key_path = '/Users/shahrukhqasim/workspace/uzh/starcompute/crypt/client_key.pem'


    t1 = time.time()
    # Instantiate the client
    star_client = StarClient(server_url, cert_path, client_cert_path, client_key_path)

    # Generate tasks
    tasks = get_tasks(10)

    # Run the tasks on the server
    result = star_client.run(tasks)

    # Print the results
    print("The result:")
    print(result)
    t2 = time.time()
    print("Took", t2-t1, "seconds")
