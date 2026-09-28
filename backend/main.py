from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from database import engine, Base, SessionLocal
from models import Chat, Message
from gemini import ask_gemini, client
from rag import ask_rag, ask_rag_stream


# ========================================
# Load environment variables
# ========================================

load_dotenv()


# ========================================
# Create database tables
# ========================================

Base.metadata.create_all(bind=engine)


# ========================================
# Create FastAPI app
# ========================================

app = FastAPI()


# ========================================
# Authentication
# ========================================

security = HTTPBearer()

AUTH_TOKEN = os.getenv("AUTH_TOKEN")


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if not AUTH_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="AUTH_TOKEN is not configured"
        )

    if credentials.credentials != AUTH_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    return True


# ========================================
# CORS
# ========================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ========================================
# Request models
# ========================================

class ChatRequest(BaseModel):
    message: str


class PythonFunctionRequest(BaseModel):
    prompt: str


# ========================================
# Home
# ========================================

@app.get("/")
def home():
    return {
        "message": "AI Chat API is running!"
    }


# ========================================
# Get all chats
# ========================================

@app.get(
    "/chats",
    dependencies=[Depends(verify_token)]
)
def get_chats():

    db = SessionLocal()

    try:

        chats = db.query(Chat).all()

        return chats

    finally:
        db.close()


# ========================================
# Create a new chat
# ========================================

@app.post(
    "/chats",
    dependencies=[Depends(verify_token)]
)
def create_chat():

    db = SessionLocal()

    try:

        new_chat = Chat(
            title="New Chat"
        )

        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)

        return {
            "id": new_chat.id,
            "title": new_chat.title
        }

    finally:
        db.close()


# ========================================
# Send message to a chat
# ========================================

@app.post(
    "/chats/{chat_id}/messages",
    dependencies=[Depends(verify_token)]
)
def create_message(
    chat_id: int,
    request: ChatRequest
):

    # ----------------------------------------
    # Check empty message
    # ----------------------------------------

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    def generate():

        db = SessionLocal()

        try:

            # ----------------------------------------
            # Find chat
            # ----------------------------------------

            chat = db.query(Chat).filter(
                Chat.id == chat_id
            ).first()

            if chat is None:
                yield "Error: Chat not found"
                return

            # ----------------------------------------
            # Save user message
            # ----------------------------------------

            user_message = Message(
                message=request.message,
                role="user",
                chat_id=chat_id
            )

            db.add(user_message)
            db.commit()
            db.refresh(user_message)

            # ----------------------------------------
            # Update chat title
            # ----------------------------------------

            if chat.title == "New Chat":

                title = request.message.strip()

                if len(title) > 30:
                    title = title[:30] + "..."

                chat.title = title

                db.commit()
                db.refresh(chat)

            # ----------------------------------------
            # Get conversation history
            # ----------------------------------------

            messages = db.query(Message).filter(
                Message.chat_id == chat_id
            ).all()

            # ----------------------------------------
            # Build conversation
            # ----------------------------------------

            conversation = ""

            for msg in messages:

                conversation += (
                    f"{msg.role}: {msg.message}\n"
                )

            # ----------------------------------------
            # Stream RAG response
            # ----------------------------------------

            full_response = ""

            for chunk in ask_rag_stream(
                request.message,
                conversation
            ):

                full_response += chunk

                yield chunk

            # ----------------------------------------
            # Save complete AI response
            # ----------------------------------------

            assistant_message = Message(
                message=full_response,
                role="assistant",
                chat_id=chat_id
            )

            db.add(assistant_message)
            db.commit()

            print(
                "Complete AI response saved to database."
            )

        finally:

            db.close()

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


# ========================================
# Get messages of a chat
# ========================================

@app.get(
    "/chats/{chat_id}/messages",
    dependencies=[Depends(verify_token)]
)
def get_messages(chat_id: int):

    db = SessionLocal()

    try:

        # ----------------------------------------
        # Check chat exists
        # ----------------------------------------

        chat = db.query(Chat).filter(
            Chat.id == chat_id
        ).first()

        if chat is None:

            raise HTTPException(
                status_code=404,
                detail="Chat not found"
            )

        # ----------------------------------------
        # Get messages
        # ----------------------------------------

        messages = db.query(Message).filter(
            Message.chat_id == chat_id
        ).all()

        return messages

    finally:

        db.close()


# ========================================
# Delete a chat
# ========================================

@app.delete(
    "/chats/{chat_id}",
    dependencies=[Depends(verify_token)]
)
def delete_chat(chat_id: int):

    db = SessionLocal()

    try:

        # ----------------------------------------
        # Find chat
        # ----------------------------------------

        chat = db.query(Chat).filter(
            Chat.id == chat_id
        ).first()

        if chat is None:

            raise HTTPException(
                status_code=404,
                detail="Chat not found"
            )

        # ----------------------------------------
        # Delete messages
        # ----------------------------------------

        db.query(Message).filter(
            Message.chat_id == chat_id
        ).delete()

        # ----------------------------------------
        # Delete chat
        # ----------------------------------------

        db.delete(chat)

        db.commit()

        return {
            "message": "Chat deleted successfully",
            "chat_id": chat_id
        }

    finally:

        db.close()


# ========================================
# Test Gemini
# ========================================

@app.post(
    "/test-gemini",
    dependencies=[Depends(verify_token)]
)
def test_gemini(request: ChatRequest):

    if not request.message.strip():

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    response = ask_gemini(
        request.message
    )

    return {
        "response": response
    }


# ========================================
# Test Gemini Streaming
# ========================================

@app.post(
    "/test-stream",
    dependencies=[Depends(verify_token)]
)
def test_stream(request: ChatRequest):

    def generate():

        response = client.models.generate_content_stream(
            model="gemini-3.5-flash-lite",
            contents=request.message
        )

        for chunk in response:

            if chunk.text:

                yield chunk.text

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


# ========================================
# Test RAG Streaming
# ========================================

@app.post(
    "/test-rag-stream",
    dependencies=[Depends(verify_token)]
)
def test_rag_stream(request: ChatRequest):

    def generate():

        for chunk in ask_rag_stream(
            request.message
        ):

            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


# ========================================
# Generate Python Function
# ========================================

@app.post(
    "/generate-python",
    dependencies=[Depends(verify_token)]
)
def generate_python_function(
    request: PythonFunctionRequest
):

    # ----------------------------------------
    # Check empty prompt
    # ----------------------------------------

    if not request.prompt.strip():

        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty"
        )

    # ----------------------------------------
    # Create Python generation prompt
    # ----------------------------------------

    prompt = f"""
You are an expert Python programming assistant.

Generate a Python function based on the user's request.

Rules:

1. Return only the Python function.
2. Do not provide explanations.
3. Do not use Markdown code fences.
4. Write clean and readable Python.
5. Use meaningful variable names.
6. Add type hints when appropriate.
7. Make sure the generated function is valid Python.

User request:

{request.prompt}
"""

    # ----------------------------------------
    # Ask Gemini
    # ----------------------------------------

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    # ----------------------------------------
    # Get generated function
    # ----------------------------------------

    generated_function = response.text.strip()

    # ----------------------------------------
    # Remove Markdown code fences
    # ----------------------------------------

    if generated_function.startswith("```"):

        lines = generated_function.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        generated_function = "\n".join(lines).strip()

    # ----------------------------------------
    # Return generated Python function
    # ----------------------------------------

    return {
        "function": generated_function
    }