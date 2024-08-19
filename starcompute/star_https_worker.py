import asyncio
import time
import ssl

import urllib3
# urllib3.PoolManager = urllib3.PoolManager(assert_samehost=False)
import requests


import websockets
import pickle
import os
import sys

from starcompute import key_and_work_pb2

def write_to_file(file_path, text_data):
    with open(file_path, 'a') as file:
        file.write(text_data + '\n')



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

        # Create a custom SSLContext
        context = ssl.create_default_context()
        context.check_hostname = False  # Disable hostname checking
        context.verify_mode = ssl.CERT_REQUIRED  # Disable certificate verification
        context.load_verify_locations(self.manager_cert_path)

        # Create a custom adapter to use the SSL context
        class HostNameIgnoringAdapter(requests.adapters.HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                # 0/0
                kwargs['ssl_context'] = context
                kwargs['assert_hostname'] = False
                x = super().init_poolmanager(*args, **kwargs)
                return x

            def proxy_manager_for(self, *args, **kwargs):
                kwargs['ssl_context'] = context
                return super().proxy_manager_for(*args, **kwargs)


        # Mount the custom adapter
        adapter = HostNameIgnoringAdapter()
        session.mount('https://', adapter)

        client_cert = (self.worker_cert_path, self.worker_key_path)
        i = 0

        while True:
            try:
                t1 = time.time()
                response = session.get('%s:%d/want_work' % (self.url, self.port), cert=client_cert)

                # Check if the request was successful
                if response.status_code == 200:
                    try:
                        key_and_work = key_and_work_pb2.KeyAndWork()
                        key_and_work.ParseFromString(response.content)
                        k, data_to_process = key_and_work.key, key_and_work.data

                        # Unpickle the response content


                        if k==-1:
                            break
                        elif k==-2:
                            print("No tasks yet to perform. Waiting and trying again...")
                            continue
                        elif k >= 0:
                            # Process the unpickled data
                            print(f"Received key: {k}")
                            time.sleep(wait_between_finishes)

                            result = self.processing_fn(pickle.loads(data_to_process))
                            print(f"RRR", result)

                            key_and_work = key_and_work_pb2.KeyAndWork()
                            key_and_work.key = k
                            key_and_work.data = pickle.dumps(result)
                            serialized_data = key_and_work.SerializeToString()

                            for i in range(10):
                                try:
                                    print("Will post to", '%s/work_done:%d' % (self.url, self.port))
                                    # POST the pickled data back to the server
                                    response = session.post(
                                        '%s:%d/work_done' % (self.url, self.port),  # Update the URL to the correct endpoint
                                        data=serialized_data,
                                        #verify=self.manager_cert_path,  # Path to server's cert
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

                            print("Task took", time.time() - t1, "seconds")

                            write_to_file('time_info.txt', str(time.time() - t1))

                            print(response.status_code, response.content)

                    except pickle.UnpicklingError as e:
                        print(f"Error unpickling the response: {e}")
            except (OSError, requests.exceptions.ConnectionError) as e:
                if num_tries < num_tries_max or num_tries_max == -1:
                    print("Connection failed. Will try again.", file=sys.stderr)
                    num_tries += 1
                    time.sleep(wait_between_tries)
                else:
                    raise e
