.PHONY: help install test test-unit test-integration test-slow test-coverage lint format clean run-api run-cli examples

# Default target
help:
	@echo "Pytest Demo - Available Commands"
	@echo "================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install         Install dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test            Run all tests"
	@echo "  test-unit       Run only unit tests"
	@echo "  test-integration Run only integration tests"
	@echo "  test-slow       Run slow tests"
	@echo "  test-coverage   Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint            Run linting checks"
	@echo "  format          Format code"
	@echo ""
	@echo "Development:"
	@echo "  run-api         Start the API server"
	@echo "  run-cli         Show CLI help"
	@echo "  examples        Run usage examples"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean           Clean temporary files"

# Installation
install:
	pip install -r requirements.txt

# Testing targets
test:
	pytest

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

test-slow:
	pytest -m slow

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 src tests
	mypy src tests --ignore-missing-imports

format:
	black src tests examples
	isort src tests examples

# Development
run-api:
	uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

run-cli:
	python -m src.cli --help

examples: run-examples

run-examples:
	python examples/run_examples.py

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf output/
	rm -f .coverage