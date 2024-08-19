# StarCompute

Allows distribution of heavy processing workloads in star topology. In this context, the client (such as your laptop or
the small server node) sends the data that needs to be processed to a central node (called manager). The manager will
distribute the workload to a bunch of workers. These workers will send the result back to the manager, which will return
it to the client. In this way, the manager acts as the central node.

## Setup

In this package, the traffic is encrypted with SSL both ways because we are sending serialized data to the workers for
processing and it can very easily introduce big security vulnerabilities. Two-way certificate verification in HTTPS
connections, also known as mutual SSL/TLS authentication, involves both the client and server authenticating each
other's identities through digital certificates. In this process, the server first presents its certificate to the
client, which the client verifies against trusted certificate authorities. Once the server is authenticated, the
client also presents its certificate to the server for verification. This mutual authentication ensures that both
parties are who they claim to be, providing a higher level of security compared to standard one-way HTTPS, which only
verifies the server's identity. To create these certificates and keys, one can use `openssl`. On Linux, `openssl` is
already installed but on the mac, it might need to be installed. This package is required for encrypting the connection.
```
brew install openssl
```

To create your keys, navigate to a folder where you want to store your keys and then create keys and certificates first
for the client and the workers:
```

openssl genpkey -algorithm RSA -out client_key.pem
openssl req -x509 -new -key client_key.pem -out client_cert.pem -days 365

openssl genpkey -algorithm RSA -out worker_key.pem
openssl req -x509 -new -key worker_key.pem -out worker_cert.pem -days 365
```
And then create keys first for the manager:
```
openssl genpkey -algorithm RSA -out manager_key.pem
```

I did not manage to get self-signed certificates working at compute nodes with any IP address. Therefore we have to sign
it with the IP address of the server. Note that if you are running the manager on google cloud, shutting off the machine
and running it again will change the IP address and the certificate will need to be generated again.
```
openssl req -new -x509 -key manager_key.pem -out manager_cert.pem -days 365 \
-subj "/C=CG/ST=Zürich/L=Zürich/O=UZH/OU=physik/CN=shahrukhqasim" \
-addext "subjectAltName=DNS:shahrukhqasim.com,IP:34.65.93.243"
```



Export the environmental variables:
```
export STARCOMPUTE_WORKER_CERT_PATH=`readlink -f worker_cert.pem`
export STARCOMPUTE_WORKER_KEY_PATH=`readlink -f worker_key.pem`
export STARCOMPUTE_MANAGER_CERT=`readlink -f manager_cert.pem`
export STARCOMPUTE_MANAGER_KEY_PATH=`readlink -f manager_key.pem`
export STARCOMPUTE_CLIENT_CERT=`readlink -f client_cert.pem`
export STARCOMPUTE_CLIENT_KEY_PATH=`readlink -f client_key.pem`

```
These variables will have to be set every time before running the server and the client. So it might be useful to add
them to your `.bashrc` or another environmental file. The client should have access to client's key, certificate, and
server's certificate. The server should have access to client's certificate, server's key and server's certificate.

The package can be easily installed via pip3. The package is still in development so frequent updates need to be made.
```
pip3 install "git+https://github.com/shahrukhqasim/StarCompute"
```

## Run
First, run the manager. This has to be done in `golang` because python is very slow for server side connections (esp
if you multiple connections) 
```
cd manager
go run -x main.go -port=443 -client_port=444
```
(TODO: Instructions about installing go and the sub packages but it should be easy by googling around)

And then you can run one or multiple workers. Adjust the IP address as well as the port according to that of the
manager.
```
python3 examples/run_example_worker_https.py --port 443 --url https://34.65.93.243
```
Finally, you can run the client:
```
python3 examples/run_example_client.py --manager-ip 34.65.93.243 --port 444
```

