using System;
using System.Collections.Generic;

namespace Calculator.Math
{
    /// <summary>
    /// Interface for calculator operations.
    /// </summary>
    public interface ICalculator
    {
        int Add(int a, int b);
        int Subtract(int a, int b);
    }

    /// <summary>
    /// Basic calculator struct.
    /// </summary>
    public struct Point
    {
        public double X;
        public double Y;
        
        public Point(double x, double y)
        {
            X = x;
            Y = y;
        }
    }

    /// <summary>
    /// Enum for operation types.
    /// </summary>
    public enum Operation
    {
        Add,
        Subtract,
        Multiply,
        Divide
    }

    /// <summary>
    /// Calculator class implementing ICalculator.
    /// </summary>
    public class Calculator : ICalculator
    {
        private int _precision;

        public Calculator(int precision = 2)
        {
            _precision = precision;
        }

        public int Add(int a, int b)
        {
            return a + b;
        }

        public int Subtract(int a, int b)
        {
            return a - b;
        }

        public double Multiply(double a, double b)
        {
            return Math.Round(a * b, _precision);
        }

        public double Divide(double a, double b)
        {
            if (b == 0)
            {
                throw new DivideByZeroException("Cannot divide by zero");
            }
            return Math.Round(a / b, _precision);
        }
    }

    /// <summary>
    /// Advanced calculator with additional operations.
    /// </summary>
    public class AdvancedCalculator : Calculator
    {
        public double Power(double baseNum, int exponent)
        {
            return Math.Pow(baseNum, exponent);
        }

        public double SquareRoot(double number)
        {
            return Math.Sqrt(number);
        }
    }
}
