import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.cli import APIClient, TaskManager, cli
from src.utils import ValidationError

# Mark this module as integration tests
pytestmark = pytest.mark.integration

class TestAPIClient:
    """Test cases for APIClient"""
    
    def test_init_default_url(self):
        """Test APIClient initialization with default URL"""
        client = APIClient()
        assert client.base_url == "http://localhost:8000"
    
    def test_init_custom_url(self):
        """Test APIClient initialization with custom URL"""
        client = APIClient("https://api.example.com/")
        assert client.base_url == "https://api.example.com"  # Should strip trailing slash
    
    @patch('src.cli.requests.Session')
    def test_health_check_success(self, mock_session_class):
        """Test successful health check"""
        # Setup mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"status": "healthy", "version": "1.0.0"}
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = APIClient()
        result = client.health_check()
        
        assert result == {"status": "healthy", "version": "1.0.0"}
        mock_session.get.assert_called_once_with("http://localhost:8000/health")
        mock_response.raise_for_status.assert_called_once()
    
    @patch('src.cli.requests.Session')
    def test_health_check_connection_error(self, mock_session_class):
        """Test health check with connection error"""
        # Setup mock to raise exception
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        mock_session_class.return_value = mock_session
        
        client = APIClient()
        
        with pytest.raises(ConnectionError, match="Failed to connect to API"):
            client.health_check()
    
    @patch('src.cli.requests.Session')
    def test_create_user_success(self, mock_session_class):
        """Test successful user creation"""
        # Setup mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "user-123",
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = APIClient()
        user = client.create_user("John Doe", "john@example.com", 30)
        
        assert user.id == "user-123"
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.age == 30
        
        mock_session.post.assert_called_once_with(
            "http://localhost:8000/users",
            json={"name": "John Doe", "email": "john@example.com", "age": 30}
        )
    
    @patch('src.cli.requests.Session')
    def test_create_user_without_age(self, mock_session_class):
        """Test user creation without age"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "user-123",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "age": None
        }
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = APIClient()
        user = client.create_user("Jane Doe", "jane@example.com")
        
        mock_session.post.assert_called_once_with(
            "http://localhost:8000/users",
            json={"name": "Jane Doe", "email": "jane@example.com"}
        )
    
    @patch('src.cli.requests.Session')
    def test_get_tasks_with_filters(self, mock_session_class):
        """Test getting tasks with filters"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "task-1", "title": "Task 1", "completed": True, "user_id": "user-1"}
        ]
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = APIClient()
        tasks = client.get_tasks(completed=True, user_id="user-1")
        
        assert len(tasks) == 1
        assert tasks[0].id == "task-1"
        
        mock_session.get.assert_called_once_with(
            "http://localhost:8000/tasks",
            params={"completed": True, "user_id": "user-1"}
        )
    
    @patch('src.cli.requests.Session')
    def test_complete_task(self, mock_session_class):
        """Test completing a task"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "task-1",
            "title": "Task 1",
            "completed": True,
            "user_id": "user-1"
        }
        mock_session.patch.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = APIClient()
        task = client.complete_task("task-1")
        
        assert task.completed is True
        mock_session.patch.assert_called_once_with(
            "http://localhost:8000/tasks/task-1/complete"
        )

class TestTaskManager:
    """Test cases for TaskManager"""
    
    def test_validate_email_valid(self, task_manager):
        """Test email validation with valid emails"""
        assert task_manager.validate_email("test@example.com") is True
        assert task_manager.validate_email("user.name+tag@domain.co.uk") is True
    
    def test_validate_email_invalid(self, task_manager):
        """Test email validation with invalid emails"""
        assert task_manager.validate_email("invalid") is False
        assert task_manager.validate_email("@domain.com") is False
        assert task_manager.validate_email("") is False
    
    @pytest.mark.parametrize("age,expected", [
        (0, True),
        (25, True),
        (150, True),
        (-1, False),
        (151, False),
        (1000, False),
    ])
    def test_validate_age(self, task_manager, age, expected):
        """Test age validation"""
        assert task_manager.validate_age(age) == expected
    
    def test_create_user_with_validation_success(self, mock_api_client):
        """Test successful user creation with validation"""
        task_manager = TaskManager(mock_api_client)
        
        # Configure mock to return user
        mock_user = Mock()
        mock_api_client.create_user.return_value = mock_user
        
        result = task_manager.create_user_with_validation("John Doe", "john@example.com", 30)
        
        assert result == mock_user
        mock_api_client.create_user.assert_called_once_with("John Doe", "john@example.com", 30)
    
    def test_create_user_with_validation_empty_name(self, task_manager):
        """Test user creation with empty name"""
        with pytest.raises(ValueError, match="Name cannot be empty"):
            task_manager.create_user_with_validation("", "john@example.com")
        
        with pytest.raises(ValueError, match="Name cannot be empty"):
            task_manager.create_user_with_validation("   ", "john@example.com")
    
    def test_create_user_with_validation_invalid_email(self, task_manager):
        """Test user creation with invalid email"""
        with pytest.raises(ValueError, match="Invalid email format"):
            task_manager.create_user_with_validation("John Doe", "invalid-email")
    
    def test_create_user_with_validation_invalid_age(self, task_manager):
        """Test user creation with invalid age"""
        with pytest.raises(ValueError, match="Age must be between 0 and 150"):
            task_manager.create_user_with_validation("John Doe", "john@example.com", -5)
        
        with pytest.raises(ValueError, match="Age must be between 0 and 150"):
            task_manager.create_user_with_validation("John Doe", "john@example.com", 200)
    
    def test_get_user_task_summary(self, mock_api_client):
        """Test getting user task summary"""
        task_manager = TaskManager(mock_api_client)
        
        # Configure mocks
        mock_user = Mock(id="user-1", name="John Doe", email="john@example.com")
        mock_tasks = [
            Mock(id="task-1", completed=True),
            Mock(id="task-2", completed=False),
            Mock(id="task-3", completed=True),
            Mock(id="task-4", completed=False),
        ]
        
        mock_api_client.get_user.return_value = mock_user
        mock_api_client.get_tasks.return_value = mock_tasks
        
        result = task_manager.get_user_task_summary("user-1")
        
        assert result["user"] == mock_user
        assert result["total_tasks"] == 4
        assert result["completed_tasks"] == 2
        assert result["pending_tasks"] == 2
        assert result["completion_rate"] == 0.5
        
        mock_api_client.get_user.assert_called_once_with("user-1")
        mock_api_client.get_tasks.assert_called_once_with(user_id="user-1")
    
    def test_get_user_task_summary_no_tasks(self, mock_api_client):
        """Test user task summary with no tasks"""
        task_manager = TaskManager(mock_api_client)
        
        mock_user = Mock(id="user-1", name="John Doe")
        mock_api_client.get_user.return_value = mock_user
        mock_api_client.get_tasks.return_value = []
        
        result = task_manager.get_user_task_summary("user-1")
        
        assert result["total_tasks"] == 0
        assert result["completion_rate"] == 0

class TestCLICommands:
    """Test cases for CLI commands"""
    
    def test_health_command_success(self):
        """Test health command with successful response"""
        runner = CliRunner()
        
        with patch('src.cli.APIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.health_check.return_value = {"status": "healthy", "version": "1.0.0"}
            mock_client_class.return_value = mock_client
            
            result = runner.invoke(cli, ['health'])
            
            assert result.exit_code == 0
            assert "API Status: healthy" in result.output
            assert "Version: 1.0.0" in result.output
    
    def test_health_command_connection_error(self):
        """Test health command with connection error"""
        runner = CliRunner()
        
        with patch('src.cli.APIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.health_check.side_effect = ConnectionError("Connection failed")
            mock_client_class.return_value = mock_client
            
            result = runner.invoke(cli, ['health'])
            
            assert result.exit_code == 1  # Should abort
            assert "Error: Connection failed" in result.output
    
    def test_create_user_command_success(self):
        """Test create user command with valid input"""
        runner = CliRunner()
        
        with patch('src.cli.TaskManager') as mock_manager_class:
            mock_manager = Mock()
            mock_user = Mock(name="John Doe", id="user-123")
            mock_manager.create_user_with_validation.return_value = mock_user
            mock_manager_class.return_value = mock_manager
            
            result = runner.invoke(cli, [
                'create-user',
                '--name', 'John Doe',
                '--email', 'john@example.com',
                '--age', '30'
            ])
            
            assert result.exit_code == 0
            assert "Created user: John Doe (user-123)" in result.output
            mock_manager.create_user_with_validation.assert_called_once_with(
                "John Doe", "john@example.com", 30
            )
    
    def test_create_user_command_validation_error(self):
        """Test create user command with validation error"""
        runner = CliRunner()
        
        with patch('src.cli.TaskManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager.create_user_with_validation.side_effect = ValueError("Invalid email format")
            mock_manager_class.return_value = mock_manager
            
            result = runner.invoke(cli, [
                'create-user',
                '--name', 'John Doe',
                '--email', 'invalid-email'
            ])
            
            assert result.exit_code == 1
            assert "Validation error: Invalid email format" in result.output
    
    def test_list_users_command_with_users(self):
        """Test list users command when users exist"""
        runner = CliRunner()
        
        with patch('src.cli.APIClient') as mock_client_class:
            mock_client = Mock()
            mock_users = [
                Mock(name="John Doe", email="john@example.com", age=30, id="user-1"),
                Mock(name="Jane Smith", email="jane@example.com", age=None, id="user-2"),
            ]
            mock_client.get_users.return_value = mock_users
            mock_client_class.return_value = mock_client
            
            result = runner.invoke(cli, ['list-users'])
            
            assert result.exit_code == 0
            assert "Users:" in result.output
            assert "John Doe - john@example.com (age: 30)" in result.output
            assert "Jane Smith - jane@example.com" in result.output
    
    def test_list_users_command_no_users(self):
        """Test list users command when no users exist"""
        runner = CliRunner()
        
        with patch('src.cli.APIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_users.return_value = []
            mock_client_class.return_value = mock_client
            
            result = runner.invoke(cli, ['list-users'])
            
            assert result.exit_code == 0
            assert "No users found." in result.output
    
    def test_create_task_command_success(self):
        """Test create task command"""
        runner = CliRunner()
        
        with patch('src.cli.APIClient') as mock_client_class:
            mock_client = Mock()
            mock_task = Mock(title="Test Task", id="task-123")
            mock_client.create_task.return_value = mock_task
            mock_client_class.return_value = mock_client
            
            result = runner.invoke(cli, [
                'create-task',
                '--title', 'Test Task',
                '--description', 'Test description',
                '--user-id', 'user-123'
            ])
            
            assert result.exit_code == 0
            assert "Created task: Test Task [ID: task-123]" in result.output
            mock_client.create_task.assert_called_once_with(
                "Test Task", "Test description", "user-123"
            )
    
    def test_list_tasks_command_with_filters(self):
        """Test list tasks command with filters"""
        runner = CliRunner()
        
        with patch('src.cli.APIClient') as mock_client_class:
            mock_client = Mock()
            mock_tasks = [
                Mock(title="Task 1", completed=True, user_id="user-1", id="task-1", description=None),
                Mock(title="Task 2", completed=False, user_id="user-1", id="task-2", description="Description"),
            ]
            mock_client.get_tasks.return_value = mock_tasks
            mock_client_class.return_value = mock_client
            
            result = runner.invoke(cli, [
                'list-tasks',
                '--completed', 'false',
                '--user-id', 'user-1'
            ])
            
            assert result.exit_code == 0
            assert "Tasks:" in result.output
            mock_client.get_tasks.assert_called_once_with(completed=False, user_id="user-1")
    
    def test_complete_task_command(self):
        """Test complete task command"""
        runner = CliRunner()
        
        with patch('src.cli.APIClient') as mock_client_class:
            mock_client = Mock()
            mock_task = Mock(title="Completed Task")
            mock_client.complete_task.return_value = mock_task
            mock_client_class.return_value = mock_client
            
            result = runner.invoke(cli, ['complete-task', 'task-123'])
            
            assert result.exit_code == 0
            assert "Completed task: Completed Task" in result.output
            mock_client.complete_task.assert_called_once_with("task-123")
    
    def test_user_summary_command(self):
        """Test user summary command"""
        runner = CliRunner()
        
        with patch('src.cli.TaskManager') as mock_manager_class:
            mock_manager = Mock()
            mock_summary = {
                "user": Mock(name="John Doe", email="john@example.com"),
                "total_tasks": 10,
                "completed_tasks": 7,
                "pending_tasks": 3,
                "completion_rate": 0.7
            }
            mock_manager.get_user_task_summary.return_value = mock_summary
            mock_manager_class.return_value = mock_manager
            
            result = runner.invoke(cli, ['user-summary', 'user-123'])
            
            assert result.exit_code == 0
            assert "User Summary for John Doe" in result.output
            assert "Total tasks: 10" in result.output
            assert "Completed: 7" in result.output
            assert "Pending: 3" in result.output
            assert "Completion rate: 70.0%" in result.output

# API integration tests (requires running server)
@pytest.mark.api
class TestAPIIntegration:
    """Integration tests that require a running API server"""
    
    def test_full_user_workflow(self):
        """Test complete user workflow"""
        pytest.skip("Requires running API server")
        
        client = APIClient()
        
        # Health check
        health = client.health_check()
        assert health["status"] == "healthy"
        
        # Create user
        user = client.create_user("Integration Test", "test@example.com", 25)
        assert user.name == "Integration Test"
        
        # Get users
        users = client.get_users()
        assert len(users) > 0
        
        # Create task for user
        task = client.create_task("Test Task", "Test Description", user.id)
        assert task.title == "Test Task"
        
        # Complete task
        completed_task = client.complete_task(task.id)
        assert completed_task.completed is True