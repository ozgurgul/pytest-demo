import pytest
from fastapi.testclient import TestClient
import json

from src.api import app, reset_database, get_database_stats

# Mark this module as integration tests
pytestmark = pytest.mark.integration

@pytest.fixture
def client():
    """FastAPI test client"""
    with TestClient(app) as test_client:
        # Reset database before each test
        reset_database()
        yield test_client
        # Clean up after test
        reset_database()

@pytest.fixture
def sample_user():
    """Sample user data"""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30
    }

@pytest.fixture
def sample_task():
    """Sample task data"""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "completed": False
    }

class TestRootEndpoints:
    """Test root and utility endpoints"""
    
    def test_read_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to Demo API"}
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

class TestUserEndpoints:
    """Test user-related endpoints"""
    
    def test_create_user_success(self, client, sample_user):
        """Test successful user creation"""
        response = client.post("/users", json=sample_user)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["name"] == sample_user["name"]
        assert data["email"] == sample_user["email"]
        assert data["age"] == sample_user["age"]
    
    def test_create_user_without_age(self, client):
        """Test creating user without age"""
        user_data = {
            "name": "Jane Doe",
            "email": "jane@example.com"
        }
        
        response = client.post("/users", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Jane Doe"
        assert data["age"] is None
    
    def test_create_user_invalid_data(self, client):
        """Test creating user with invalid data"""
        invalid_data = {
            "name": "",  # Empty name should be handled by Pydantic
            "email": "invalid-email"
        }
        
        response = client.post("/users", json=invalid_data)
        # The API doesn't validate email format in the model, so this should succeed
        # In a real app, you might want to add validation
        assert response.status_code == 200
    
    def test_get_users_empty(self, client):
        """Test getting users when none exist"""
        response = client.get("/users")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_users_with_data(self, client, sample_user):
        """Test getting users when some exist"""
        # Create a user first
        create_response = client.post("/users", json=sample_user)
        user_id = create_response.json()["id"]
        
        # Get users
        response = client.get("/users")
        assert response.status_code == 200
        
        users = response.json()
        assert len(users) == 1
        assert users[0]["id"] == user_id
        assert users[0]["name"] == sample_user["name"]
    
    def test_get_user_by_id(self, client, sample_user):
        """Test getting specific user by ID"""
        # Create user
        create_response = client.post("/users", json=sample_user)
        user_id = create_response.json()["id"]
        
        # Get user by ID
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        
        user = response.json()
        assert user["id"] == user_id
        assert user["name"] == sample_user["name"]
    
    def test_get_user_not_found(self, client):
        """Test getting non-existent user"""
        response = client.get("/users/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
    
    def test_update_user(self, client, sample_user):
        """Test updating user"""
        # Create user
        create_response = client.post("/users", json=sample_user)
        user_id = create_response.json()["id"]
        
        # Update user
        updated_data = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "age": 25
        }
        
        response = client.put(f"/users/{user_id}", json=updated_data)
        assert response.status_code == 200
        
        user = response.json()
        assert user["id"] == user_id
        assert user["name"] == "Jane Smith"
        assert user["email"] == "jane@example.com"
        assert user["age"] == 25
    
    def test_update_user_not_found(self, client, sample_user):
        """Test updating non-existent user"""
        response = client.put("/users/nonexistent-id", json=sample_user)
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
    
    def test_delete_user(self, client, sample_user):
        """Test deleting user"""
        # Create user
        create_response = client.post("/users", json=sample_user)
        user_id = create_response.json()["id"]
        
        # Delete user
        response = client.delete(f"/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully"
        
        # Verify user is deleted
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 404
    
    def test_delete_user_not_found(self, client):
        """Test deleting non-existent user"""
        response = client.delete("/users/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
    
    def test_delete_user_with_tasks(self, client, sample_user, sample_task):
        """Test deleting user also deletes their tasks"""
        # Create user
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]
        
        # Create task for user
        task_data = {**sample_task, "user_id": user_id}
        task_response = client.post("/tasks", json=task_data)
        task_id = task_response.json()["id"]
        
        # Delete user
        delete_response = client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 200
        
        # Verify task is also deleted
        task_get_response = client.get(f"/tasks/{task_id}")
        assert task_get_response.status_code == 404

class TestTaskEndpoints:
    """Test task-related endpoints"""
    
    def test_create_task_success(self, client, sample_task):
        """Test successful task creation"""
        response = client.post("/tasks", json=sample_task)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["title"] == sample_task["title"]
        assert data["description"] == sample_task["description"]
        assert data["completed"] is False
        assert data["user_id"] is None
    
    def test_create_task_with_user(self, client, sample_user, sample_task):
        """Test creating task assigned to user"""
        # Create user first
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]
        
        # Create task assigned to user
        task_data = {**sample_task, "user_id": user_id}
        response = client.post("/tasks", json=task_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
    
    def test_create_task_invalid_user(self, client, sample_task):
        """Test creating task with non-existent user"""
        task_data = {**sample_task, "user_id": "nonexistent-user"}
        response = client.post("/tasks", json=task_data)
        
        assert response.status_code == 400
        assert response.json()["detail"] == "User not found"
    
    def test_get_tasks_empty(self, client):
        """Test getting tasks when none exist"""
        response = client.get("/tasks")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_tasks_with_data(self, client, sample_task):
        """Test getting tasks when some exist"""
        # Create task
        create_response = client.post("/tasks", json=sample_task)
        task_id = create_response.json()["id"]
        
        # Get tasks
        response = client.get("/tasks")
        assert response.status_code == 200
        
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task_id
        assert tasks[0]["title"] == sample_task["title"]
    
    def test_get_tasks_filter_by_completion(self, client, sample_task):
        """Test filtering tasks by completion status"""
        # Create completed and incomplete tasks
        completed_task = {**sample_task, "completed": True, "title": "Completed Task"}
        incomplete_task = {**sample_task, "completed": False, "title": "Incomplete Task"}
        
        client.post("/tasks", json=completed_task)
        client.post("/tasks", json=incomplete_task)
        
        # Get only completed tasks
        response = client.get("/tasks?completed=true")
        assert response.status_code == 200
        
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Completed Task"
        assert tasks[0]["completed"] is True
        
        # Get only incomplete tasks
        response = client.get("/tasks?completed=false")
        assert response.status_code == 200
        
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Incomplete Task"
        assert tasks[0]["completed"] is False
    
    def test_get_tasks_filter_by_user(self, client, sample_user, sample_task):
        """Test filtering tasks by user"""
        # Create users
        user1_response = client.post("/users", json=sample_user)
        user1_id = user1_response.json()["id"]
        
        user2_data = {**sample_user, "name": "Jane Doe", "email": "jane@example.com"}
        user2_response = client.post("/users", json=user2_data)
        user2_id = user2_response.json()["id"]
        
        # Create tasks for different users
        task1 = {**sample_task, "user_id": user1_id, "title": "User 1 Task"}
        task2 = {**sample_task, "user_id": user2_id, "title": "User 2 Task"}
        
        client.post("/tasks", json=task1)
        client.post("/tasks", json=task2)
        
        # Get tasks for user 1
        response = client.get(f"/tasks?user_id={user1_id}")
        assert response.status_code == 200
        
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "User 1 Task"
        assert tasks[0]["user_id"] == user1_id
    
    def test_get_task_by_id(self, client, sample_task):
        """Test getting specific task by ID"""
        # Create task
        create_response = client.post("/tasks", json=sample_task)
        task_id = create_response.json()["id"]
        
        # Get task by ID
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        
        task = response.json()
        assert task["id"] == task_id
        assert task["title"] == sample_task["title"]
    
    def test_get_task_not_found(self, client):
        """Test getting non-existent task"""
        response = client.get("/tasks/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    
    def test_update_task(self, client, sample_task):
        """Test updating task"""
        # Create task
        create_response = client.post("/tasks", json=sample_task)
        task_id = create_response.json()["id"]
        
        # Update task
        updated_data = {
            "title": "Updated Task",
            "description": "Updated description",
            "completed": True
        }
        
        response = client.put(f"/tasks/{task_id}", json=updated_data)
        assert response.status_code == 200
        
        task = response.json()
        assert task["id"] == task_id
        assert task["title"] == "Updated Task"
        assert task["description"] == "Updated description"
        assert task["completed"] is True
    
    def test_complete_task(self, client, sample_task):
        """Test completing a task"""
        # Create incomplete task
        create_response = client.post("/tasks", json=sample_task)
        task_id = create_response.json()["id"]
        
        # Complete task
        response = client.patch(f"/tasks/{task_id}/complete")
        assert response.status_code == 200
        
        task = response.json()
        assert task["id"] == task_id
        assert task["completed"] is True
    
    def test_complete_task_not_found(self, client):
        """Test completing non-existent task"""
        response = client.patch("/tasks/nonexistent-id/complete")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    
    def test_delete_task(self, client, sample_task):
        """Test deleting task"""
        # Create task
        create_response = client.post("/tasks", json=sample_task)
        task_id = create_response.json()["id"]
        
        # Delete task
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Task deleted successfully"
        
        # Verify task is deleted
        get_response = client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404

class TestUtilityFunctions:
    """Test utility functions in the API"""
    
    def test_reset_database(self, client, sample_user, sample_task):
        """Test database reset functionality"""
        # Create some data
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]
        
        task_data = {**sample_task, "user_id": user_id}
        client.post("/tasks", json=task_data)
        
        # Verify data exists
        users_response = client.get("/users")
        tasks_response = client.get("/tasks")
        assert len(users_response.json()) == 1
        assert len(tasks_response.json()) == 1
        
        # Reset database
        reset_database()
        
        # Verify data is gone
        users_response = client.get("/users")
        tasks_response = client.get("/tasks")
        assert len(users_response.json()) == 0
        assert len(tasks_response.json()) == 0
    
    def test_database_stats(self, client, sample_user, sample_task):
        """Test database statistics"""
        # Initial stats
        stats = get_database_stats()
        assert stats["users_count"] == 0
        assert stats["tasks_count"] == 0
        assert stats["completed_tasks"] == 0
        
        # Create user and tasks
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]
        
        # Create completed and incomplete tasks
        completed_task = {**sample_task, "completed": True, "user_id": user_id}
        incomplete_task = {**sample_task, "completed": False, "user_id": user_id}
        
        client.post("/tasks", json=completed_task)
        client.post("/tasks", json=incomplete_task)
        
        # Check updated stats
        stats = get_database_stats()
        assert stats["users_count"] == 1
        assert stats["tasks_count"] == 2
        assert stats["completed_tasks"] == 1

# Performance and edge case tests
class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON"""
        response = client.post(
            "/users",
            data="{ invalid json }",
            headers={"Content-Type": "application/json"}
        )
        # FastAPI should return 422 for invalid JSON
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        incomplete_user = {"name": "John Doe"}  # Missing email
        
        response = client.post("/users", json=incomplete_user)
        # Should return validation error
        assert response.status_code == 422
        
        error_detail = response.json()["detail"]
        assert any("email" in str(error).lower() for error in error_detail)
    
    @pytest.mark.slow
    def test_large_data_handling(self, client):
        """Test handling of large data sets"""
        # Create many users and tasks
        for i in range(50):
            user_data = {
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 50)
            }
            user_response = client.post("/users", json=user_data)
            user_id = user_response.json()["id"]
            
            # Create multiple tasks for each user
            for j in range(3):
                task_data = {
                    "title": f"Task {j} for User {i}",
                    "completed": j % 2 == 0,
                    "user_id": user_id
                }
                client.post("/tasks", json=task_data)
        
        # Test that we can still retrieve all data efficiently
        users_response = client.get("/users")
        tasks_response = client.get("/tasks")
        
        assert len(users_response.json()) == 50
        assert len(tasks_response.json()) == 150
        
        # Test filtering still works with large dataset
        completed_tasks = client.get("/tasks?completed=true")
        assert len(completed_tasks.json()) == 100  # 2 out of 3 tasks per user are completed