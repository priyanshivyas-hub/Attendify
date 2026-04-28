import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv('GOOGLE_API_KEY')

client = genai.Client(api_key=API_KEY)

def get_bot_response(message):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""You are Attendify AI assistant for a college attendance management system. 
Students use this platform to track their attendance in courses like DBMS, OS, AI, DAA, MPMC, Statistics, and Soft Skills.
The minimum attendance requirement is 75%. Students must maintain this to appear in exams.
Professors can mark attendance, manage courses, and resolve disputes.
Answer in 2-4 short sentences. Be direct and helpful.

User: {message}""",
            config={
                "temperature": 0.3,
                "max_output_tokens": 200
            }
        )
        return response.text.strip()
    except Exception as e:
        print("GEMINI ERROR:", e)
        return "I can help with attendance, courses, professors, and campus. What do you need?"