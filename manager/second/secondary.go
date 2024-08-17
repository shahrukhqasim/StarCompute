package main

import (
	"fmt"
	"sync"
	"time"
)

func main() {
	var (
		myMap = make(map[string]int)
		mu    sync.Mutex
		cond  = sync.NewCond(&mu)
	)

	// Goroutine to simulate adding an item to the map after some time
	go func() {
		time.Sleep(3 * time.Second) // Simulate some work
		mu.Lock()                   // Lock before modifying the map
		myMap["Alice"] = 25
		fmt.Println("Added Alice to the map")
		cond.Signal() // Signal the condition variable
		mu.Unlock()   // Unlock after modification
	}()

	// Main goroutine waiting for the item to be available in the map
	mu.Lock()
	for _, exists := myMap["Alice"]; !exists; _, exists = myMap["Alice"] {
		fmt.Println("Waiting for Alice to be added to the map...")
		cond.Wait() // Wait releases the lock and puts the goroutine to sleep
	}
	fmt.Println("Alice's age:", myMap["Alice"])
	mu.Unlock()
}
