from speech_module import listen, speak
from tasks.youtube_task import handle_youtube
from tasks.media_task import handle_media
from tasks.system_task import handle_system
from tasks.todo_task import handle_todo
from tasks.reminder_task import handle_reminder, schedule_existing_reminders
from tasks.picture_task import handle_pictures  # ✅ Added
import os
import subprocess
import atexit

# Suppress ALSA / JACK warnings
devnull = os.open(os.devnull, os.O_WRONLY)
os.dup2(devnull, 2)

# Schedule all saved reminders on startup
schedule_existing_reminders()

# Start gnome-session-inhibit to prevent suspend/lock
inhibitor_process = subprocess.Popen([
    "gnome-session-inhibit",
    "--inhibit", "idle:sleep",
    "--inhibit", "idle:logout",
    "--inhibit", "idle:suspend",
    "--inhibit", "idle:autosuspend",
    "sleep", "infinity"
])

# Ensure the inhibitor process is killed on exit
def cleanup():
    try:
        inhibitor_process.terminate()
        print("[CLEANUP] Inhibitor process terminated.")
    except Exception as e:
        print(f"[CLEANUP ERROR] Could not terminate inhibitor: {e}")

atexit.register(cleanup)

def process_command(command):
    print(f"[PROCESS DEBUG] Trying to process command: {command}")
    if handle_youtube(command):
        print("[PROCESS DEBUG] Handled by: YouTube Task")
        return True
    if handle_media(command):
        print("[PROCESS DEBUG] Handled by: Media Task")
        return True
    if handle_system(command):
        print("[PROCESS DEBUG] Handled by: System Task")
        return True
    if handle_todo(command):
        print("[PROCESS DEBUG] Handled by: To-Do Task")
        return True
    if handle_reminder(command):
        print("[PROCESS DEBUG] Handled by: Reminder Task")
        return True
    if handle_pictures(command):  # ✅ NEW HANDLER
        print("[PROCESS DEBUG] Handled by: Picture Task")
        return True
    return False

def main():
    speak("Jarvis ready. Say 'ok jarvis' or 'ok bro' followed by your command.")
    while True:
        command = listen()
        print(f"[MAIN DEBUG] Final returned command: '{command}'")
        if command:
            if not process_command(command.strip()):
                speak("Sorry, I didn't understand that command.")

if __name__ == "__main__":
    main()
