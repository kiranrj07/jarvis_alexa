import os
import subprocess
import socket
import random
import json
from speech_module import speak

MEDIA_STATE_FILE = os.path.join(os.path.dirname(__file__), "media_state.json")

MEDIA_CATEGORIES = {
    "music": {"path": os.path.join(os.path.dirname(__file__), "music"), "type": "music"},
    "video": {"path": os.path.join(os.path.dirname(__file__), "videos"), "type": "video"},
    "devotional": {"path": os.path.join(os.path.dirname(__file__), "devotional"), "type": "video"},
    "study music": {"path": os.path.join(os.path.dirname(__file__), "study_music"), "type": "music"},
    "study video": {"path": os.path.join(os.path.dirname(__file__), "study_video"), "type": "video"}
}

if not os.path.exists(MEDIA_STATE_FILE):
    with open(MEDIA_STATE_FILE, "w") as f:
        json.dump({}, f)

def load_state():
    with open(MEDIA_STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(MEDIA_STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def get_media_files(folder):
    return sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(('.mp3', '.wav', '.m4a', '.mp4', '.mkv', '.avi'))
    ])

def play_media(category, shuffle=False):
    info = MEDIA_CATEGORIES.get(category)
    if not info:
        speak("Unsupported media category.")
        return True

    folder = info["path"]
    media_type = info["type"]

    if not os.path.exists(folder):
        speak(f"{category} folder not found.")
        return True

    media_files = get_media_files(folder)
    if not media_files:
        speak(f"No {category} files found.")
        return True

    state = load_state()
    index = 0

    if shuffle:
        random.shuffle(media_files)
        state[category] = {"last_index": 0}
    else:
        index = state.get(category, {}).get("last_index", 0)
        if index >= len(media_files):
            index = 0
        media_files = media_files[index:] + media_files[:index]

    speak(f"Playing your {category}{' in random order' if shuffle else ''} now.")
    args = ['vlc', '--extraintf', 'rc', '--rc-host', 'localhost:9999']
    if shuffle:
        args.append('--random')
    if media_type == "video":
        args.append('--fullscreen')
    else:
        args.extend(['--intf', 'dummy', '--no-video'])

    subprocess.Popen(args + media_files)

    # Save last index for next session
    state[category] = {"last_index": (index + 1) % len(media_files)}
    save_state(state)

    return True

def send_vlc_command(cmd):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', 9999))
            s.sendall((cmd + '\n').encode())
    except Exception as e:
        speak("Failed to control VLC.")
        print("[VLC TCP Error]", e)

def control_vlc(action):
    commands = {
        "pause": "pause", "stop": "stop", "next": "next",
        "volume up": "volup 20", "volume down": "voldown 20",
        "mute": "volume 0", "unmute": "volume 100"
    }
    if action in commands:
        send_vlc_command(commands[action])
        return True
    return False

def handle_media(command):
    command = command.lower().strip()

    # Play commands
    for category in MEDIA_CATEGORIES:
        if f"play random {category}" in command:
            return play_media(category, shuffle=True)
        elif f"play {category}" in command:
            return play_media(category)

    # Control commands
    for category in MEDIA_CATEGORIES:
        if any(kw in command for kw in [f"pause {category}", f"resume {category}", f"continue {category}"]):
            return control_vlc("pause")
        elif f"stop {category}" in command:
            return control_vlc("stop")
        elif any(kw in command for kw in [f"skip {category}", f"next {category}"]):
            return control_vlc("next")

    # Generic controls
    if "volume up" in command:
        return control_vlc("volume up")
    elif "volume down" in command:
        return control_vlc("volume down")
    elif "mute" in command:
        return control_vlc("mute")
    elif "unmute" in command:
        return control_vlc("unmute")

    return False
