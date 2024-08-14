import asyncio
import pickle
import time
import os
import sys
import websockets
import threading
import ssl
import threading


class StarProcessingServer:
    def __init__(self, port):
        """
        Constructor.

        :param port: The port at which to start the server
        """
        self.send_queue = asyncio.Queue()
        self.max_k = 0
        self.results_dict = dict()
        self.results_dict_lock = threading.Lock()
        self.port = port
        self.shutdown_event = threading.Event()

        self.client_cert_path = os.getenv('STARCOMPUTE_CLIENT_CERT_PATH')
        self.server_cert_path = os.getenv('STARCOMPUTE_SERVER_CERT_PATH')
        self.server_key_path = os.getenv('STARCOMPUTE_SERVER_KEY_PATH')

        if self.server_cert_path is None or self.client_cert_path is None or self.client_key_path is None:
            err_str = ("Cannot find values of environmental variables for certificates and clients. Make sure the"
                       "following environmental variables are set:\n1. STARCOMPUTE_CLIENT_CERT_PATH\n"
                       "2. STARCOMPUTE_SERVER_CERT_PATH\n3. STARCOMPUTE_SERVER_KEY_PATH")

            raise RuntimeError(err_str)

        # for i in range(10000):
        #     self.send_queue.put_nowait(i*2)
        # self.receive_queue = asyncio.Queue()
        # self.receive_dict = AsyncDict()

    async def handle_client(self, websocket, path):
        # async def send_messages():
        #     num = 1
        #     while True:
        #         # await asyncio.sleep(5)  # Send every 5 seconds
        #         data = await self.send_queue.get()
        #         print(f"Server: Sending {num} to client.")
        #         await websocket.send(str(data))
        #         num += 1

        async def receive_messages():
            while True:
                try:
                    k, data_to_process = await self.send_queue.get()
                    print(k)
                    if k == -1:
                        break
                    data_result = await websocket.recv()
                    print(f"Server: Received {data_result} from client.")
                    try:
                        print(f"Server: Sending message to process to a slave.")
                        serialized_obj = pickle.dumps(data_to_process)
                        await websocket.send(serialized_obj)
                        data_result = await websocket.recv()
                        data_result = pickle.loads(data_result)
                        with self.results_dict_lock:
                            self.results_dict[k] = data_result
                        print("Got back result from a slave")
                    except ValueError:
                        print("Server: Received invalid data_to_process.")
                except websockets.exceptions.ConnectionClosedOK:
                    print("Server: Connection closed by client.")
                    break

        await asyncio.gather(receive_messages())

    def run_server(self):
        """
        Run the server in another thread. The function will return immediately.

        :return: None
        """

        def _thread():
            async def _thread_in():
                # Create SSL context for the server
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(certfile=self.server_cert_path, keyfile=self.server_key_path)

                # Require clients to present certificates
                ssl_context.verify_mode = ssl.CERT_REQUIRED
                ssl_context.load_verify_locations(self.client_cert_path)

                self.server = await websockets.serve(self.handle_client, "localhost", self.port)
                print("Server started on ws://localhost:%d"%self.port)
                # while True:
                #     # print("Server running...")
                #     await asyncio.sleep(10)
                #     # await asyncio.Future()  # Run forever
                while not self.shutdown_event.is_set():
                    await asyncio.sleep(1)

                    # Stop the server gracefully
                self.server.close()
                await self.server.wait_closed()

            asyncio.run(_thread_in())
            # while True:
            #     time.sleep(5)
        self.server_thread = threading.Thread(target=_thread)
        self.server_thread.start()

    def join(self):
        self.server_thread.join()

    def close(self):
        """
        Shutdown the server and all the connections.
        """

        for i in range(10000):
            self.send_queue.put_nowait((-1, None))

        self.shutdown_event.set()
        asyncio.get_event_loop().call_soon_threadsafe(asyncio.get_event_loop().stop)

    def run_tasks(self, tasks):
        """
        Will perform the tasks on clients and values will be returned.

        :param tasks: A list of tasks.
        :return: A list of results.
        """

        to_get = []
        for t in tasks:
            t2 = self.max_k, t
            to_get.append(self.max_k)
            self.send_queue.put_nowait(t2)
            self.max_k += 1
        while len(self.results_dict) != len(to_get):
            time.sleep(0.01)

        results = []
        for t in to_get:
            results.append(self.results_dict.pop(t))

        self.results_dict = dict()

        return results
