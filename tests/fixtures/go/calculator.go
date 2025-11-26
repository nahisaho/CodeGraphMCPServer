// Sample Go file for testing
// Package calculator provides basic math operations.
package calculator

import (
	"fmt"
	"math"
)

// Calculator struct holds state for calculations
type Calculator struct {
	Memory float64
	History []float64
}

// Operation interface defines a math operation
type Operation interface {
	Execute(a, b float64) float64
	Name() string
}

// Add adds two numbers
func Add(a, b float64) float64 {
	return a + b
}

// Subtract subtracts b from a
func Subtract(a, b float64) float64 {
	return a - b
}

// Multiply multiplies two numbers
func Multiply(a, b float64) float64 {
	return a * b
}

// Divide divides a by b
func Divide(a, b float64) float64 {
	if b == 0 {
		return 0
	}
	return a / b
}

// Calculate performs an operation and stores result
func (c *Calculator) Calculate(op Operation, a, b float64) float64 {
	result := op.Execute(a, b)
	c.Memory = result
	c.History = append(c.History, result)
	return result
}

// Clear resets the calculator
func (c *Calculator) Clear() {
	c.Memory = 0
	c.History = nil
}

// GetHistory returns the calculation history
func (c Calculator) GetHistory() []float64 {
	return c.History
}

// SquareRoot returns the square root using math package
func SquareRoot(x float64) float64 {
	return math.Sqrt(x)
}

// PrintResult formats and prints a result
func PrintResult(result float64) {
	fmt.Printf("Result: %.2f\n", result)
}

// AddOperation implements Operation interface
type AddOperation struct{}

func (a AddOperation) Execute(x, y float64) float64 {
	return x + y
}

func (a AddOperation) Name() string {
	return "add"
}
