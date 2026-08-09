import { createContext, useContext, useState, useCallback } from "react";
import { sendMessage as apiSendMessage } from "../api/client";

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const send = useCallback(async (text) => {
    const userMsg = { id: Date.now(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError(null);
    try {
      const data = await apiSendMessage(text, conversationId);
      const botMsg = {
        id: Date.now() + 1,
        role: "assistant",
        content: data.response,
        sources: data.sources,
        images: data.images || [],
      };
      setMessages((prev) => [...prev, botMsg]);
      if (data.conversation_id && !conversationId) {
        setConversationId(data.conversation_id);
      }
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to send message");
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  const clear = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  return (
    <ChatContext.Provider value={{ messages, send, loading, error, clear, conversationId }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
