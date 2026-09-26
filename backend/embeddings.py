import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def create_embedding(text: str):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )

    return result.embeddings[0].values


if __name__ == "__main__":
    text = "Insyde AI provides enterprise AI solutions."

    embedding = create_embedding(text)

    print("Embedding created successfully!")
    print("Number of dimensions:", len(embedding))
    print("First 10 values:")
    print(embedding[:10])