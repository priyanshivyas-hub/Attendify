import requests

def get_bot_response(message):
    try:
        print("Sending request to Ollama...")

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",  
                "prompt": message,
                "stream": False
            },
            timeout=180
        )

        print("Status:", response.status_code)
        print("Raw Response:", response.text)

        if response.status_code == 200:
            return response.json().get("response", "No reply from model.")
        else:
            return f"Model error: {response.text}"

    except Exception as e:
        print("OLLAMA ERROR:", e)
        return f"Local AI error response: {e}"