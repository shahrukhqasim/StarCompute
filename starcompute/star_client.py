import pickle
import ssl
import time
import websockets
import asyncio
import logging
import numpy as np

from starcompute import array_of_bytes_pb2

logging.basicConfig(level=logging.DEBUG)


class StarClient:
    def __init__(self, server_url, manager_cert_path, client_cert_path, client_key_path):
        self.server_url = server_url
        self.ssl_context = self.create_ssl_context(manager_cert_path, client_cert_path, client_key_path)


    def create_ssl_context(self, manager_cert_path, client_cert_path, client_key_path):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.load_verify_locations(manager_cert_path)
        ssl_context.check_hostname = False
        ssl_context.load_cert_chain(certfile=client_cert_path, keyfile=client_key_path)
        return ssl_context

    def serialize(self, tasks):
        data_array = array_of_bytes_pb2.SerializedDataArray()
        for t in tasks:
            data_array.data.append(pickle.dumps(t))
        serialized_data = data_array.SerializeToString()
        return serialized_data

    def deserialize(self, result):
        data_array = array_of_bytes_pb2.SerializedDataArray()
        data_array.ParseFromString(result)
        results_array = [pickle.loads(item) for item in data_array.data]
        return results_array

    async def connect(self, tasks):
        try:
            async with websockets.connect(self.server_url, timeout=10, ssl=self.ssl_context, ping_interval=300, ping_timeout=300) as websocket:
                print("Connected to the server.")
                await websocket.send("Hello")

                serialized_tasks = self.serialize(tasks)
                await websocket.send(serialized_tasks)

                result = await websocket.recv()
                deserialized_result = self.deserialize(result)

                return deserialized_result

        except asyncio.TimeoutError:
            print("Connection timed out")
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def run(self, tasks):
        return asyncio.get_event_loop().run_until_complete(self.connect(tasks))
