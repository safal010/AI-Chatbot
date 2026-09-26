from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import engine, Base, SessionLocal
from models import Chat, Message
from gemini import ask_gemini
from rag import ask_rag

# -------------------------
# Create database tables
# -------------------------

Base.metadata.create_all(bind=engine)


# -------------------------
# Create FastAPI app
# -------------------------

app = FastAPI()


# -------------------------
# CORS
# -------------------------

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


# -------------------------
# Request models
# -------------------------

class ChatRequest(BaseModel):
    message: str


# -------------------------
# Home
# -------------------------

@app.get("/")
def home():
    return {
        "message": "AI Chat API is running!"
    }


# -------------------------
# Get all chats
# -------------------------

@app.get("/chats")
def get_chats():

    db = SessionLocal()

    try:
        chats = db.query(Chat).all()

        return chats

    finally:
        db.close()


# -------------------------
# Create a new chat
# -------------------------

@app.post("/chats")
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


# -------------------------
# Send message to a chat
# -------------------------

@app.post("/chats/{chat_id}/messages")
def create_message(
    chat_id: int,
    request: ChatRequest
):

    # -------------------------
    # Check empty message
    # -------------------------

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    db = SessionLocal()

    try:

        # -------------------------
        # Find chat
        # -------------------------

        chat = db.query(Chat).filter(
            Chat.id == chat_id
        ).first()

        if chat is None:
            raise HTTPException(
                status_code=404,
                detail="Chat not found"
            )

        # -------------------------
        # Save user message
        # -------------------------

        user_message = Message(
            message=request.message,
            role="user",
            chat_id=chat_id
        )

        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        # -------------------------
        # Update chat title
        # -------------------------

        if chat.title == "New Chat":

            title = request.message.strip()

            if len(title) > 30:
                title = title[:30] + "..."

            chat.title = title

            db.commit()
            db.refresh(chat)

        # -------------------------
        # Get conversation history
        # -------------------------

        messages = db.query(Message).filter(
            Message.chat_id == chat_id
        ).all()

        # -------------------------
        # Build conversation
        # -------------------------

        conversation = ""

        for msg in messages:

            conversation += (
                f"{msg.role}: {msg.message}\n"
            )

        # -------------------------
        # Ask Gemini
        # -------------------------

        ai_response = ask_rag(
    request.message,
    conversation
)

        # -------------------------
        # Save AI response
        # -------------------------

        assistant_message = Message(
            message=ai_response,
            role="assistant",
            chat_id=chat_id
        )

        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        # -------------------------
        # Prepare response data
        # -------------------------

        user_data = {
            "id": user_message.id,
            "message": user_message.message,
            "role": user_message.role,
            "chat_id": user_message.chat_id
        }

        assistant_data = {
            "id": assistant_message.id,
            "message": assistant_message.message,
            "role": assistant_message.role,
            "chat_id": assistant_message.chat_id
        }

        # -------------------------
        # Return response
        # -------------------------

        return {
            "user_message": user_data,
            "assistant_message": assistant_data
        }

    finally:
        db.close()


# -------------------------
# Get messages of a chat
# -------------------------

@app.get("/chats/{chat_id}/messages")
def get_messages(chat_id: int):

    db = SessionLocal()

    try:

        # -------------------------
        # Check chat exists
        # -------------------------

        chat = db.query(Chat).filter(
            Chat.id == chat_id
        ).first()

        if chat is None:
            raise HTTPException(
                status_code=404,
                detail="Chat not found"
            )

        # -------------------------
        # Get messages
        # -------------------------

        messages = db.query(Message).filter(
            Message.chat_id == chat_id
        ).all()

        return messages

    finally:
        db.close()


# -------------------------
# Delete a chat
# -------------------------

@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: int):

    db = SessionLocal()

    try:

        # -------------------------
        # Find chat
        # -------------------------

        chat = db.query(Chat).filter(
            Chat.id == chat_id
        ).first()

        if chat is None:
            raise HTTPException(
                status_code=404,
                detail="Chat not found"
            )

        # -------------------------
        # Delete messages
        # -------------------------

        db.query(Message).filter(
            Message.chat_id == chat_id
        ).delete()

        # -------------------------
        # Delete chat
        # -------------------------

        db.delete(chat)

        db.commit()

        return {
            "message": "Chat deleted successfully",
            "chat_id": chat_id
        }

    finally:
        db.close()


# -------------------------
# Test Gemini
# -------------------------

@app.post("/test-gemini")
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