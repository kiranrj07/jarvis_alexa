import speech_recognition as sr
import pyttsx3
import time
import subprocess
import simpleaudio as sa

recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Configure voice
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)
for voice in engine.getProperty('voices'):
    if 'english' in voice.name.lower() and 'female' in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

# Volume control for VLC via pactl
def get_vlc_sink_id():
    try:
        output = subprocess.check_output("pactl list sink-inputs", shell=True).decode()
        blocks = output.split("Sink Input #")[1:]
        for block in blocks:
            if "vlc" in block.lower():
                return block.split('\n')[0].strip()
    except Exception as e:
        print(f"[DEBUG] Error finding VLC sink ID: {e}")
    return "0"

def lower_vlc_volume():
    print("[DEBUG] Lowering VLC volume to 30%")
    subprocess.run(["pactl", "set-sink-input-volume", get_vlc_sink_id(), "30%"])

def restore_vlc_volume():
    print("[DEBUG] Restoring VLC volume to 80%")
    subprocess.run(["pactl", "set-sink-input-volume", get_vlc_sink_id(), "80%"])

def play_beep():
    try:
        print("[DEBUG] Playing beep")
        wave_obj = sa.WaveObject.from_wave_file("beep.wav")
        wave_obj.play()
    except Exception as e:
        print(f"[DEBUG] Beep Error: {e}")

def speak(text):
    print(f"[Jarvis says] {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("🎧 [DEBUG] Listening for wake word...")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("[DEBUG] Capturing wake word audio...")
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=40)
            text = recognizer.recognize_google(audio).lower()
            print(f"🎙️ [DEBUG] Wake word recognized: {text}")

            if "ok jarvis" in text or "ok bro" in text:
                lower_vlc_volume()
                try:
                    time.sleep(0.5)
                    play_beep()
                    time.sleep(3)
                    print("🎧 [DEBUG] Listening for command...")
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=100)
                    print("[DEBUG] Finished recording command audio")
                    time.sleep(2)
                    play_beep()
                    final_command = recognizer.recognize_google(audio).lower()
                    print(f"🎙️ [DEBUG] Final Command: {final_command}")
                    return final_command
                except sr.UnknownValueError:
                    print("🤷 [DEBUG] Could not understand the speech.")
                    return ""
                except sr.RequestError as e:
                    print(f"🚫 [DEBUG] Google API error: {e}")
                    return ""
                finally:
                    restore_vlc_volume()  # ✅ Always restore volume

            print("[DEBUG] Wake word not detected.")
            return ""

        except sr.WaitTimeoutError:
            print("⏱️ [DEBUG] No speech detected within time window.")
            return ""
        except sr.UnknownValueError:
            print("🤷 [DEBUG] Could not understand the speech.")
            return ""
        except sr.RequestError as e:
            print(f"🚫 [DEBUG] Google API error: {e}")
            return ""
