import pickle
import ssl
import time

import websockets
import asyncio
import logging
import requests
import numpy as np

from starcompute import array_of_bytes_pb2

logging.basicConfig(level=logging.DEBUG)

def get_tasks(num_tasks, pickle_it=True):
    tasks = []
    for i in range(num_tasks):
        tasks.append(np.random.normal(size=100))
    return tasks


def serialize(tasks):
    data_array = array_of_bytes_pb2.SerializedDataArray()
    for t in tasks:
        data_array.data.append(pickle.dumps(t))
    serialized_data = data_array.SerializeToString()
    return serialized_data

def deserialize(result):
    data_array = array_of_bytes_pb2.SerializedDataArray()

    # Deserialize the binary string back into the data_array message
    data_array.ParseFromString(result)

    data_array = [x for x in data_array.data]
    results_array = []
    print("DAT array", data_array)
    print(len(data_array))
    for i, item in enumerate(data_array):
        print("YYY", pickle.loads(item))
        results_array.append(pickle.loads(item))
    return results_array


async def connect():
    # Create SSL context for the client
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # Load the server's certificate to verify the server
    ssl_context.load_verify_locations('/Users/shahrukhqasim/workspace/uzh/starcompute/crypt/manager_cert.pem')

    ssl_context.check_hostname = False
    # ssl_context.verify_mode = ssl.CERT_NONE

    # Load client's certificate and key
    ssl_context.load_cert_chain(certfile='/Users/shahrukhqasim/workspace/uzh/starcompute/crypt/client_cert.pem', keyfile='/Users/shahrukhqasim/workspace/uzh/starcompute/crypt/client_key.pem')

    num_tries = 0

    try:
        async with websockets.connect('wss://34.65.93.243:444', timeout=10, ssl=ssl_context, ping_interval=300, ping_timeout=300) as websocket:
            print("Helloooo!!!")
            await websocket.send("Hello")


            to_process = get_tasks(5000)

            to_process_serialized = serialize(to_process)

            await websocket.send(to_process_serialized)
            #
            # for i in range(1000000):
            #     time.sleep(1)
            result = await websocket.recv()
            print("Got back", result)
            result = deserialize(result)
            print(to_process)
            print("The result:")
            print(result)
    except asyncio.TimeoutError:
        print("Connection timed out")
    except Exception as e:
        print(f"An error occurred: {e}")

asyncio.get_event_loop().run_until_complete(connect())
