#!/usr/bin/env python3
"""
Example usage of the pytest demo application.

This script demonstrates how to use both the API and CLI components.
Run this after starting the API server with: uvicorn src.api:app --reload
"""

import time
import requests
from src.cli import APIClient, TaskManager

def main():
    """Run examples of API and CLI usage"""
    print("🚀 Pytest Demo Examples")
    print("=" * 50)
    
    # Initialize clients
    api_client = APIClient("http://localhost:8000")
    task_manager = TaskManager(api_client)
    
    try:
        # Health check
        print("\n1. Health Check")
        health = api_client.health_check()
        print(f"   API Status: {health['status']}")
        print(f"   Version: {health['version']}")
        
        # Create users
        print("\n2. Creating Users")
        user1 = task_manager.create_user_with_validation(
            "Alice Johnson", "alice@example.com", 28
        )
        print(f"   Created: {user1.name} (ID: {user1.id})")
        
        user2 = task_manager.create_user_with_validation(
            "Bob Smith", "bob@example.com", 35
        )
        print(f"   Created: {user2.name} (ID: {user2.id})")
        
        # Create tasks
        print("\n3. Creating Tasks")
        task1 = api_client.create_task(
            "Complete project documentation",
            "Write comprehensive docs for the project",
            user1.id
        )
        print(f"   Task: {task1.title} (ID: {task1.id})")
        
        task2 = api_client.create_task(
            "Review code changes",
            "Review pull requests from team",
            user2.id
        )
        print(f"   Task: {task2.title} (ID: {task2.id})")
        
        task3 = api_client.create_task(
            "Update dependencies",
            "Update all project dependencies to latest versions",
            user1.id
        )
        print(f"   Task: {task3.title} (ID: {task3.id})")
        
        # List all users and tasks
        print("\n4. Listing Data")
        users = api_client.get_users()
        print(f"   Total users: {len(users)}")
        for user in users:
            print(f"   - {user.name} ({user.email})")
        
        tasks = api_client.get_tasks()
        print(f"   Total tasks: {len(tasks)}")
        for task in tasks:
            status = "✓" if task.completed else "○"
            print(f"   {status} {task.title}")
        
        # Complete some tasks
        print("\n5. Completing Tasks")
        completed_task = api_client.complete_task(task1.id)
        print(f"   Completed: {completed_task.title}")
        
        # Get user summaries
        print("\n6. User Task Summaries")
        for user in users:
            summary = task_manager.get_user_task_summary(user.id)
            print(f"   {summary['user'].name}:")
            print(f"     Total tasks: {summary['total_tasks']}")
            print(f"     Completed: {summary['completed_tasks']}")
            print(f"     Completion rate: {summary['completion_rate']:.1%}")
        
        # Filter tasks
        print("\n7. Filtering Tasks")
        completed_tasks = api_client.get_tasks(completed=True)
        print(f"   Completed tasks: {len(completed_tasks)}")
        
        pending_tasks = api_client.get_tasks(completed=False)
        print(f"   Pending tasks: {len(pending_tasks)}")
        
        alice_tasks = api_client.get_tasks(user_id=user1.id)
        print(f"   Alice's tasks: {len(alice_tasks)}")
        
        print("\n✅ Examples completed successfully!")
        print("\nNext steps:")
        print("- Try running the CLI: python -m src.cli --help")
        print("- Run tests: pytest")
        print("- Run specific test categories: pytest -m unit")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Please start the server first:")
        print("  uvicorn src.api:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()