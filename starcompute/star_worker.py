import asyncio
import time
import ssl
import websockets
import pickle
import os
import sys

class StarProcessingWorker:
    def __init__(self, port, processing_fn, url="ws://localhost"):
        """
        Constructor.

        :param port: The port to connect to.
        :param processing_fn: A callable function which takes one argument, the data to process. It should return the
        result which will be pickled and sent back to the server.
        :param url: The URL at which the server can be found.
        """

        self.port = port
        assert callable(processing_fn)
        self.processing_fn = processing_fn
        self.url = url

        self.manager_cert_path = os.getenv('STARCOMPUTE_MANAGER_CERT_PATH')
        self.worker_cert_path = os.getenv('STARCOMPUTE_WORKER_CERT_PATH')
        self.worker_key_path = os.getenv('STARCOMPUTE_WORKER_KEY_PATH')

        if self.manager_cert_path is None or self.worker_cert_path is None or self.worker_key_path is None:
            err_str = ("Cannot find values of environmental variables for certificates and keys. Make sure the"
                       "following environmental variables are set:\n1. STARCOMPUTE_MANAGER_CERT_PATH\n"
                       "2. STARCOMPUTE_WORKER_CERT_PATH\n3. STARCOMPUTE_WORKER_KEY_PATH")

            raise RuntimeError(err_str)


    async def start(self, num_tries_max=-1, wait_between_tries=1):
        """
        Starts the WebSocket client that connects to the server with a secure SSL/TLS context to start processing the
        data.

        The client will attempt to establish a connection with the server and will continue to retry
        if the connection fails.

        :param num_tries_max:
            The maximum number of attempts to establish a connection. If set to -1 (default),
            the worker will keep trying indefinitely until it succeeds. If set to a positive integer,
            the worker will attempt to connect the specified number of times before giving up.

        :param wait_between_tries:
            The time in seconds to wait between connection attempts if the connection fails.
            Default is 1 second.

        :return:
            None

        :raises OSError:
            If the worker fails to connect to the server after the specified number of attempts
            (only if num_tries_max is a positive integer).

        The method establishes a WebSocket connection using SSL/TLS, verifies the server's certificate,
        and loads the worker's certificate and key for mutual authentication. After that it will start receiving data
        from the server in order to be able to start processing the data.
        """

        # Create SSL context for the client
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        # Load the server's certificate to verify the server
        ssl_context.load_verify_locations(self.manager_cert_path)

        ssl_context.check_hostname = False
        # ssl_context.verify_mode = ssl.CERT_NONE

        # Load client's certificate and key
        ssl_context.load_cert_chain(certfile=self.worker_cert_path, keyfile=self.worker_key_path)

        num_tries = 0

        while True:
            try:
                async with websockets.connect("wss://localhost:%d"%self.port, ssl=ssl_context) as websocket:
                    async def send_messages():
                        while True:
                            try:
                                print(f"Worker: Sending hello to the server.")
                                await websocket.send("Helo")
                                command = await websocket.recv()
                                assert type(command) is str
                                if command == 'process':
                                    to_process = await websocket.recv()
                                    to_process = pickle.loads(to_process)
                                    processed = self.processing_fn(to_process)
                                    result = pickle.dumps(processed)
                                    print("Sending back processed ")
                                    # print(f"Client: Received {response} from server.")
                                    await websocket.send(result)
                                elif command == 'stop':
                                    return
                            except websockets.exceptions.ConnectionClosedOK:
                                break

                    async def receive_messages():
                        while True:
                            data = await websocket.recv()
                            print(f"Client: Received {data} from server.")
                            # try:
                            #     number = int(data)
                            #     result = number + 1
                            #     print(f"Client: Sending {result} back to server.")
                            #     await websocket.send(str(result))
                            # except ValueError:
                            #     print("Client: Received invalid number.")

                    await asyncio.gather(send_messages())
                    break
            except OSError as e:
                if num_tries < num_tries_max or num_tries_max == -1:
                    print("Connection failed. Will try again.", file=sys.stderr)
                    await asyncio.sleep(wait_between_tries)
                    num_tries += 1
                else:
                    raise e
