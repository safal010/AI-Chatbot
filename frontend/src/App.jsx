import "./App.css";
import { useEffect, useState } from "react";

// ========================================
// API CONFIGURATION
// ========================================

const API_BASE_URL = "/api";
const API_TOKEN = import.meta.env.VITE_API_TOKEN;

// ========================================
// API FETCH HELPER
// Automatically adds Bearer token
// ========================================

async function apiFetch(url, options = {}) {
  return fetch(`${API_BASE_URL}${url}`, {
    ...options,

    headers: {
      ...(options.body
        ? {
            "Content-Type": "application/json",
          }
        : {}),

      Authorization: `Bearer ${API_TOKEN}`,

      ...options.headers,
    },
  });
}

// ========================================
// APP
// ========================================

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(false);

  // ========================================
  // Get saved chat ID from localStorage
  // ========================================

  const [chatId, setChatId] = useState(() => {
    const savedChatId = localStorage.getItem("chatId");

    return savedChatId ? Number(savedChatId) : null;
  });

  // ========================================
  // Load chats when app starts
  // ========================================

  useEffect(() => {
    async function initializeApp() {
      try {
        // Load all saved chats
        const response = await apiFetch("/chats");

        if (!response.ok) {
          throw new Error("Could not load chats");
        }

        const data = await response.json();

        setChats(data);

        // Get saved chat ID
        const savedChatId = localStorage.getItem("chatId");

        if (savedChatId) {
          const savedId = Number(savedChatId);

          // Check whether the saved chat still exists
          const chatExists = data.some(
            (chat) => chat.id === savedId
          );

          if (chatExists) {
            setChatId(savedId);

            // Load its messages
            const messageResponse = await apiFetch(
              `/chats/${savedId}/messages`
            );

            if (messageResponse.ok) {
              const messagesData =
                await messageResponse.json();

              setMessages(messagesData);
            }
          } else {
            // Saved chat no longer exists
            localStorage.removeItem("chatId");
            setChatId(null);
          }
        }
      } catch (error) {
        console.error(
          "Error initializing app:",
          error
        );
      }
    }

    initializeApp();
  }, []);

  // ========================================
  // Get all chats
  // ========================================

  async function loadChats() {
    try {
      const response = await apiFetch("/chats");

      if (!response.ok) {
        throw new Error("Could not load chats");
      }

      const data = await response.json();

      setChats(data);
    } catch (error) {
      console.error("Error loading chats:", error);
    }
  }

  // ========================================
  // Create new chat
  // ========================================

  async function createChat() {
    try {
      const response = await apiFetch("/chats", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Could not create chat");
      }

      const data = await response.json();

      setChatId(data.id);

      localStorage.setItem("chatId", data.id);

      setMessages([]);

      setChats((previousChats) => [
        ...previousChats,
        data,
      ]);
    } catch (error) {
      console.error("Error creating chat:", error);
    }
  }

  // ========================================
  // Send message with streaming response
  // ========================================

  async function sendMessage() {
    if (!message.trim() || loading) {
      return;
    }

    setLoading(true);

    try {
      let currentChatId = chatId;

      // ========================================
      // Create chat automatically
      // ========================================

      if (!currentChatId) {
        const response = await apiFetch("/chats", {
          method: "POST",
        });

        if (!response.ok) {
          throw new Error("Could not create chat");
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

      // ========================================
      // Save current message
      // ========================================

      const currentMessage = message;

      // ========================================
      // Show user message immediately
      // ========================================

      const userMessage = {
        message: currentMessage,
        role: "user",
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        userMessage,
      ]);

      // ========================================
      // Create empty assistant message
      // This will be updated while streaming
      // ========================================

      const assistantMessage = {
        message: "",
        role: "assistant",
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        assistantMessage,
      ]);

      // ========================================
      // Clear input
      // ========================================

      setMessage("");

      // ========================================
      // Send message to backend
      // ========================================

      const response = await apiFetch(
        `/chats/${currentChatId}/messages`,
        {
          method: "POST",

          body: JSON.stringify({
            message: currentMessage,
          }),
        }
      );

      // ========================================
      // Check response
      // ========================================

      if (!response.ok) {
        throw new Error(
          "Server error while sending message"
        );
      }

      // ========================================
      // Check streaming support
      // ========================================

      if (!response.body) {
        throw new Error(
          "Streaming response is not supported"
        );
      }

      // ========================================
      // Create stream reader
      // ========================================

      const reader = response.body.getReader();

      const decoder = new TextDecoder();

      let assistantText = "";

      // ========================================
      // Read chunks
      // ========================================

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        const chunk = decoder.decode(value, {
          stream: true,
        });

        assistantText += chunk;

        console.log("Received chunk:", chunk);

        // ========================================
        // Update assistant message in real time
        // ========================================

        setMessages((previousMessages) => {
          const updatedMessages = [
            ...previousMessages,
          ];

          updatedMessages[
            updatedMessages.length - 1
          ] = {
            message: assistantText,
            role: "assistant",
          };

          return updatedMessages;
        });
      }

      // ========================================
      // Flush remaining decoder data
      // ========================================

      const remainingText = decoder.decode();

      if (remainingText) {
        assistantText += remainingText;

        setMessages((previousMessages) => {
          const updatedMessages = [
            ...previousMessages,
          ];

          updatedMessages[
            updatedMessages.length - 1
          ] = {
            message: assistantText,
            role: "assistant",
          };

          return updatedMessages;
        });
      }

      // ========================================
      // Update chat title
      // ========================================

      setChats((previousChats) =>
        previousChats.map((chat) => {
          if (chat.id === currentChatId) {
            return {
              ...chat,

              title:
                chat.title === "New Chat"
                  ? currentMessage.length > 30
                    ? currentMessage.substring(0, 30) +
                      "..."
                    : currentMessage
                  : chat.title,
            };
          }

          return chat;
        })
      );

      // ========================================
      // Reload chats from backend
      // This keeps sidebar data synchronized
      // ========================================

      await loadChats();

    } catch (error) {
      console.error("Error:", error);

      // ========================================
      // Show error message
      // ========================================

      setMessages((previousMessages) => {
        const updatedMessages = [
          ...previousMessages,
        ];

        // If an empty assistant message exists,
        // replace it with the error.
        if (
          updatedMessages.length > 0 &&
          updatedMessages[
            updatedMessages.length - 1
          ].role === "assistant"
        ) {
          updatedMessages[
            updatedMessages.length - 1
          ] = {
            message:
              "Sorry, something went wrong. Please try again.",
            role: "assistant",
          };
        } else {
          updatedMessages.push({
            message:
              "Sorry, something went wrong. Please try again.",
            role: "assistant",
          });
        }

        return updatedMessages;
      });
    } finally {
      setLoading(false);
    }
  }

  // ========================================
  // Select a chat
  // ========================================

  async function selectChat(id) {
    try {
      setChatId(id);

      localStorage.setItem("chatId", id);

      const response = await apiFetch(
        `/chats/${id}/messages`
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

  // ========================================
  // Delete chat
  // ========================================

  async function deleteChat(id) {
    try {
      const response = await apiFetch(
        `/chats/${id}`,
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

        localStorage.removeItem("chatId");
      }
    } catch (error) {
      console.error(
        "Error deleting chat:",
        error
      );
    }
  }

  // ========================================
  // UI
  // ========================================

  return (
    <div className="app">

      {/* ========================================
          Sidebar
      ======================================== */}

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

      {/* ========================================
          Chat area
      ======================================== */}

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
                event.key === "Enter" &&
                !event.shiftKey
              ) {
                event.preventDefault();
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
              ? "Generating..."
              : "Send"}
          </button>

        </div>

      </main>

    </div>
  );
}

export default App;