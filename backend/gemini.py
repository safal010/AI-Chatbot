import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def ask_gemini(message: str):
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=message
    )

    return response.text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")