# CHANGE-004: v0.3.0 Language Expansion

## Overview
Added support for 5 new programming languages: PHP, C#, C++, HCL (Terraform), and Ruby.

## Changes Made

### New Language Extractors
1. **PHP** (`src/codegraph_mcp/languages/php.py`)
   - Classes, interfaces, traits
   - Methods, functions
   - Namespaces
   - Inheritance and implements relations

2. **C#** (`src/codegraph_mcp/languages/csharp.py`)
   - Classes, structs, interfaces, enums
   - Methods, constructors, properties
   - Namespaces
   - Using directives

3. **C++** (`src/codegraph_mcp/languages/cpp.py`)
   - Classes, structs
   - Functions, methods (including header declarations)
   - Namespaces
   - Include directives
   - Template support

4. **HCL** (`src/codegraph_mcp/languages/hcl.py`)
   - Resources, data sources
   - Variables, outputs
   - Modules, locals
   - Providers

5. **Ruby** (`src/codegraph_mcp/languages/ruby.py`)
   - Classes, modules
   - Methods, singleton methods
   - require/require_relative
   - Module include/extend

### Test Fixtures
- `tests/fixtures/php/calculator.php`
- `tests/fixtures/csharp/Calculator.cs`
- `tests/fixtures/cpp/calculator.cpp`
- `tests/fixtures/hcl/main.tf`
- `tests/fixtures/ruby/calculator.rb`

### Test Files
- `tests/unit/test_php.py` - 15 tests
- `tests/unit/test_csharp.py` - 15 tests
- `tests/unit/test_cpp.py` - 14 tests
- `tests/unit/test_hcl.py` - 13 tests
- `tests/unit/test_ruby.py` - 16 tests

### Dependencies Added
- `tree-sitter-php>=0.23.0`
- `tree-sitter-c-sharp>=0.23.0`
- `tree-sitter-cpp>=0.23.0`
- `tree-sitter-hcl>=0.23.0`
- `tree-sitter-ruby>=0.23.0`

## Supported Languages Summary (11 total)
| Version | Languages |
|---------|-----------|
| v0.1.0 | Python, TypeScript, JavaScript, Rust |
| v0.2.0 | + Go, Java |
| v0.3.0 | + PHP, C#, C++, HCL, Ruby |

## Test Results
- Total tests: 286 (73 new)
- All tests passing
- Code coverage: maintained

## Version
- pyproject.toml updated to 0.3.0
- CHANGELOG.md updated

## Release Checklist
- [x] Extractors implemented
- [x] Tests written and passing
- [x] Dependencies added
- [x] CHANGELOG updated
- [ ] Git commit and tag
- [ ] PyPI release
- [ ] GitHub release
