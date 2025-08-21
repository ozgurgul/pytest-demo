# Pytest Features Demonstrated

This document explains the various pytest features demonstrated in this project.

## Basic Testing

### Unit Tests (`tests/test_utils.py`)
- Basic test functions
- Test classes for organization  
- Assertion statements
- Test data setup

### Fixtures (`tests/conftest.py`)
- Function-scoped fixtures (default)
- Module-scoped fixtures (`api_server_config`)
- Session-scoped fixtures (`test_database`)
- Autouse fixtures (`reset_environment`)
- Fixture factories (`UserFactory`, `TaskFactory`)

## Advanced Features

### Parametrized Tests
Tests that run multiple times with different inputs:
```python
@pytest.mark.parametrize("email,expected", [
    ("valid@example.com", True),
    ("invalid.email", False),
])
def test_validate_email(email, expected):
    assert EmailValidator.validate(email) == expected
```

### Custom Markers
Organize and filter tests with custom markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.api` - Tests requiring API server

Run specific test categories:
```bash
pytest -m unit          # Run only unit tests
pytest -m "not slow"    # Skip slow tests
pytest -m integration   # Run only integration tests
```

### Mocking (`tests/test_cli.py`)
Mock external dependencies and APIs:
```python
@patch('src.cli.requests.Session')
def test_health_check_success(self, mock_session_class):
    # Setup mock behavior
    mock_session = Mock()
    mock_response = Mock()
    mock_response.json.return_value = {"status": "healthy"}
    mock_session.get.return_value = mock_response
    mock_session_class.return_value = mock_session
    
    # Test with mock
    client = APIClient()
    result = client.health_check()
    assert result == {"status": "healthy"}
```

### Test Configuration (`pytest.ini`)
- Marker registration
- Test discovery patterns  
- Warning filters
- Logging configuration
- Coverage settings

### Exception Testing
Test that code properly raises exceptions:
```python
def test_validate_strict_failure(self):
    with pytest.raises(ValidationError, match="Invalid email format"):
        EmailValidator.validate_strict("invalid-email")
```

### FastAPI Testing (`tests/test_api.py`)
Integration testing with FastAPI test client:
```python
def test_create_user_success(self, client, sample_user):
    response = client.post("/users", json=sample_user)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_user["name"]
```

### CLI Testing
Test command-line interfaces with Click's test runner:
```python
def test_health_command_success(self):
    runner = CliRunner()
    result = runner.invoke(cli, ['health'])
    assert result.exit_code == 0
    assert "API Status: healthy" in result.output
```

## Test Organization

### File Structure
- `tests/conftest.py` - Shared fixtures and configuration
- `tests/test_*.py` - Test modules following naming convention
- `pytest.ini` - Project-wide pytest configuration

### Test Naming
- Test files: `test_*.py` or `*_test.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Test Categories
Tests are organized by type and purpose:
- **Unit tests**: Test individual functions/methods in isolation
- **Integration tests**: Test component interactions
- **API tests**: Test HTTP endpoints with test client
- **CLI tests**: Test command-line interface
- **Slow tests**: Performance or long-running tests

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_utils.py

# Run specific test function
pytest tests/test_utils.py::TestEmailValidator::test_validate

# Run tests matching pattern
pytest -k "email"
```

### Coverage Reporting
```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

### Parallel Execution
```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### Output Options
```bash
# Generate HTML report
pytest --html=output/report.html

# Generate JSON report  
pytest --json-report --json-report-file=output/report.json
```

## Best Practices Demonstrated

1. **Isolation**: Each test runs independently with clean state
2. **Fixtures**: Reusable test data and setup code
3. **Mocking**: Test units in isolation by mocking dependencies  
4. **Parametrization**: Test multiple scenarios efficiently
5. **Organization**: Clear test structure with meaningful names
6. **Documentation**: Tests serve as living documentation
7. **CI/CD Ready**: Configuration suitable for continuous integration

## Common Patterns

### Test Data Factories
Create test data with sensible defaults:
```python
class UserFactory:
    @staticmethod
    def create(name="Test User", email="test@example.com", **kwargs):
        return {"name": name, "email": email, **kwargs}
```

### Setup and Teardown
Use fixtures for resource management:
```python
@pytest.fixture
def temp_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)  # Cleanup
```

### Error Testing
Verify error conditions:
```python
def test_invalid_input(self):
    with pytest.raises(ValueError, match="Expected error message"):
        function_that_should_fail("invalid input")
```

This project demonstrates these features in a practical, real-world context with API and CLI components.