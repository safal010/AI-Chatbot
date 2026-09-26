import "./App.css";
import { useEffect, useState } from "react";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [chats, setChats] = useState([]);

  // Get saved chat ID from localStorage
  const [chatId, setChatId] = useState(() => {
    const savedChatId = localStorage.getItem("chatId");

    return savedChatId ? Number(savedChatId) : null;
  });

  const [loading, setLoading] = useState(false);


  // -------------------------
  // Load chats when app starts
  // -------------------------

  useEffect(() => {
    loadChats();
  }, []);


  // -------------------------
  // Load saved chat
  // -------------------------

  useEffect(() => {
    if (chatId) {
      selectChat(chatId);
    }
  }, []);


  // -------------------------
  // Get all chats
  // -------------------------

  async function loadChats() {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/chats"
      );

      if (!response.ok) {
        throw new Error("Could not load chats");
      }

      const data = await response.json();

      setChats(data);

    } catch (error) {
      console.error("Error loading chats:", error);
    }
  }


  // -------------------------
  // Create new chat
  // -------------------------

  async function createChat() {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/chats",
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Could not create chat");
      }

      const data = await response.json();

      // Select new chat
      setChatId(data.id);

      localStorage.setItem(
        "chatId",
        data.id
      );

      // Clear messages
      setMessages([]);

      // Add new chat to sidebar
      setChats((previousChats) => [
        ...previousChats,
        data,
      ]);

    } catch (error) {
      console.error(
        "Error creating chat:",
        error
      );
    }
  }


  // -------------------------
  // Send message
  // -------------------------

  async function sendMessage() {

    if (!message.trim() || loading) {
      return;
    }

    setLoading(true);

    try {

      let currentChatId = chatId;


      // -------------------------
      // Create chat automatically
      // -------------------------

      if (!currentChatId) {

        const response = await fetch(
          "http://127.0.0.1:8000/chats",
          {
            method: "POST",
          }
        );

        if (!response.ok) {
          throw new Error(
            "Could not create chat"
          );
        }

        const data = await response.json();

        currentChatId = data.id;

        setChatId(currentChatId);

        localStorage.setItem(
          "chatId",
          currentChatId
        );

        setChats((previousChats) => [
          ...previousChats,
          data,
        ]);
      }


      // -------------------------
      // Save current message
      // -------------------------

      const currentMessage = message;


      // -------------------------
      // Show user message immediately
      // -------------------------

      const userMessage = {
        message: currentMessage,
        role: "user",
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        userMessage,
      ]);


      // Clear input
      setMessage("");


      // -------------------------
      // Send message to backend
      // -------------------------

      const response = await fetch(
        `http://127.0.0.1:8000/chats/${currentChatId}/messages`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            message: currentMessage,
          }),
        }
      );


      // -------------------------
      // Check response
      // -------------------------

      if (!response.ok) {
        throw new Error(
          "Server error while sending message"
        );
      }


      const data = await response.json();


      // -------------------------
      // Check backend error
      // -------------------------

      if (data.error) {
        throw new Error(data.error);
      }


      // -------------------------
      // Update chat title
      // -------------------------

      setChats((previousChats) =>
        previousChats.map((chat) => {

          if (chat.id === currentChatId) {

            return {
              ...chat,

              title:
                chat.title === "New Chat"
                  ? currentMessage.length > 30
                    ? currentMessage.substring(
                        0,
                        30
                      ) + "..."
                    : currentMessage
                  : chat.title,
            };
          }

          return chat;
        })
      );


      // -------------------------
      // Show AI response
      // -------------------------

      const assistantMessage = {
        message:
          data.assistant_message.message,

        role: "assistant",
      };


      setMessages((previousMessages) => [
        ...previousMessages,
        assistantMessage,
      ]);

    } catch (error) {

      console.error(
        "Error:",
        error
      );


      // -------------------------
      // Show error message
      // -------------------------

      const errorMessage = {
        message:
          "Sorry, something went wrong. Please try again.",

        role: "assistant",
      };


      setMessages((previousMessages) => [
        ...previousMessages,
        errorMessage,
      ]);

    } finally {

      setLoading(false);
    }
  }


  // -------------------------
  // Select a chat
  // -------------------------

  async function selectChat(id) {

    try {

      setChatId(id);

      localStorage.setItem(
        "chatId",
        id
      );


      const response = await fetch(
        `http://127.0.0.1:8000/chats/${id}/messages`
      );


      if (!response.ok) {
        throw new Error(
          "Could not load messages"
        );
      }


      const data = await response.json();

      setMessages(data);

    } catch (error) {

      console.error(
        "Error loading messages:",
        error
      );
    }
  }


  // -------------------------
  // Delete chat
  // -------------------------

  async function deleteChat(id) {

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/chats/${id}`,
        {
          method: "DELETE",
        }
      );


      if (!response.ok) {
        throw new Error(
          "Could not delete chat"
        );
      }


      // Remove chat from sidebar
      setChats((previousChats) =>
        previousChats.filter(
          (chat) => chat.id !== id
        )
      );


      // If deleted chat was selected
      if (chatId === id) {

        setChatId(null);

        setMessages([]);

        localStorage.removeItem(
          "chatId"
        );
      }

    } catch (error) {

      console.error(
        "Error deleting chat:",
        error
      );
    }
  }


  // -------------------------
  // UI
  // -------------------------

  return (
    <div className="app">

      {/* Sidebar */}

      <aside className="sidebar">

        <h2>AI Chat</h2>


        {/* New Chat button */}

        <button
          className="new-chat-button"
          onClick={createChat}
        >
          + New Chat
        </button>


        {/* Chat list */}

        <div className="chat-list">

          {chats.map((chat) => (

            <div
              key={chat.id}

              className={
                chat.id === chatId
                  ? "chat-item active-chat"
                  : "chat-item"
              }
            >

              <span
                onClick={() =>
                  selectChat(chat.id)
                }
              >
                {chat.title}
              </span>


              <button
                className="delete-chat-button"

                onClick={() =>
                  deleteChat(chat.id)
                }
              >
                🗑
              </button>

            </div>

          ))}

        </div>

      </aside>


      {/* Chat area */}

      <main className="chat-area">

        {/* Header */}

        <header className="chat-header">

          <h2>
            AI Assistant
          </h2>

        </header>


        {/* Messages */}

        <div className="messages">

          {messages.map(
            (msg, index) => (

              <div
                key={index}

                className={`message ${
                  msg.role === "user"
                    ? "user-message"
                    : "assistant-message"
                }`}
              >

                {msg.message}

              </div>

            )
          )}


          {/* Thinking indicator */}

          {loading && (

            <div className="message assistant-message">

              Thinking...

            </div>

          )}

        </div>


        {/* Input area */}

        <div className="message-input-area">

          <input
            type="text"

            placeholder="Type a message..."

            value={message}

            onChange={(event) =>
              setMessage(event.target.value)
            }

            onKeyDown={(event) => {

              if (
                event.key === "Enter"
              ) {

                sendMessage();

              }

            }}

            disabled={loading}
          />


          <button
            onClick={sendMessage}

            disabled={loading}
          >

            {loading
              ? "Thinking..."
              : "Send"}

          </button>

        </div>

      </main>

    </div>
  );
}

export default App;