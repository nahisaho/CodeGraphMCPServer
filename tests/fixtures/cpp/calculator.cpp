#include <iostream>
#include <cmath>
#include <stdexcept>

namespace Calculator {

/**
 * Base calculator class.
 */
class BaseCalculator {
public:
    virtual int add(int a, int b) = 0;
    virtual int subtract(int a, int b) = 0;
    virtual ~BaseCalculator() = default;
};

/**
 * Point struct for 2D coordinates.
 */
struct Point {
    double x;
    double y;
    
    Point(double x, double y) : x(x), y(y) {}
    
    double distance() const {
        return std::sqrt(x * x + y * y);
    }
};

/**
 * Calculator implementation.
 */
class Calculator : public BaseCalculator {
private:
    int precision;

public:
    Calculator(int prec = 2) : precision(prec) {}
    
    int add(int a, int b) override {
        return a + b;
    }
    
    int subtract(int a, int b) override {
        return a - b;
    }
    
    double multiply(double a, double b) {
        return a * b;
    }
    
    double divide(double a, double b) {
        if (b == 0) {
            throw std::invalid_argument("Division by zero");
        }
        return a / b;
    }
};

/**
 * Advanced calculator with extra operations.
 */
class AdvancedCalculator : public Calculator {
public:
    double power(double base, int exponent) {
        return std::pow(base, exponent);
    }
    
    double squareRoot(double number) {
        return std::sqrt(number);
    }
};

} // namespace Calculator

// Free function
int createDefaultPrecision() {
    return 2;
}
