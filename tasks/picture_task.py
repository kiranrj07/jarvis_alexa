import os
import glob
import threading
import time
import tkinter as tk
from PIL import Image, ImageTk
from speech_module import speak

PICTURE_FOLDER = os.path.join(os.path.dirname(__file__), "Pictures")

slideshow_state = {
    "root": None,
    "paused": False,
    "stop_requested": False,
}

def play_slideshow():
    image_files = glob.glob(os.path.join(PICTURE_FOLDER, "*.[jJpP][pPnN][gG]"))

    print(f"[PICTURE DEBUG] Found {len(image_files)} image(s) in {PICTURE_FOLDER}")
    if not image_files:
        speak("No pictures found in your Pictures folder.")
        return

    def run_slideshow():
        root = tk.Tk()
        slideshow_state["root"] = root
        slideshow_state["paused"] = False
        slideshow_state["stop_requested"] = False

        root.attributes("-fullscreen", True)
        label = tk.Label(root)
        label.pack(expand=True)

        def show_image(index):
            if slideshow_state["stop_requested"]:
                return

            if slideshow_state["paused"]:
                root.after(1000, show_image, index)  # Check again after 1s
                return

            try:
                img = Image.open(image_files[index])
                screen_width = root.winfo_screenwidth()
                screen_height = root.winfo_screenheight()
                img = img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label.config(image=photo)
                label.image = photo
            except Exception as e:
                print(f"[PICTURE ERROR] Could not display image: {e}")

            next_index = (index + 1) % len(image_files)
            root.after(5000, show_image, next_index)

        def exit_fullscreen(event=None):
            slideshow_state["stop_requested"] = True
            root.destroy()
            slideshow_state["root"] = None

        root.bind("<Escape>", exit_fullscreen)
        show_image(0)
        root.mainloop()

    threading.Thread(target=run_slideshow).start()
    speak("Starting slideshow now.")

def pause_slideshow():
    if slideshow_state["root"] and not slideshow_state["paused"]:
        slideshow_state["paused"] = True
        speak("Slideshow paused.")
    else:
        speak("Slideshow is not running or already paused.")

def continue_slideshow():
    if slideshow_state["root"] and slideshow_state["paused"]:
        slideshow_state["paused"] = False
        speak("Resuming slideshow.")
    else:
        speak("Slideshow is not paused or not running.")

def stop_slideshow():
    root = slideshow_state.get("root")
    if root:
        speak("Stopping slideshow.")
        slideshow_state["stop_requested"] = True
        root.destroy()
        slideshow_state["root"] = None
    else:
        speak("No slideshow is currently running.")

def handle_pictures(command):
    command = command.lower().strip()
    print(f"[PICTURE DEBUG] Received command: {command}")

    if command in ["play pictures", "show pictures", "start slideshow"]:
        play_slideshow()
        return True
    elif command == "pause picture":
        pause_slideshow()
        return True
    elif command == "continue picture":
        continue_slideshow()
        return True
    elif command in ["stop picture", "close pictures"]:
        stop_slideshow()
        return True

    return False
