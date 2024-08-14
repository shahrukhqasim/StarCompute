# StarCompute

Allows distribution of heavy processing workloads in star topology. In this context, the server is the central node
which is responsible for delegating the tasks to the worker nodes which are labeled as clients.

## Setup

On Linux, `openssl` is automatically installed but on the mac, it might need to be installed. This
package is required for encrypting the connection.
```
brew install openssl
```

Navigate to a folder where you want to store yoru keys and then create keys first for the client:
```
openssl genpkey -algorithm RSA -out client_key.pem
openssl req -x509 -new -key client_key.pem -out client_cert.pem -days 365
```
Create keys first for the server:
```
openssl genpkey -algorithm RSA -out server_key.pem
openssl req -x509 -new -key server_key.pem -out server_cert.pem -days 365
```

Export the environmental variables:
```
export STARCOMPUTE_CLIENT_CERT_PATH=`readlink -f client_cert.pem`
export STARCOMPUTE_CLIENT_KEY_PATH=`readlink -f client_key.pem`
export STARCOMPUTE_SERVER_CERT=`readlink -f server_cert.pem`
export STARCOMPUTE_SERVER_KEY_PATH=`readlink -f server_key.pem`

```
These variables will have to be set every time before running the server and the client. So it might be useful to add
them to your `.bashrc` or another environmental file. The client should have access to client's key, certificate, and
server's certificate. The server should have access to client's certificate, server's key and server's certificate.

## Run
First, run the server:
```
python3 python/bin/run_example_server.py
```
And then you can run one or multiple clients:
```
python3 python/bin/run_example_client.py
```