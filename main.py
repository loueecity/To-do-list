from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import os

from schemas import TaskCreate, Task
from database import get_db, init_db

app = FastAPI()

# Serve static files from ./static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve frontend HTML
@app.get("/")
def root():
    return FileResponse(os.path.join("static", "index.html"))

# Initialize DB on startup
@app.on_event("startup")
def startup():
    init_db()

@app.post("/tasks/", response_model=Task)
def create_task(task: TaskCreate):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO tasks (title) VALUES (?)", (task.title,))
    db.commit()
    task_id = cursor.lastrowid
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return Task(id=row["id"], title=row["title"], is_completed=bool(row["is_completed"]))

@app.get("/tasks/", response_model=List[Task])  # <-- changed here for Python 3.8
def get_tasks():
    db = get_db()
    rows = db.execute("SELECT * FROM tasks").fetchall()
    return [Task(id=row["id"], title=row["title"], is_completed=bool(row["is_completed"])) for row in rows]

@app.put("/tasks/{task_id}", response_model=Task)
def toggle_task_completion(task_id: int):
    db = get_db()
    # Get current status
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    
    new_status = 0 if row["is_completed"] else 1
    db.execute("UPDATE tasks SET is_completed = ? WHERE id = ?", (new_status, task_id))
    db.commit()
    
    updated_row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return Task(id=updated_row["id"], title=updated_row["title"], is_completed=bool(updated_row["is_completed"]))

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    db = get_db()
    cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}

@app.delete("/tasks/")
def delete_all_tasks():
    db = get_db()
    db.execute("DELETE FROM tasks")
    db.commit()
    return {"message": "All tasks deleted"}