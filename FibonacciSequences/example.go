// Produce Fibonacci sequence for a given number of terms using loop, and recursion.

package main

import (
	"fmt"
)

func FibonacciRecursion(t int) int {
	// Recursively calculate fibonacci term.
	if t <= 1 {
		return t
	}
	return FibonacciRecursion(t-1) + FibonacciRecursion(t-2)
}

func main() {

	// Get maximum terms
	var n int
	fmt.Print("Enter a positive integer: ")
	fmt.Scanf("%d", &n)

	// Produce sequence using loop
	LoopSlice := make([]int, n+1, n+2)
	for i := 0; i <= n; i++ {
		if n < 2 {
			LoopSlice = LoopSlice[0:2]
		}
		LoopSlice[0] = 0
		LoopSlice[1] = 1
		for i := 2; i <= n; i++ {
			LoopSlice[i] = LoopSlice[i-1] + LoopSlice[i-2]
		}
	}
	fmt.Println("Fibonacci sequence (loop): ", LoopSlice)

	// Produce sequence using recursive function
	var RecursiveSlice []int
	for i := 0; i <= n; i++ {
		RecursiveSlice = append(RecursiveSlice, FibonacciRecursion(i))
	}
	fmt.Println("Fibonacci sequence (recursion): ", RecursiveSlice)
}
