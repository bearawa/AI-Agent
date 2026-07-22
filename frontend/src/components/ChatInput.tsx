import React, { useState, useRef, useEffect } from "react";
import { ArrowUp } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export default function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-2 md:px-4 pb-2 md:pb-6 pt-1 md:pt-2">
      <div className="relative flex items-end w-full border border-gray-200/80 dark:border-gray-700/80 rounded-2xl md:rounded-[2rem] bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl shadow-[0_4px_20px_rgb(0,0,0,0.06)] md:shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)] overflow-hidden focus-within:ring-2 focus-within:ring-[var(--color-zuel-cyan)] focus-within:border-transparent transition-all duration-300">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="给 AIZS 发送消息..."
          className="w-full max-h-[120px] md:max-h-[200px] py-3 md:py-4 pl-4 md:pl-6 pr-12 md:pr-14 bg-transparent outline-none resize-none overflow-y-auto text-black dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 leading-relaxed text-sm md:text-base"
          rows={1}
        />
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading}
          className="absolute right-2 md:right-3 bottom-2 md:bottom-3 p-1.5 md:p-2 bg-[var(--color-zuel-cyan)] text-white rounded-full disabled:opacity-40 disabled:scale-95 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:text-gray-500 hover:bg-[var(--color-zuel-cyan-dark)] hover:scale-105 active:scale-95 transition-all duration-200 shadow-sm"
        >
          <ArrowUp className="w-4 h-4 md:w-5 md:h-5" strokeWidth={2.5} />
        </button>
      </div>
      <div className="text-center text-[10px] md:text-xs text-gray-400 mt-2 md:mt-3 font-medium tracking-wide pb-1 md:pb-0 px-2">
        内容由 AI 生成，请注意甄别，重要信息请以 <span className="text-[var(--color-zuel-blue)] dark:text-[var(--color-zuel-cyan)]">学校官方文件</span> 为准。
      </div>
    </div>
  );
}
