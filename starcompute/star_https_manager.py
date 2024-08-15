import http.server
import pickle
import ssl
import os
import threading
import time
import queue
from urllib.parse import urlparse, parse_qs



class StarHttpsManager:
    def __init__(self, port):
        self.port = port

        self.worker_cert_path = os.getenv('STARCOMPUTE_WORKER_CERT_PATH')
        self.manager_cert_path = os.getenv('STARCOMPUTE_MANAGER_CERT_PATH')
        self.manager_key_path = os.getenv('STARCOMPUTE_MANAGER_KEY_PATH')

        if self.manager_cert_path is None or self.worker_cert_path is None or self.manager_key_path is None:
            err_str = ("Cannot find values of environmental variables for certificates and key. Make sure the"
                       "following environmental variables are set:\n1. STARCOMPUTE_WORKER_CERT_PATH\n"
                       "2. STARCOMPUTE_MANAGER_CERT_PATH\n3. STARCOMPUTE_MANAGER_KEY_PATH")

            raise RuntimeError(err_str)
        self.httpd = None

        self.send_queue = queue.Queue()
        self.max_k = 0
        self.results_dict = dict()
        self.results_dict_lock = threading.Lock()
        self.shutdown_flag = threading.Event()



    def handler_factory(self):
        def create_handler(*args, **kwargs):
            return RequestHandler(self, *args, **kwargs)

        return create_handler


    def run_manager(self):
        def _thread():
            # Create the HTTP server
            self.httpd = http.server.HTTPServer(('0.0.0.0', self.port), self.handler_factory())

            worker_cert_path = os.getenv('STARCOMPUTE_WORKER_CERT_PATH')
            manager_cert_path = os.getenv('STARCOMPUTE_MANAGER_CERT_PATH')
            manager_key_path = os.getenv('STARCOMPUTE_MANAGER_KEY_PATH')

            # Wrap the server's socket with SSL
            self.httpd.socket = ssl.wrap_socket(self.httpd.socket,
                                           keyfile=manager_key_path,  # Path to your private key
                                           certfile=manager_cert_path,  # Path to your certificate
                                           server_side=True,
                                           cert_reqs=ssl.CERT_REQUIRED,
                                           ca_certs=worker_cert_path)

            # Start the HTTPS server
            print("Serving on https://0.0.0.0:%d"%self.port)
            self.httpd.serve_forever()
            self.httpd.server_close()

        self.server_thread = threading.Thread(target=_thread)
        self.server_thread.start()

    def join(self):
        self.server_thread.join()

    def close(self, wait_to_acknowledge_worker=30):
        if self.httpd is None:
            raise RuntimeError("Cannot close a non running server")
        self.shutdown_flag.set()
        time.sleep(wait_to_acknowledge_worker) # wait 30 seconds before actually killing the server
        self.httpd.shutdown()

    def run_tasks(self, tasks, wait_resolution=0.01):
        """
        Distributes tasks to the worker nodes

        :param tasks: Tasks to perform
        :param wait_resolution: in seconds, how much to wait in between checks of completions
        :return:
        """
        assert len(self.results_dict) == 0

        to_get = []
        for t in tasks:
            t2 = self.max_k, t
            to_get.append(self.max_k)
            self.send_queue.put_nowait(t2)
            self.max_k += 1
        while len(self.results_dict) != len(to_get):
            time.sleep(wait_resolution)

        results = []
        for t in to_get:
            results.append(self.results_dict.pop(t))

        self.results_dict = dict()

        return results


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, star_manager : StarHttpsManager, *args, **kwargs):
        self.star_manager = star_manager
        super().__init__(*args, **kwargs)

    def do_GET(self):
        print(self.path)
        if self.path.startswith('/want_work'):
            try:
                k, data_to_process = self.star_manager.send_queue.get(timeout=2)
                pickled_data = pickle.dumps((k, data_to_process))
            except queue.Empty:
                if self.star_manager.shutdown_flag.is_set():
                    pickled_data = pickle.dumps((-1, None))
                else:
                    pickled_data = pickle.dumps((-2, None))

            # Send a basic response
            # pickle (k, data_to_process)
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.end_headers()
            # Send the pickled data as the response
            self.wfile.write(pickled_data)

        elif self.path.startswith('/check_in'):
            # Send a basic response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"You good!\n")

        elif self.path.startswith('/work_done'):
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)

            # Now you have a dictionary of query parameters
            print("Query Parameters:", query_params)
            # Send a basic response
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Please post it!\n")
        else:
            # Send a basic response
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"You doing something wrong bro...\n")

    def do_POST(self):
        # Determine the length of the data
        content_length = int(self.headers['Content-Length'])

        # Read the data from the request
        post_data = self.rfile.read(content_length)

        try:
            # Unpickle the data
            data = pickle.loads(post_data)

            # Assume the unpickled data is a tuple (k, processed_data)
            k, processed_data = data

            # Process the data (example: just print it)
            print(f"Received key: {k}")
            print(f"Received processed data: {processed_data}")

            with self.star_manager.results_dict_lock:
                self.star_manager.results_dict[k] = processed_data
                print("putting back in and it is now", len(self.star_manager.results_dict))
                in_processing = None

            # Send a response back to the client
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Data received and processed successfully\n")

        except (pickle.UnpicklingError, EOFError, TypeError) as e:
            # Handle errors in unpickling
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"Failed to unpickle data: {str(e)}".encode('utf-8'))

        except Exception as e:
            # Handle any other errors
            self.send_response(500)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"Internal server error: {str(e)}".encode('utf-8'))

