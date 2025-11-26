# Calculator module for basic arithmetic operations.

require 'logger'

module Loggable
  def log(message)
    puts "[LOG] #{message}"
  end
end

module Calculator
  # Base calculator class
  class Base
    include Loggable
    
    attr_reader :precision
    
    def initialize(precision: 2)
      @precision = precision
      log("Calculator initialized with precision #{precision}")
    end
    
    def add(a, b)
      result = a + b
      log("Adding #{a} + #{b} = #{result}")
      result
    end
    
    def subtract(a, b)
      result = a - b
      log("Subtracting #{a} - #{b} = #{result}")
      result
    end
  end
  
  # Advanced calculator with more operations
  class Advanced < Base
    def multiply(a, b)
      (a * b).round(precision)
    end
    
    def divide(a, b)
      raise ArgumentError, "Division by zero" if b.zero?
      (a.to_f / b).round(precision)
    end
    
    def power(base, exponent)
      base ** exponent
    end
    
    def self.create_default
      new(precision: 2)
    end
  end
  
  # Scientific calculator module
  module Scientific
    def square_root(number)
      Math.sqrt(number)
    end
    
    def logarithm(number, base: Math::E)
      Math.log(number, base)
    end
  end
  
  # Full featured calculator
  class Full < Advanced
    include Scientific
    
    def factorial(n)
      return 1 if n <= 1
      n * factorial(n - 1)
    end
  end
end

def create_calculator(type: :basic, precision: 2)
  case type
  when :basic
    Calculator::Base.new(precision: precision)
  when :advanced
    Calculator::Advanced.new(precision: precision)
  when :full
    Calculator::Full.new(precision: precision)
  else
    raise ArgumentError, "Unknown calculator type: #{type}"
  end
end
