import json
import os
import threading
import tkinter as tk
from speech_module import speak

TODO_FILE = "todo_list.json"

# Ensure the file exists
if not os.path.exists(TODO_FILE):
    with open(TODO_FILE, "w") as f:
        json.dump({}, f)

def load_tasks():
    with open(TODO_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TODO_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

def add_task(task_text):
    tasks = load_tasks()
    next_id = len(tasks) + 1
    task_id = f"task-{next_id}"
    tasks[task_id] = task_text
    save_tasks(tasks)
    speak(f"{task_id} added: {task_text}")
    print(f"[✔] {task_id} added: {task_text}")

def remove_task_by_id(task_id):
    tasks = load_tasks()
    if task_id in tasks:
        removed = tasks.pop(task_id)
        save_tasks(tasks)
        speak(f"{task_id} removed.")
        print(f"[🗑️] {task_id} removed: {removed}")
    else:
        speak("Task not found.")
        print("[!] Task not found.")

def show_tasks():
    tasks = load_tasks()
    if not tasks:
        speak("No tasks found.")
        print("[📝] No tasks in list.")
        return

    lines = [f"{k}: {v}" for k, v in tasks.items()]
    task_text = "\n".join(lines)
    print("[📋] Current tasks:\n" + task_text)
    speak("Here are your tasks.")
    for line in lines:
        speak(line)

    # GUI Window
    def show_window():
        root = tk.Tk()
        root.title("To-Do List")
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)

        text_widget = tk.Text(root, wrap="word", font=("Helvetica", 20))
        text_widget.insert("1.0", task_text)
        text_widget.config(state="disabled")
        text_widget.pack(padx=20, pady=20, fill="both", expand=True)

        # Close button
        def close():
            root.destroy()

        tk.Button(root, text="Close", command=close, font=("Helvetica", 16)).pack(pady=10)

        root.after(10000, close)  # Auto-close after 10 seconds
        root.mainloop()

    threading.Thread(target=show_window).start()

def handle_todo(command):
    command = command.strip()

    if command.startswith("add task"):
        task = command.replace("add task", "", 1).strip()
        if task:
            add_task(task)
            return True

    elif command.startswith("remove task"):
        task_suffix = command.replace("remove task", "", 1).strip()
        if task_suffix.isdigit():
            task_id = f"task-{task_suffix}"
        else:
            task_id = task_suffix
        if task_id:
            remove_task_by_id(task_id)
            return True

    elif command == "show task":
        show_tasks()
        return True

    return False
