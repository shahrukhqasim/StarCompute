package main

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"github.com/gorilla/websocket"
	"google.golang.org/protobuf/proto"
	"io/ioutil"
	"log"
	"manager/messages"
	"net/http"
	"os"
	"time"
)

// Handler function for the root URL "/"
func helloHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hello, World! This is served over HTTPS.")
}

// Function to get an environment variable or panic if not set
func getEnvOrPanic(envVar string) string {
	value, exists := os.LookupEnv(envVar)
	if !exists {
		panic(envVar + " is not set")
	}
	return value
}

// Define an upgrader
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	// Allow all connections by setting CheckOrigin to always return true.
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

// Define a struct to hold an int and an array
type KeyAndTask struct {
	Key  int32
	Task []uint8 // Example: array of 3 integers
}

type TheManager struct {
	maxK          int32
	dataToProcess chan KeyAndTask
	dataProcessed chan KeyAndTask
	// Add other dependencies as needed
}

func (h *TheManager) workDone(w http.ResponseWriter, r *http.Request) {
	log.Println("Work done.")

	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}
	// Ensure the Content-Type is application/octet-stream
	if r.Header.Get("Content-Type") != "application/octet-stream" {
		http.Error(w, "Invalid content type", http.StatusUnsupportedMediaType)
		return
	}

	// Read the request body
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Unable to read body", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// Convert the body to a []uint8 (which is the same as []byte)
	data := []uint8(body)

	newMsg := &messages.KeyAndWork{}
	err = proto.Unmarshal(data, newMsg)

	if err != nil {
		http.Error(w, "Error unmarshalling", http.StatusBadRequest)
		return
	}

	h.dataProcessed <- KeyAndTask{Key: newMsg.GetKey(), Task: newMsg.GetData()}

}

func (h *TheManager) wantWork(w http.ResponseWriter, r *http.Request) {
	var val KeyAndTask
	select {
	case val = <-h.dataToProcess:
		//_ = _
		//fmt.Println("To process:", val)
	case <-time.After(5 * time.Second):
		//fmt.Println("Timeout! No data received within 5 seconds.")
		val = KeyAndTask{Key: -2, Task: []uint8{}}
	}

	to_send := messages.KeyAndWork{Key: val.Key, Data: val.Task}
	data, err := proto.Marshal(&to_send)
	if err != nil {
		log.Fatalf("Failed to Task: %v", err)
	}

	// Set the status code to 200 OK
	w.WriteHeader(http.StatusOK)

	// Set the Content-Type header
	w.Header().Set("Content-Type", "application/octet-stream")

	// Serialize the data (you'll need to replace `yourData` with your actual data)
	if err != nil {
		http.Error(w, "Failed to serialize data", http.StatusInternalServerError)
		return
	}

	// Write the serialized data to the response
	w.Write(data)
}

// Handle WebSocket connections
func (h *TheManager) handleWebSocket(w http.ResponseWriter, r *http.Request) {

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("Upgrade error:", err)
		return
	}
	defer conn.Close()

	for {
		// Read message from browser
		msgType, msg, err := conn.ReadMessage()
		if err != nil {
			log.Println("Read error:", err)
			break
		}

		msgType, msg, err = conn.ReadMessage()
		if err != nil {
			log.Println("Read error:", err)
			break
		}

		newMsg := &messages.SerializedDataArray{}
		err = proto.Unmarshal(msg, newMsg)
		dat := newMsg.GetData()

		theLen := len(dat)

		set := make(map[int32]bool)
		take_keys := make([]int32, theLen)

		for i := 0; i < theLen; i++ {
			h.dataToProcess <- KeyAndTask{Key: h.maxK, Task: dat[i]}
			set[h.maxK] = true
			take_keys[i] = h.maxK
			h.maxK += 1
		}

		byteMap := make(map[int32][]byte)

		for {
			value, _ := <-h.dataProcessed
			if !set[value.Key] {
				continue
			}
			//log.Println("Got one!", value.Key, value.Task)
			byteMap[value.Key] = value.Task

			if (len(byteMap)) == theLen {
				break
			}
		}

		var resultBytes [][]uint8

		for i := 0; i < theLen; i++ {
			resultBytes = append(resultBytes, byteMap[take_keys[i]])
		}

		returnBack := messages.SerializedDataArray{Data: resultBytes}
		bytesToSendBack, err := proto.Marshal(&returnBack)

		//emptySlice := []byte{}

		//conn.WriteMessage(0, emptySlice)

		// Write message back to browser
		if err = conn.WriteMessage(msgType, bytesToSendBack); err != nil {
			log.Println("Write error:", err)
			break
		}
	}
}

