from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid

app = FastAPI(title="Demo API", description="A simple API for pytest demonstrations")

# In-memory storage for demo purposes
users_db: Dict[str, dict] = {}
tasks_db: Dict[str, dict] = {}

class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None

class Task(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    user_id: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    age: Optional[int] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    user_id: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Welcome to Demo API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# User endpoints
@app.post("/users", response_model=UserResponse)
def create_user(user: User):
    user_id = str(uuid.uuid4())
    user_data = user.dict()
    user_data["id"] = user_id
    users_db[user_id] = user_data
    return UserResponse(**user_data)

@app.get("/users", response_model=List[UserResponse])
def get_users():
    return [UserResponse(**user) for user in users_db.values()]

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**users_db[user_id])

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user: User):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = user.dict()
    user_data["id"] = user_id
    users_db[user_id] = user_data
    return UserResponse(**user_data)

@app.delete("/users/{user_id}")
def delete_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Also delete user's tasks
    user_tasks = [task_id for task_id, task in tasks_db.items() if task.get("user_id") == user_id]
    for task_id in user_tasks:
        del tasks_db[task_id]
    
    del users_db[user_id]
    return {"message": "User deleted successfully"}

# Task endpoints
@app.post("/tasks", response_model=TaskResponse)
def create_task(task: Task):
    if task.user_id and task.user_id not in users_db:
        raise HTTPException(status_code=400, detail="User not found")
    
    task_id = str(uuid.uuid4())
    task_data = task.dict()
    task_data["id"] = task_id
    tasks_db[task_id] = task_data
    return TaskResponse(**task_data)

@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks(completed: Optional[bool] = None, user_id: Optional[str] = None):
    tasks = list(tasks_db.values())
    
    if completed is not None:
        tasks = [task for task in tasks if task["completed"] == completed]
    
    if user_id is not None:
        tasks = [task for task in tasks if task.get("user_id") == user_id]
    
    return [TaskResponse(**task) for task in tasks]

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**tasks_db[task_id])

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task: Task):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.user_id and task.user_id not in users_db:
        raise HTTPException(status_code=400, detail="User not found")
    
    task_data = task.dict()
    task_data["id"] = task_id
    tasks_db[task_id] = task_data
    return TaskResponse(**task_data)

@app.patch("/tasks/{task_id}/complete")
def complete_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    tasks_db[task_id]["completed"] = True
    return TaskResponse(**tasks_db[task_id])

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del tasks_db[task_id]
    return {"message": "Task deleted successfully"}

# Utility functions for testing
def reset_database():
    """Reset the in-memory database - useful for testing"""
    global users_db, tasks_db
    users_db.clear()
    tasks_db.clear()

def get_database_stats():
    """Get database statistics - useful for testing"""
    return {
        "users_count": len(users_db),
        "tasks_count": len(tasks_db),
        "completed_tasks": len([t for t in tasks_db.values() if t["completed"]])
    }