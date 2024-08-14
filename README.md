# StarCompute

Allows distribution of heavy processing workloads in star topology. In this context, the manager (labeled as such) is
the central node which is responsible for delegating the tasks to the worker nodes which are labeled as "workers".

## Setup

On Linux, `openssl` is automatically installed but on the mac, it might need to be installed. This
package is required for encrypting the connection.
```
brew install openssl
```

Navigate to a folder where you want to store yoru keys and then create keys first for the client:
```
openssl genpkey -algorithm RSA -out worker_key.pem
openssl req -x509 -new -key worker_key.pem -out worker_cert.pem -days 365
```
Create keys first for the server:
```
openssl genpkey -algorithm RSA -out manager_key.pem
openssl req -x509 -new -key manager_key.pem -out manager_cert.pem -days 365
```

Export the environmental variables:
```
export STARCOMPUTE_WORKER_CERT_PATH=`readlink -f worker_cert.pem`
export STARCOMPUTE_WORKER_KEY_PATH=`readlink -f worker_key.pem`
export STARCOMPUTE_MANAGER_CERT=`readlink -f manager_cert.pem`
export STARCOMPUTE_MANAGER_KEY_PATH=`readlink -f manager_key.pem`

```
These variables will have to be set every time before running the server and the client. So it might be useful to add
them to your `.bashrc` or another environmental file. The client should have access to client's key, certificate, and
server's certificate. The server should have access to client's certificate, server's key and server's certificate.

The package can be easily installed via pip3. The package is still in development so frequent updates need to be made.
```
pip3 install "git+https://github.com/shahrukhqasim/StarCompute"
```

## Run
First, run the manager:
```
python3 examples/run_example_manager.py
```
And then you can run one or multiple workers:
```
python3 examples/run_example_worker.py
```