func main() {
	handlerX := &TheManager{
		maxK:          1,
		dataToProcess: make(chan KeyAndTask, 10000),
		dataProcessed: make(chan KeyAndTask, 10000),
	}

	mux1 := http.NewServeMux()
	//mux1.HandleFunc("/", helloHandler)
	mux1.HandleFunc("/want_work", handlerX.wantWork)
	mux1.HandleFunc("/work_done", handlerX.workDone)

	keyFile := getEnvOrPanic("STARCOMPUTE_MANAGER_KEY_PATH")
	certFile := getEnvOrPanic("STARCOMPUTE_MANAGER_CERT_PATH")
	workerCertFile := getEnvOrPanic("STARCOMPUTE_WORKER_CERT_PATH")
	clientCertFile := getEnvOrPanic("STARCOMPUTE_CLIENT_CERT_PATH")

	// Load the client CA certificate
	workerCACert, err := ioutil.ReadFile(workerCertFile)
	if err != nil {
		fmt.Println("Failed to read client CA file:", err)
		return
	}
	// Load the client CA certificate
	clientCACert, err := ioutil.ReadFile(clientCertFile)
	if err != nil {
		fmt.Println("Failed to read client CA file:", err)
		return
	}

	// Create a pool with the client CA certificate
	workerCAPool := x509.NewCertPool()
	if !workerCAPool.AppendCertsFromPEM(workerCACert) {
		fmt.Println("Failed to append client CA certificate")
		return
	}

	clientCAPool := x509.NewCertPool()
	if !clientCAPool.AppendCertsFromPEM(clientCACert) {
		fmt.Println("Failed to append client CA certificate")
		return
	}

	// Create a TLS config that requires client certificates
	tlsConfig := &tls.Config{
		ClientCAs:          workerCAPool,
		ClientAuth:         tls.RequireAndVerifyClientCert,
		InsecureSkipVerify: true, // Allow self-signed certificates
	}

	// Create a TLS config that requires client certificates
	tlsConfig2 := &tls.Config{
		ClientCAs:          clientCAPool,
		ClientAuth:         tls.RequireAndVerifyClientCert,
		InsecureSkipVerify: true, // Allow self-signed certificates
	}

	server := &http.Server{
		Addr:      ":443",
		Handler:   mux1, // Default handler (uses http.DefaultServeMux)
		TLSConfig: tlsConfig,
	}

	go func() {
		// Start the HTTPS server with client certificate validation
		fmt.Println("Starting HTTPS server with client certificate validation on :443")
		if err := server.ListenAndServeTLS(certFile, keyFile); err != nil {
			fmt.Println("Failed to start server:", err)
		}
	}()

	mux2 := http.NewServeMux()

	mux2.HandleFunc("/", handlerX.handleWebSocket)

	server2 := &http.Server{
		Addr:      ":444",
		Handler:   mux2, // Default handler
		TLSConfig: tlsConfig2,
	}

	fmt.Println("WebSocket server started at :444 with TLS")
	if err := server2.ListenAndServeTLS(certFile, keyFile); err != nil {
		log.Fatal("ListenAndServeTLS error:", err)
	}

	select {}

}
