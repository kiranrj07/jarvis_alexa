import os
import json
import requests

def query_groq_model(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
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
        print("Error from Groq API:", e)
        return "I'm sorry, something went wrong with the AI response."
