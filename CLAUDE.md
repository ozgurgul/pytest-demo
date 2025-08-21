# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive pytest demonstration repository showcasing modern Python testing practices. It includes a FastAPI web API, a Click-based CLI application, and extensive test suites demonstrating various pytest features.

### Architecture
- **API Layer** (`src/api.py`): FastAPI-based REST API for user and task management
- **CLI Layer** (`src/cli.py`): Click-based command-line interface with API client
- **Utilities** (`src/utils.py`): Common utilities and business logic components  
- **Tests** (`tests/`): Comprehensive test suites demonstrating pytest features

## Development Setup

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
# Start API server (runs on http://localhost:8000)
uvicorn src.api:app --reload

# Or use Make target
make run-api

# Use CLI (requires running API server)
python -m src.cli --help # /usr/local/opt/python@3.10/bin/python3.10 -m src.cli --help
python -m src.cli health
python -m src.cli create-user --name "John Doe" --email "john@example.com"
```

## Testing Commands

### Basic Testing
- `pytest` - Run all tests
- `pytest -v` - Run tests with verbose output
- `pytest -x` - Stop after first failure
- `pytest --tb=short` - Shorter traceback format

### Test Categories (using custom markers)
- `pytest -m unit` - Run only unit tests
- `pytest -m integration` - Run only integration tests  
- `pytest -m "not slow"` - Skip slow tests
- `pytest -m api` - Run API integration tests (requires running server)

### Specific Test Execution
- `pytest tests/test_utils.py` - Run specific test file
- `pytest tests/test_utils.py::TestEmailValidator` - Run specific test class
- `pytest tests/test_utils.py::TestEmailValidator::test_validate` - Run specific test
- `pytest -k "email"` - Run tests matching keyword

### Coverage and Reporting
- `pytest --cov=src` - Run with coverage
- `pytest --cov=src --cov-report=html` - Generate HTML coverage report
- `pytest --cov=src --cov-report=term-missing --cov-fail-under=80` - Coverage with threshold
- `pytest --html=output/report.html` - Generate HTML test report

### Development Testing
- `pytest --lf` - Run only tests that failed in last run
- `pytest --ff` - Run failed tests first, then remaining tests
- `pytest -n auto` - Run tests in parallel (requires pytest-xdist)

## Make Targets

The project includes a Makefile with common development commands:

- `make install` - Install dependencies
- `make test` - Run all tests
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests only
- `make test-coverage` - Run tests with coverage report
- `make lint` - Run code linting (flake8, mypy)
- `make format` - Format code (black, isort)
- `make run-api` - Start API server
- `make examples` - Run usage examples
- `make clean` - Clean temporary files

## Project Structure

```
├── src/                    # Source code
│   ├── api.py             # FastAPI REST API
│   ├── cli.py             # Click CLI application  
│   └── utils.py           # Utility functions
├── tests/                 # Test suites
│   ├── conftest.py        # Pytest fixtures and configuration
│   ├── test_utils.py      # Unit tests for utilities
│   ├── test_cli.py        # Integration tests for CLI
│   └── test_api.py        # API integration tests
├── examples/              # Usage examples
├── docs/                  # Documentation
├── output/                # Test outputs and reports
├── config/                # Configuration files
├── requirements.txt       # Python dependencies
├── pytest.ini            # Pytest configuration
└── Makefile              # Development commands
```

## Key Testing Features Demonstrated

### Fixtures (`tests/conftest.py`)
- Function, module, and session-scoped fixtures
- Fixture factories for test data creation
- Mock fixtures for external dependencies
- Autouse fixtures for environment setup

### Parametrized Tests
- Email validation with multiple test cases
- Data processing with various inputs
- String manipulation edge cases

### Mocking and Patching
- HTTP requests mocking for API client tests
- External dependency isolation
- Mock configuration and assertions

### Custom Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.api` - Tests requiring API server

### FastAPI Testing
- Test client usage for API endpoints
- Request/response validation
- Error condition testing
- Database state management

### CLI Testing
- Click command testing with CliRunner
- Input/output validation
- Error handling verification

## Configuration

### pytest.ini
- Custom markers registration
- Test discovery patterns
- Warning filters
- Coverage settings
- Logging configuration

### Test Data Management
- Factory pattern for test data creation
- Temporary file/directory fixtures
- Database reset utilities
- Mock data generation

When running linting and type checking, use:
- `flake8 src tests` for style checking
- `mypy src tests --ignore-missing-imports` for type checking
- `black src tests` for code formatting
- `isort src tests` for import sorting