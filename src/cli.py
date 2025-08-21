import click
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
    email: str
    age: Optional[int] = None

@dataclass
class Task:
    id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    user_id: Optional[str] = None

class APIClient:
    """Client for interacting with the Demo API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def health_check(self) -> Dict:
        """Check if the API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to API: {e}")
    
    def create_user(self, name: str, email: str, age: Optional[int] = None) -> User:
        """Create a new user"""
        data = {"name": name, "email": email}
        if age is not None:
            data["age"] = age
        
        response = self.session.post(f"{self.base_url}/users", json=data)
        response.raise_for_status()
        user_data = response.json()
        return User(**user_data)
    
    def get_users(self) -> List[User]:
        """Get all users"""
        response = self.session.get(f"{self.base_url}/users")
        response.raise_for_status()
        users_data = response.json()
        return [User(**user) for user in users_data]
    
    def get_user(self, user_id: str) -> User:
        """Get a specific user"""
        response = self.session.get(f"{self.base_url}/users/{user_id}")
        response.raise_for_status()
        user_data = response.json()
        return User(**user_data)
    
    def create_task(self, title: str, description: Optional[str] = None, user_id: Optional[str] = None) -> Task:
        """Create a new task"""
        data = {"title": title}
        if description is not None:
            data["description"] = description
        if user_id is not None:
            data["user_id"] = user_id
        
        response = self.session.post(f"{self.base_url}/tasks", json=data)
        response.raise_for_status()
        task_data = response.json()
        return Task(**task_data)
    
    def get_tasks(self, completed: Optional[bool] = None, user_id: Optional[str] = None) -> List[Task]:
        """Get tasks with optional filters"""
        params = {}
        if completed is not None:
            params["completed"] = completed
        if user_id is not None:
            params["user_id"] = user_id
        
        response = self.session.get(f"{self.base_url}/tasks", params=params)
        response.raise_for_status()
        tasks_data = response.json()
        return [Task(**task) for task in tasks_data]
    
    def complete_task(self, task_id: str) -> Task:
        """Mark a task as completed"""
        response = self.session.patch(f"{self.base_url}/tasks/{task_id}/complete")
        response.raise_for_status()
        task_data = response.json()
        return Task(**task_data)

class TaskManager:
    """Business logic for managing tasks and users"""
    
    def __init__(self, api_client: APIClient):
        self.api = api_client
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_age(self, age: int) -> bool:
        """Validate age is reasonable"""
        return 0 <= age <= 150
    
    def create_user_with_validation(self, name: str, email: str, age: Optional[int] = None) -> User:
        """Create user with validation"""
        if not name.strip():
            raise ValueError("Name cannot be empty")
        
        if not self.validate_email(email):
            raise ValueError("Invalid email format")
        
        if age is not None and not self.validate_age(age):
            raise ValueError("Age must be between 0 and 150")
        
        return self.api.create_user(name.strip(), email, age)
    
    def get_user_task_summary(self, user_id: str) -> Dict:
        """Get a summary of user's tasks"""
        user = self.api.get_user(user_id)
        tasks = self.api.get_tasks(user_id=user_id)
        
        completed_tasks = [t for t in tasks if t.completed]
        pending_tasks = [t for t in tasks if not t.completed]
        
        return {
            "user": user,
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "pending_tasks": len(pending_tasks),
            "completion_rate": len(completed_tasks) / len(tasks) if tasks else 0
        }

# CLI Commands
@click.group()
@click.option('--api-url', default='http://localhost:8000', help='API base URL')
@click.pass_context
def cli(ctx, api_url):
    """Demo CLI for interacting with the API"""
    ctx.ensure_object(dict)
    ctx.obj['api_client'] = APIClient(api_url)
    ctx.obj['task_manager'] = TaskManager(ctx.obj['api_client'])

@cli.command()
@click.pass_context
def health(ctx):
    """Check API health"""
    try:
        result = ctx.obj['api_client'].health_check()
        click.echo(f"API Status: {result['status']}")
        click.echo(f"Version: {result['version']}")
    except ConnectionError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.option('--name', prompt='User name', help='Name of the user')
@click.option('--email', prompt='Email', help='Email address')
@click.option('--age', type=int, help='Age (optional)')
@click.pass_context
def create_user(ctx, name, email, age):
    """Create a new user"""
    try:
        user = ctx.obj['task_manager'].create_user_with_validation(name, email, age)
        click.echo(f"Created user: {user.name} ({user.id})")
    except ValueError as e:
        click.echo(f"Validation error: {e}", err=True)
        raise click.Abort()
    except requests.exceptions.RequestException as e:
        click.echo(f"API error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.pass_context
def list_users(ctx):
    """List all users"""
    try:
        users = ctx.obj['api_client'].get_users()
        if not users:
            click.echo("No users found.")
            return
        
        click.echo("Users:")
        for user in users:
            age_info = f" (age: {user.age})" if user.age else ""
            click.echo(f"  {user.name} - {user.email}{age_info} [ID: {user.id}]")
    except requests.exceptions.RequestException as e:
        click.echo(f"API error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.option('--title', prompt='Task title', help='Title of the task')
@click.option('--description', help='Task description (optional)')
@click.option('--user-id', help='Assign to user ID (optional)')
@click.pass_context
def create_task(ctx, title, description, user_id):
    """Create a new task"""
    try:
        task = ctx.obj['api_client'].create_task(title, description, user_id)
        click.echo(f"Created task: {task.title} [ID: {task.id}]")
    except requests.exceptions.RequestException as e:
        click.echo(f"API error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.option('--completed', type=bool, help='Filter by completion status')
@click.option('--user-id', help='Filter by user ID')
@click.pass_context
def list_tasks(ctx, completed, user_id):
    """List tasks with optional filters"""
    try:
        tasks = ctx.obj['api_client'].get_tasks(completed=completed, user_id=user_id)
        if not tasks:
            click.echo("No tasks found.")
            return
        
        click.echo("Tasks:")
        for task in tasks:
            status = "✓" if task.completed else "○"
            user_info = f" [User: {task.user_id}]" if task.user_id else ""
            click.echo(f"  {status} {task.title}{user_info} [ID: {task.id}]")
            if task.description:
                click.echo(f"    Description: {task.description}")
    except requests.exceptions.RequestException as e:
        click.echo(f"API error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.argument('task_id')
@click.pass_context
def complete_task(ctx, task_id):
    """Mark a task as completed"""
    try:
        task = ctx.obj['api_client'].complete_task(task_id)
        click.echo(f"Completed task: {task.title}")
    except requests.exceptions.RequestException as e:
        click.echo(f"API error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.argument('user_id')
@click.pass_context
def user_summary(ctx, user_id):
    """Get user task summary"""
    try:
        summary = ctx.obj['task_manager'].get_user_task_summary(user_id)
        user = summary['user']
        
        click.echo(f"User Summary for {user.name} ({user.email})")
        click.echo(f"Total tasks: {summary['total_tasks']}")
        click.echo(f"Completed: {summary['completed_tasks']}")
        click.echo(f"Pending: {summary['pending_tasks']}")
        click.echo(f"Completion rate: {summary['completion_rate']:.1%}")
    except requests.exceptions.RequestException as e:
        click.echo(f"API error: {e}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()