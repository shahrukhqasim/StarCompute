import asyncio
import time
import ssl

import requests
import websockets
import pickle
import os
import sys

class StarHttpsProcessingWorker:
    def __init__(self, port, processing_fn, url="https://localhost"):
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


    def start(self, num_tries_max=-1, wait_between_tries=1, wait_between_finishes=0.001):
        num_tries = 0
        session = requests.Session()

        client_cert = (self.worker_cert_path, self.worker_key_path)
        i = 0

        while True:
            try:
                response = session.get('%s:%d/want_work' % (self.url, self.port), verify=self.manager_cert_path, cert=client_cert)
                # Check if the request was successful
                if response.status_code == 200:
                    try:
                        # Unpickle the response content
                        data = pickle.loads(response.content)

                        # Assume the unpickled data is a tuple (k, data_to_process)
                        k, data_to_process = data
                        print(k)

                        if k==-1:
                            break
                        elif k==-2:
                            print("No tasks yet to perform. Waiting and trying again...")
                            continue
                        elif k >= 0:
                            # Process the unpickled data
                            print(f"Received key: {k}")
                            print(f"Received data to process: {data_to_process}", type(data_to_process))
                            time.sleep(wait_between_finishes)

                            result = self.processing_fn(data_to_process)

                            pickled_data = pickle.dumps((k, result))


                            for i in range(10):
                                try:
                                    # POST the pickled data back to the server
                                    response = requests.post(
                                        '%s:%d' % (self.url, self.port),  # Update the URL to the correct endpoint
                                        data=pickled_data,
                                        verify=self.manager_cert_path,  # Path to server's cert
                                        cert=client_cert,  # Client cert and key
                                        headers={'Content-Type': 'application/octet-stream'}  # Set the appropriate content type
                                    )
                                    if response.status_code == 200:
                                        break
                                except OSError as e:
                                    print("Connection failed posting back. Will try again.", file=sys.stderr)
                                    time.sleep(0.05)

                            i += 1

                            print("Result posted back", response.status_code, response.text)
                            print("Completed", i)

                    except pickle.UnpicklingError as e:
                        print(f"Error unpickling the response: {e}")
            except OSError as e:
                if num_tries < num_tries_max or num_tries_max == -1:
                    print("Connection failed. Will try again.", file=sys.stderr)
                    num_tries += 1
                else:
                    raise e
