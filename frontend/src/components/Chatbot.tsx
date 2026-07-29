import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../api/client";
import type { ChatMessage } from "../types/api";

interface ChatbotProps {
  apiBase: string;
}

function formatTime(): string {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function Chatbot({ apiBase }: ChatbotProps) {
  const [messages, setMessages] = useState<(ChatMessage & { ts: string })[]>([
    { role: "assistant", content: "Hi! I'm the Ledger assistant. Ask me anything about cash-flow underwriting or how to use the platform.", ts: formatTime() },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (expanded) inputRef.current?.focus();
  }, [expanded]);

  function handleClear() {
    setMessages([
      { role: "assistant", content: "Hi! I'm the Ledger assistant. Ask me anything about cash-flow underwriting or how to use the platform.", ts: formatTime() },
    ]);
    setError("");
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || streaming) return;

    setInput("");
    setError("");
    const now = formatTime();
    const userMsg = { role: "user" as const, content: text, ts: now };
    setMessages((prev) => [...prev, userMsg]);
    setStreaming(true);

    const assistantMsg = { role: "assistant" as const, content: "", ts: now };
    setMessages((prev) => [...prev, assistantMsg]);

    const history = messages.concat(userMsg).map((m) => ({ role: m.role, content: m.content }));

    try {
      const resp = await sendChatMessage(apiBase, text, history.slice(0, -1));
      if (!resp.ok) {
        throw new Error(`Request failed: ${resp.status}`);
      }

      const reader = resp.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let full = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (payload === "[DONE]") continue;

          try {
            const parsed = JSON.parse(payload);
            if (parsed.error) {
              setError(parsed.error);
              break;
            }
            if (parsed.text) {
              full += parsed.text;
              setMessages((prev) => {
                const next = [...prev];
                next[next.length - 1] = { ...next[next.length - 1], content: full };
                return next;
              });
            }
          } catch {
            // skip malformed JSON
          }
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Chat request failed";
      setError(msg);
    } finally {
      setStreaming(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  if (!expanded) {
    return (
      <button className="chatbot-fab" onClick={() => setExpanded(true)} aria-label="Open chat">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </button>
    );
  }

  return (
    <div className="chatbot-overlay">
      <div className="chatbot-panel">
        <div className="chatbot-header">
          <div className="chatbot-header-left">
            <div className="chatbot-header-avatar">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <span>Ledger Assistant</span>
          </div>
          <div className="chatbot-header-actions">
            <button className="chatbot-clear" onClick={handleClear} title="Clear chat">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
            <button className="chatbot-close" onClick={() => setExpanded(false)} aria-label="Close chat">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="chatbot-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`chatbot-msg chatbot-msg-${msg.role}`}>
              {msg.role === "assistant" && (
                <div className="chatbot-msg-avatar">L</div>
              )}
              <div className="chatbot-msg-body">
                <div className="chatbot-msg-content">{msg.content}</div>
                <span className="chatbot-msg-time">{msg.ts}</span>
              </div>
            </div>
          ))}
          {streaming && (
            <div className="chatbot-typing">
              <span className="chatbot-dot" /><span className="chatbot-dot" /><span className="chatbot-dot" />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {error && <div className="chatbot-error">{error}</div>}

        <div className="chatbot-input-row">
          <input
            ref={inputRef}
            className="chatbot-input"
            type="text"
            placeholder="Ask about underwriting..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={streaming}
          />
          <button
            className="chatbot-send"
            onClick={handleSend}
            disabled={!input.trim() || streaming}
            aria-label="Send"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
