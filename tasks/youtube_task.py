def handle_youtube(command):
    command = command.lower()
    if "open youtube and play" in command:
        import subprocess, time
        import pyautogui
        from speech_module import speak

        keyword = command.replace("open youtube and play", "").strip()
        if not keyword:
            speak("Please tell me what to search for on YouTube.")
            return True

        try:
            url = "https://www.youtube.com"
            subprocess.Popen(["firefox", url])
            speak(f"Opening YouTube and searching for {keyword}")

            time.sleep(7)
            pyautogui.write(keyword)
            time.sleep(1)
            pyautogui.press("enter")
            time.sleep(5)
            pyautogui.moveTo(400, 350)
            pyautogui.click()
            return True
        except Exception as e:
            speak("Something went wrong while trying to open YouTube.")
            print(f"[ERROR] {e}")
            return True
    return False