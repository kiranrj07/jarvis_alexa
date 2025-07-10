import os
import tkinter as tk
import threading
import simpleaudio as sa

ALARM_SOUND = "/usr/share/sounds/alsa/Front_Center.wav"  # Replace with louder .wav if needed

def play_alarm():
    try:
        wave_obj = sa.WaveObject.from_wave_file(ALARM_SOUND)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print("Error playing alarm:", e)

def show_reminder_popup(message):
    def show():
        root = tk.Tk()
        root.title("Reminder")
        root.attributes('-topmost', True)
        root.attributes('-fullscreen', True)
        label = tk.Label(root, text=message, font=("Helvetica", 20), fg="white", bg="black", wraplength=1000)
        label.pack(padx=20, pady=20, expand=True)
        root.after(10000, root.destroy)
        root.mainloop()

    threading.Thread(target=show).start()

def trigger_reminder(message):
    threading.Thread(target=play_alarm).start()
    show_reminder_popup(message)
