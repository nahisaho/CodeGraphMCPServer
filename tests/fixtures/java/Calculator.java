package com.example.calculator;

import java.util.List;
import java.util.ArrayList;

/**
 * Calculator class for basic math operations.
 */
public class Calculator {
    private double memory;
    private List<Double> history;

    /**
     * Creates a new Calculator instance.
     */
    public Calculator() {
        this.memory = 0;
        this.history = new ArrayList<>();
    }

    /**
     * Adds two numbers.
     * @param a First number
     * @param b Second number
     * @return Sum of a and b
     */
    public double add(double a, double b) {
        double result = a + b;
        storeResult(result);
        return result;
    }

    /**
     * Subtracts b from a.
     */
    public double subtract(double a, double b) {
        double result = a - b;
        storeResult(result);
        return result;
    }

    /**
     * Multiplies two numbers.
     */
    public double multiply(double a, double b) {
        double result = a * b;
        storeResult(result);
        return result;
    }

    /**
     * Divides a by b.
     */
    public double divide(double a, double b) {
        if (b == 0) {
            throw new ArithmeticException("Division by zero");
        }
        double result = a / b;
        storeResult(result);
        return result;
    }

    private void storeResult(double result) {
        this.memory = result;
        this.history.add(result);
    }

    public double getMemory() {
        return memory;
    }

    public List<Double> getHistory() {
        return new ArrayList<>(history);
    }

    public void clear() {
        memory = 0;
        history.clear();
    }
}

/**
 * Operation interface for extensible operations.
 */
interface Operation {
    double execute(double a, double b);
    String getName();
}

/**
 * Addition operation implementation.
 */
class AddOperation implements Operation {
    @Override
    public double execute(double a, double b) {
        return a + b;
    }

    @Override
    public String getName() {
        return "add";
    }
}

/**
 * Operation type enumeration.
 */
enum OperationType {
    ADD,
    SUBTRACT,
    MULTIPLY,
    DIVIDE
}
