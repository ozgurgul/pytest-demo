import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
from typing import Dict, List

from src.utils import FileManager, ConfigManager
from src.cli import APIClient, TaskManager

# Custom markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "api: marks tests that require API server")

# Fixtures for test data
@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30
    }

@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "title": "Complete project",
        "description": "Finish the pytest demo project",
        "completed": False,
        "user_id": "user-123"
    }

@pytest.fixture
def multiple_users():
    """Multiple user records for testing"""
    return [
        {"id": "1", "name": "Alice", "email": "alice@example.com", "age": 25},
        {"id": "2", "name": "Bob", "email": "bob@example.com", "age": 30},
        {"id": "3", "name": "Charlie", "email": "charlie@example.com", "age": 35},
    ]

@pytest.fixture
def multiple_tasks():
    """Multiple task records for testing"""
    return [
        {"id": "1", "title": "Task 1", "completed": True, "user_id": "1"},
        {"id": "2", "title": "Task 2", "completed": False, "user_id": "1"},
        {"id": "3", "title": "Task 3", "completed": False, "user_id": "2"},
        {"id": "4", "title": "Task 4", "completed": True, "user_id": "2"},
        {"id": "5", "title": "Task 5", "completed": False, "user_id": "3"},
    ]

# File system fixtures
@pytest.fixture
def temp_dir():
    """Temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def file_manager(temp_dir):
    """FileManager instance with temporary directory"""
    return FileManager(str(temp_dir))

@pytest.fixture
def sample_json_file(temp_dir):
    """Create a sample JSON file for testing"""
    data = {
        "users": [
            {"id": 1, "name": "Test User", "email": "test@example.com"}
        ],
        "settings": {
            "theme": "dark",
            "notifications": True
        }
    }
    
    file_path = temp_dir / "sample.json"
    with open(file_path, 'w') as f:
        import json
        json.dump(data, f)
    
    return file_path

# Mock fixtures
@pytest.fixture
def mock_api_client():
    """Mock API client for testing"""
    mock = Mock(spec=APIClient)
    
    # Configure common mock responses
    mock.health_check.return_value = {"status": "healthy", "version": "1.0.0"}
    mock.create_user.return_value = Mock(id="user-123", name="Test User", email="test@example.com", age=30)
    mock.get_users.return_value = []
    mock.create_task.return_value = Mock(id="task-123", title="Test Task", completed=False, user_id="user-123")
    mock.get_tasks.return_value = []
    
    return mock

@pytest.fixture
def mock_requests_session():
    """Mock requests session for API client testing"""
    mock = Mock()
    
    # Mock successful responses
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"status": "ok"}
    
    mock.get.return_value = mock_response
    mock.post.return_value = mock_response
    mock.put.return_value = mock_response
    mock.patch.return_value = mock_response
    mock.delete.return_value = mock_response
    
    return mock

@pytest.fixture
def task_manager(mock_api_client):
    """TaskManager instance with mock API client"""
    return TaskManager(mock_api_client)

# Configuration fixtures
@pytest.fixture
def config_manager(temp_dir):
    """ConfigManager with temporary directory"""
    config_file = temp_dir / "test_config.json"
    return ConfigManager(str(config_file))

# Parametrized data fixtures
@pytest.fixture(params=[
    ("valid@example.com", True),
    ("test.email+tag@domain.co.uk", True),
    ("invalid.email", False),
    ("@domain.com", False),
    ("user@", False),
    ("", False),
])
def email_validation_data(request):
    """Parametrized email validation test data"""
    return request.param

@pytest.fixture(params=[
    ("hello world", "hello-world"),
    ("Hello World!", "hello-world"),
    ("test   123", "test-123"),
    ("---test---", "test"),
    ("", ""),
])
def slugify_test_data(request):
    """Parametrized slugify test data"""
    return request.param

# Scoped fixtures
@pytest.fixture(scope="session")
def test_database():
    """Session-scoped test database"""
    # This would typically set up a test database
    # For demo purposes, we'll use a simple dict
    db = {"users": {}, "tasks": {}}
    yield db
    # Cleanup would happen here

@pytest.fixture(scope="module")
def api_server_config():
    """Module-scoped API server configuration"""
    return {
        "host": "localhost",
        "port": 8000,
        "debug": True,
        "testing": True
    }

# Autouse fixtures
@pytest.fixture(autouse=True)
def reset_environment():
    """Automatically reset environment for each test"""
    # This fixture runs before each test automatically
    # Useful for cleaning up global state
    yield
    # Cleanup after test

# Custom fixture factories
class UserFactory:
    """Factory for creating test users"""
    
    @staticmethod
    def create(name="Test User", email="test@example.com", age=25, **kwargs):
        """Create a user with default or custom values"""
        user_data = {
            "name": name,
            "email": email,
            "age": age,
            **kwargs
        }
        return user_data
    
    @staticmethod
    def create_batch(count=5, **base_kwargs):
        """Create multiple users"""
        users = []
        for i in range(count):
            user = UserFactory.create(
                name=f"User {i+1}",
                email=f"user{i+1}@example.com",
                **base_kwargs
            )
            users.append(user)
        return users

@pytest.fixture
def user_factory():
    """User factory fixture"""
    return UserFactory

class TaskFactory:
    """Factory for creating test tasks"""
    
    @staticmethod
    def create(title="Test Task", completed=False, user_id=None, **kwargs):
        """Create a task with default or custom values"""
        task_data = {
            "title": title,
            "completed": completed,
            "user_id": user_id,
            **kwargs
        }
        return task_data
    
    @staticmethod
    def create_batch(count=3, **base_kwargs):
        """Create multiple tasks"""
        tasks = []
        for i in range(count):
            task = TaskFactory.create(
                title=f"Task {i+1}",
                **base_kwargs
            )
            tasks.append(task)
        return tasks

@pytest.fixture
def task_factory():
    """Task factory fixture"""
    return TaskFactory