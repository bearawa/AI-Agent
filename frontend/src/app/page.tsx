"use client";

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/Sidebar";
import ChatInput from "@/components/ChatInput";
import ChatMessage, { MessageData } from "@/components/ChatMessage";

export default function Home() {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Fetch messages when session changes
  useEffect(() => {
    if (currentSessionId) {
      fetchMessages(currentSessionId);
    } else {
      setMessages([]);
    }
  }, [currentSessionId]);

  const fetchMessages = async (sessionId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/sessions/${sessionId}/messages`);
      const data = await res.json();
      const mapped = data.map((msg: any) => ({
        id: msg.message_id,
        role: msg.role,
        content: msg.content,
        // (In a complete implementation, fetch sources/intents here if available from API)
      }));
      setMessages(mapped);
    } catch (e) {
      console.error("Failed to fetch messages", e);
    }
  };

  const handleNewSession = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/sessions", {
        method: "POST",
      });
      const data = await res.json();
      setCurrentSessionId(data.session_id);
    } catch (e) {
      console.error("Failed to create new session", e);
    }
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    let sessionId = currentSessionId;
    if (!sessionId) {
      // Auto-create session if none exists
      try {
        const res = await fetch("http://localhost:8000/api/sessions", { method: "POST" });
        const data = await res.json();
        sessionId = data.session_id;
        setCurrentSessionId(sessionId);
      } catch (e) {
        console.error("Error creating session", e);
        return;
      }
    }

    const userMessage: MessageData = {
      id: Date.now().toString(),
      role: "user",
      content: text,
    };

    const assistantId = (Date.now() + 1).toString();
    const assistantMessage: MessageData = {
      id: assistantId,
      role: "assistant",
      content: "",
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
        }),
      });

      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let currentAssistantText = "";
      let currentSources: any[] = [];
      let currentIntent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value);
        const lines = chunkText.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const dataStr = line.slice(6);
              if (!dataStr.trim()) continue;
              const data = JSON.parse(dataStr);

              if (data.type === 'text') {
                currentAssistantText += data.data;
              } else if (data.type === 'sources') {
                currentSources = data.data;
              } else if (data.type === 'intent') {
                currentIntent = data.data.intent_name;
              }

              setMessages((prev) =>
                prev.map(msg =>
                  msg.id === assistantId ? {
                    ...msg,
                    content: currentAssistantText,
                    sources: currentSources,
                    intentName: currentIntent,
                    isStreaming: true
                  } : msg
                )
              );
            } catch (e) {
              console.error("Error parsing SSE chunk:", e, "Line:", line);
            }
          }
        }
      }
    } catch (e) {
      console.error("Stream error", e);
    } finally {
      setIsLoading(false);
      setMessages((prev) =>
        prev.map(msg =>
          msg.id === assistantId ? { ...msg, isStreaming: false } : msg
        )
      );
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-white dark:bg-[#212121]">
      <Sidebar
        currentSessionId={currentSessionId}
        onSelectSession={setCurrentSessionId}
        onNewSession={handleNewSession}
      />

      <main className="flex-1 flex flex-col relative">
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <h1 className="text-4xl font-bold text-gray-300 dark:text-gray-600">AIZS 智能咨询</h1>
            </div>
          ) : (
            <div className="pb-32">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white dark:from-[#212121] dark:via-[#212121] to-transparent pt-10">
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
      </main>
    </div>
  );
}
