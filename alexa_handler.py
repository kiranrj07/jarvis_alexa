import json
import os
import requests
from dotenv import load_dotenv
from tasks.youtube_task import handle_youtube
from tasks.media_task import handle_media
from tasks.system_task import handle_system
from tasks.todo_task import handle_todo
from tasks.reminder_task import handle_reminder, schedule_existing_reminders
from tasks.picture_task import handle_pictures
from speech_module import speak  # Still useful for output
from tasks.media_task import speak  # assuming speak() is reused here

def handle_local_command(command):
    """Process local Jarvis commands from Alexa input."""
    command = command.lower().strip()
    print(f"[ALEXA DEBUG] Processing local command: {command}")

    if handle_youtube(command):
        return "YouTube task triggered."
    if handle_media(command):
        return "Media task executed."
    if handle_system(command):
        return "System task executed."
    if handle_todo(command):
        return "To-do task executed."
    if handle_reminder(command):
        return "Reminder task added."
    if handle_pictures(command):
        return "Picture slideshow started."

    return "Sorry, I could not process the local command."

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

def handle_alexa_request(data):
    try:
        user_query = data['request']['intent']['slots']['query']['value'].lower()
    except KeyError:
        return build_alexa_response("Sorry, I didn't catch that.")

    if user_query.startswith("local to "):
        local_command = user_query.replace("local to ", "").strip()
        if process_local_command(local_command):
            return build_alexa_response("Command executed.")
        else:
            return build_alexa_response("Sorry, I couldn't process that local command.")
    else:
        return build_alexa_response(query_groq_model(user_query))

def process_local_command(command):
    if handle_youtube(command):
        return True
    if handle_media(command):
        return True
    if handle_system(command):
        return True
    if handle_todo(command):
        return True
    if handle_reminder(command):
        return True
    if handle_pictures(command):
        return True
    return False

def query_groq_model(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("[ERROR] Groq API:", e)
        return "There was a problem contacting the AI."

def build_alexa_response(message):
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": message
            },
            "shouldEndSession": True
        }
    }
