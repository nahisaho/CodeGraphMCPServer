<?php
/**
 * Calculator class for basic arithmetic operations.
 */
namespace App\Math;

use App\Interfaces\CalculatorInterface;
use App\Traits\Loggable;

interface CalculatorInterface {
    public function add(int $a, int $b): int;
    public function subtract(int $a, int $b): int;
}

trait Loggable {
    public function log(string $message): void {
        echo "[LOG] " . $message . "\n";
    }
}

class Calculator implements CalculatorInterface {
    use Loggable;
    
    private int $precision;
    
    public function __construct(int $precision = 2) {
        $this->precision = $precision;
        $this->log("Calculator initialized");
    }
    
    public function add(int $a, int $b): int {
        $result = $a + $b;
        $this->log("Adding $a + $b = $result");
        return $result;
    }
    
    public function subtract(int $a, int $b): int {
        $result = $a - $b;
        $this->log("Subtracting $a - $b = $result");
        return $result;
    }
    
    public function multiply(float $a, float $b): float {
        return round($a * $b, $this->precision);
    }
    
    public function divide(float $a, float $b): float {
        if ($b === 0.0) {
            throw new \InvalidArgumentException("Division by zero");
        }
        return round($a / $b, $this->precision);
    }
}

class AdvancedCalculator extends Calculator {
    public function power(float $base, int $exponent): float {
        return pow($base, $exponent);
    }
    
    public function squareRoot(float $number): float {
        return sqrt($number);
    }
}

function createCalculator(int $precision = 2): Calculator {
    return new Calculator($precision);
}
