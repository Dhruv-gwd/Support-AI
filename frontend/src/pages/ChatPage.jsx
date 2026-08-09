import { useState, useRef, useEffect } from "react";
import { useChat } from "../context/ChatContext";
import Navbar from "../components/Navbar";

export default function ChatPage() {
  const { messages, send, loading, error, clear } = useChat();
  const [input, setInput] = useState("");
  const [queue, setQueue] = useState([]);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Send the next queued message once the current one finishes loading
  useEffect(() => {
    if (!loading && queue.length > 0) {
      const [next, ...rest] = queue;
      setQueue(rest);
      send(next);
    }
  }, [loading, queue, send]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const text = input.trim();
    setInput("");

    if (loading) {
      setQueue((prev) => [...prev, text]);
    } else {
      send(text);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-6 h-[calc(100vh-3.5rem)] flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-20">
              <p className="text-lg font-medium">👋 Hi! I am SupportAI.</p>
              <p className="mt-2">Ask me anything about your uploaded documents.</p>
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white rounded-br-sm"
                    : "bg-white border border-gray-200 text-gray-800 rounded-bl-sm"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                {msg.images && msg.images.length > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {msg.images.map((src, i) => (
                      <img
                        key={i}
                        src={src}
                        alt={`Document image ${i + 1}`}
                        className="rounded-lg max-w-full h-auto border border-gray-200"
                      />
                    ))}
                  </div>
                )}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-200/50">
                    <p className="text-xs text-gray-500 mb-1">Sources:</p>
                    <div className="flex flex-wrap gap-1">
                      {msg.sources.map((s, i) => (
                        <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {error && (
          <div className="mb-3 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {queue.length > 0 && (
          <div className="mb-2 text-xs text-gray-500">
            {queue.length} message{queue.length > 1 ? "s" : ""} queued...
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question..."
            className="flex-1 rounded-xl border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white px-6 py-3 rounded-xl font-medium transition"
          >
            Send
          </button>
          {messages.length > 0 && (
            <button
              type="button"
              onClick={clear}
              className="text-gray-500 hover:text-gray-700 px-3 py-3 text-sm"
              title="Clear chat"
            >
              Clear
            </button>
          )}
        </form>
      </div>
    </div>
  );
}