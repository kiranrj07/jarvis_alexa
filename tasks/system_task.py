import subprocess
from speech_module import speak

def handle_system(command):
    command = command.lower()
    if "close play" in command:
        try:
            subprocess.run(["pkill", "vlc"])
            speak("Closed VLC player.")
        except Exception as e:
            speak("Failed to close VLC.")
            print("[ERROR closing VLC]", e)
        return True
    return False