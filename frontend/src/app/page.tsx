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
      const res = await fetch(`/api/sessions/${sessionId}/messages`);
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
      const res = await fetch("/api/sessions", { method: "POST" });
      const data = await res.json();
      setCurrentSessionId(data.session_id);
      setMessages([]);
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
        const res = await fetch("/api/sessions", { method: "POST" });
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
      const response = await fetch("/api/chat/stream", {
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
                  } : msg
                )
              );
            } catch (err) {
              console.error("Error parsing JSON chunk", err);
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
    <div className="flex h-screen overflow-hidden bg-white dark:bg-[#0a0a0a] selection:bg-[var(--color-zuel-cyan)] selection:text-white">
      <Sidebar
        currentSessionId={currentSessionId}
        onSelectSession={setCurrentSessionId}
        onNewSession={handleNewSession}
      />

      <main className="flex-1 flex flex-col relative w-full">
        {/* Subtle background gradient mesh */}
        <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none opacity-40 dark:opacity-20">
          <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-[var(--color-zuel-blue)] blur-[120px] opacity-20"></div>
          <div className="absolute top-[20%] -right-[10%] w-[40%] h-[40%] rounded-full bg-[var(--color-zuel-cyan)] blur-[120px] opacity-20"></div>
        </div>

        <div className="flex-1 overflow-y-auto z-10 scroll-smooth custom-scrollbar relative">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="flex flex-col items-center justify-center p-12 max-w-2xl w-full text-center">

                <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-[var(--color-zuel-blue)] to-[var(--color-zuel-cyan)] mb-4 tracking-tight">
                  AIZS 智能咨询平台
                </h1>
                <p className="text-gray-500 dark:text-gray-400 text-lg md:text-xl font-medium mb-8 max-w-lg leading-relaxed">
                  中南财经政法大学您的专属校园 AI 助手，随时为您解答校园生活、学习疑问。
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-lg mt-4">
                  {['图书馆今天几点闭馆？', '怎么办理校园网宽带？', '南湖校区二食堂有什么好吃的？', '新生入学体检流程是什么？'].map((suggestion, i) => (
                    <button
                      key={i}
                      onClick={() => handleSendMessage(suggestion)}
                      className="px-4 py-3 bg-white dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50 rounded-xl text-sm text-gray-600 dark:text-gray-300 hover:border-[var(--color-zuel-cyan)] hover:text-[var(--color-zuel-blue)] dark:hover:text-[var(--color-zuel-cyan)] hover:shadow-md transition-all text-left group"
                    >
                      {suggestion} <span className="opacity-0 group-hover:opacity-100 transition-opacity float-right text-[var(--color-zuel-cyan)]">→</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="pb-40">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Sticky Input Area */}
        <div className="absolute bottom-0 left-0 right-0 pt-16 pb-4 bg-gradient-to-t from-white via-white/95 to-transparent dark:from-[#0a0a0a] dark:via-[#0a0a0a]/95 z-20">
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
      </main>
    </div>
  );
}
