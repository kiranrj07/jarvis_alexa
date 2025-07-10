import os
import subprocess
import time
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Ensure these imports are correct and point to your alexa_handler.py and update_alexa_endpoint.py
from alexa_handler import handle_local_command, query_groq_model, build_alexa_response
from update_alexa_endpoint import update_alexa_endpoint

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
ngrok_token = os.getenv("NGROK_AUTH_TOKEN")

app = Flask(__name__)

ngrok_process = None

def start_ngrok():
    global ngrok_process
    try:
        subprocess.run(["ngrok", "config", "add-authtoken", ngrok_token], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error setting ngrok authtoken: {e.stderr}")
        print("Please ensure ngrok is installed and your NGROK_AUTH_TOKEN is correct in .env")
        return None
    except FileNotFoundError:
        print("Error: 'ngrok' command not found. Please ensure ngrok is installed and in your system's PATH.")
        return None

    ngrok_process = subprocess.Popen(["ngrok", "http", "5000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(5) # Adjust this if you still experience Connection Refused errors

    try:
        tunnels_api_url = "http://localhost:4040/api/tunnels"
        response = requests.get(tunnels_api_url, timeout=5)
        response.raise_for_status()
        tunnels_data = response.json()

        if not tunnels_data or "tunnels" not in tunnels_data or not tunnels_data["tunnels"]:
            print("No tunnels found in ngrok API response.")
            return None

        public_url = tunnels_data["tunnels"][0]["public_url"] + "/alexa"
        print(f"\n🚀 Ngrok Public URL: {public_url}")
        update_env_variable("NGROK_PUBLIC_URL", public_url)
        return public_url
    except requests.exceptions.ConnectionError:
        print("❌ Failed to retrieve ngrok URL: Connection refused. Ngrok API might not be ready or running.")
        print("   Please ensure ngrok is properly started. You might need to increase the sleep time in app.py.")
        return None
    except requests.exceptions.Timeout:
        print("❌ Failed to retrieve ngrok URL: Request to ngrok API timed out.")
        print("   Ngrok might be taking longer to start. Try increasing the sleep time in app.py.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ An HTTP request error occurred while retrieving ngrok URL: {e}")
        return None
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON response from ngrok API.")
        return None
    except IndexError:
        print("❌ Ngrok API returned no valid tunnel data.")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred while retrieving ngrok URL: {e}")
        return None

def update_env_variable(key, value):
    env_path = ".env"
    lines = []
    key_found = False
    try:
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    lines.append(line)

        if not key_found:
            lines.append(f"{key}={value}\n")

        with open(env_path, "w") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"Error updating .env file: {e}")

@app.route("/alexa", methods=["POST"]) # Ensure only POST is allowed
def handle_alexa():
    # >>> CRITICAL DEBUGGING LINES <<<
    import time # Import time if not already at top
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] RECEIVED POST REQUEST at /alexa")
    data = request.get_json()
    print("[DEBUG] Incoming Alexa JSON:\n", json.dumps(data, indent=2))
    # >>> END CRITICAL DEBUGGING LINES <<<

    response_text = "Sorry, I couldn't process your request." # Default response in case of unhandled error

    try:
        request_type = data['request']['type']
        print(f"[DEBUG] Alexa Request Type: {request_type}") # Added debug

        if request_type == "IntentRequest":
            intent = data['request']['intent']
            intent_name = intent.get('name')
            print(f"[DEBUG] Detected Intent Name: {intent_name}") # Added debug

            if intent_name == "LocalToIntent":
                localquery_slot = intent['slots'].get('localquery')
                if localquery_slot and 'value' in localquery_slot:
                    user_query = localquery_slot['value']
                    print(f"[DEBUG] Extracted user_query from 'localquery' slot: '{user_query}'") # Added debug
                    response_text = handle_local_command(user_query)
                    print(f"[DEBUG] Response from handle_local_command: '{response_text}'") # Added debug
                else:
                    response_text = "Sorry, I didn't get a specific command for local action."
                    print(f"[ERROR] 'localquery' slot or its value missing for LocalToIntent.") # Added debug
            else:
                query_slot = intent['slots'].get('query')
                if query_slot and 'value' in query_slot:
                    user_query = query_slot['value']
                    print(f"[DEBUG] Extracted user_query from 'query' slot: '{user_query}'") # Added debug
                    response_text = query_groq_model(user_query)
                    print(f"[DEBUG] Response from query_groq_model: '{response_text}'") # Added debug
                else:
                    response_text = "Sorry, I didn't get a specific query for the AI."
                    print(f"[ERROR] 'query' slot or its value missing for non-LocalToIntent.") # Added debug
        elif request_type == "LaunchRequest":
            print("[DEBUG] Received LaunchRequest.") # Added debug
            response_text = "Hello, Jarvis is ready. What can I do for you?"
        elif request_type == "SessionEndedRequest":
            print("[DEBUG] Received SessionEndedRequest.") # Added debug
            response_text = ""
        else:
            print(f"[WARNING] Unhandled Alexa request type: {request_type}") # Added debug
            response_text = "Sorry, I didn't understand that type of request."

    except KeyError as e:
        print(f"[ERROR] Missing key in Alexa JSON structure: {e}")
        response_text = "Sorry, I received an incomplete request from Alexa."
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in handle_alexa: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for deeper error analysis
        response_text = "Sorry, I encountered an internal error processing your request."

    print(f"[DEBUG] Sending Alexa response: '{response_text}'") # Added debug
    return jsonify(build_alexa_response(response_text))

if __name__ == "__main__":
    public_url = start_ngrok()
    if public_url:
        try:
            update_alexa_endpoint(public_url)
            print("✅ Jarvis Alexa Integration Ready. Waiting for requests...")
            app.run(port=5000, debug=False)
        except Exception as e:
            print(f"\n[CRITICAL ERROR] Alexa endpoint update or Flask app failed to start: {e}")
            import traceback
            traceback.print_exc()
            print("Please check previous error messages and ensure update_alexa_endpoint.py runs correctly.")
    else:
        print("[CRITICAL ERROR] Failed to get ngrok public URL. Cannot start Flask app.")
        if ngrok_process and ngrok_process.poll() is None:
             print("   Ngrok process might still be running. You may need to terminate it manually (Ctrl+C).")
