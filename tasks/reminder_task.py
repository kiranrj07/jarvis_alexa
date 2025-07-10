import os
import json
import time
import threading
import datetime
import tkinter as tk
from playsound import playsound
from speech_module import speak

REMINDER_FILE = os.path.join("tasks", "reminders.json")
ALARM_FILE = os.path.join("tasks", "alarm.wav")

# Ensure file exists
if not os.path.exists(REMINDER_FILE):
    with open(REMINDER_FILE, "w") as f:
        json.dump({}, f)

def load_reminders():
    with open(REMINDER_FILE, "r") as f:
        return json.load(f)

def save_reminders(reminders):
    with open(REMINDER_FILE, "w") as f:
        json.dump(reminders, f, indent=4)

def parse_time(time_str):
    try:
        return datetime.datetime.strptime(time_str, "%I:%M %p")
    except ValueError:
        return None

def show_reminder_popup(text):
    def show_window():
        root = tk.Tk()
        root.title("Reminder")
        root.attributes("-fullscreen", True)
        label = tk.Label(root, text=text, font=("Helvetica", 20))
        label.pack(expand=True)

        def close():
            root.destroy()

        tk.Button(root, text="Dismiss", command=close, font=("Helvetica", 14)).pack(pady=20)
        root.mainloop()

    thread = threading.Thread(target=show_window)
    thread.start()
    time.sleep(1)  # Ensure popup shows first
    return thread

def trigger_reminder(task_id, text):
    popup_thread = show_reminder_popup(f"{task_id}: {text}")
    playsound(ALARM_FILE)
    speak(f"Reminder: {text}")
    popup_thread.join()

def schedule_existing_reminders():
    def check_reminders():
        while True:
            now = datetime.datetime.now()
            current_time = now.strftime("%I:%M %p")
            current_day = now.strftime("%A").lower()

            reminders = load_reminders()
            to_remove = []

            for task_id, info in reminders.items():
                if info["time"] == current_time:
                    recurring = info.get("recurring")
                    if not recurring:
                        to_remove.append(task_id)
                    elif recurring == "weekly":
                        if info.get("day", "").lower() != current_day:
                            continue  # Skip until day matches

                    trigger_reminder(task_id, info["task"])

            if to_remove:
                for r in to_remove:
                    reminders.pop(r)
                save_reminders(reminders)

            time.sleep(30)

    threading.Thread(target=check_reminders, daemon=True).start()

def handle_reminder(command):
    print(f"[REMINDER DEBUG] Received command: {command}")
    command = command.lower().strip()

    if command.startswith("remind me to"):
        try:
            task_part, time_part = command.replace("remind me to", "").split(" at ")
            task = task_part.strip()

            time_str = time_part.strip().replace(".", "").upper()
            recurring = None
            day = None

            if "daily" in time_str:
                recurring = "daily"
                time_str = time_str.replace("daily", "").strip()
            elif "weekly" in time_str:
                recurring = "weekly"
                day = datetime.datetime.now().strftime("%A")  # current day
                time_str = time_str.replace("weekly", "").strip()

            parsed = parse_time(time_str)
            if not parsed:
                speak("Invalid time format. Please say time like 5:30 p.m.")
                print("[!] Invalid time format. Use HH:MM AM/PM format.")
                return True

            reminders = load_reminders()
            task_id = f"reminder-{len(reminders) + 1}"
            reminders[task_id] = {
                "task": task,
                "time": parsed.strftime("%I:%M %p"),
                "recurring": recurring,
            }
            if day:
                reminders[task_id]["day"] = day

            save_reminders(reminders)
            speak(f"{task_id} set for {parsed.strftime('%I:%M %p')}")
            print(f"[⏰] {task_id} set for {task} at {parsed.strftime('%I:%M %p')}")
            return True

        except Exception as e:
            speak("Sorry, I couldn't understand the reminder.")
            print(f"[!] Error parsing reminder: {e}")
            return True

    elif command == "show reminders":
        reminders = load_reminders()
        if not reminders:
            speak("No reminders found.")
            print("[📭] No reminders in list.")
        else:
            speak("Here are your reminders.")
            text = "\n".join([
                f"{task_id}: {info['task']} at {info['time']}" +
                (f" ({info['recurring']})" if info.get("recurring") else "")
                for task_id, info in reminders.items()
            ])

            # GUI popup
            def show_window():
                root = tk.Tk()
                root.title("Reminders")
                root.attributes("-fullscreen", True)

                text_widget = tk.Text(root, wrap="word", font=("Helvetica", 20))
                text_widget.insert("1.0", text)
                text_widget.config(state="disabled")
                text_widget.pack(padx=10, pady=10, fill="both", expand=True)

                tk.Button(root, text="Close", command=root.destroy, font=("Helvetica", 14)).pack(pady=10)
                root.after(10000, root.destroy)
                root.mainloop()

            threading.Thread(target=show_window).start()
            for task_id, info in reminders.items():
                speak(f"{task_id}: {info['task']} at {info['time']}")
        return True

    elif command.startswith("remove reminder"):
        task_id = command.replace("remove reminder", "").strip()
        if not task_id.startswith("reminder-"):
            task_id = f"reminder-{task_id}"

        reminders = load_reminders()
        if task_id in reminders:
            removed = reminders.pop(task_id)
            save_reminders(reminders)
            speak(f"{task_id} removed.")
            print(f"[🗑️] {task_id} removed: {removed}")
        else:
            speak("Reminder not found.")
            print("[!] Reminder not found.")
        return True

    return False
