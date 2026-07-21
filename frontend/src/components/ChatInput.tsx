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
    <div className="w-full max-w-3xl mx-auto p-4 bg-white dark:bg-[#212121]">
      <div className="relative flex items-end w-full border border-gray-300 dark:border-gray-600 rounded-3xl bg-white dark:bg-[#2f2f2f] shadow-sm overflow-hidden focus-within:ring-1 focus-within:ring-black dark:focus-within:ring-white transition-shadow">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="请输入您想咨询的校园问题..."
          className="w-full max-h-[200px] py-3.5 pl-4 pr-12 bg-transparent outline-none resize-none overflow-y-auto text-black dark:text-white"
          rows={1}
        />
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading}
          className="absolute right-2 bottom-2 p-1.5 bg-black dark:bg-white text-white dark:text-black rounded-full disabled:opacity-30 disabled:cursor-not-allowed transition-opacity"
        >
          <ArrowUp size={20} />
        </button>
      </div>
      <div className="text-center text-xs text-gray-500 mt-2">
        AIZS 智能咨询系统可能产生错误，请以学校官方文件为准。
      </div>
    </div>
  );
}
