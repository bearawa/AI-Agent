import React from "react";
import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

export interface MessageData {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  intentName?: string;
  isStreaming?: boolean;
}

interface ChatMessageProps {
  message: MessageData;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "w-full py-6 flex justify-center text-base",
        isUser ? "bg-white dark:bg-[#212121]" : "bg-[#F9F9F9] dark:bg-[#212121]"
      )}
    >
      <div className="flex w-full max-w-3xl gap-4 px-4">
        {/* Avatar */}
        <div className="shrink-0 flex flex-col relative items-end">
          <div
            className={cn(
              "w-8 h-8 rounded-sm flex items-center justify-center text-white",
              isUser ? "bg-gray-300 dark:bg-gray-600" : "bg-[#10a37f]"
            )}
          >
            {isUser ? <User size={20} /> : <Bot size={20} />}
          </div>
        </div>

        {/* Content */}
        <div className="flex flex-col min-w-0 w-full pb-2">
          {message.intentName && (
            <div className="text-xs text-gray-500 mb-2">
              🎯 识别到意图：{message.intentName}
            </div>
          )}
          <div className="prose dark:prose-invert max-w-none break-words text-black dark:text-[#ececec]">
            {message.content}
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-black dark:bg-white animate-pulse" />
            )}
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm font-semibold mb-2 text-gray-700 dark:text-gray-300">🔍 信息来源</p>
              {message.sources.map((src, idx) => (
                <div key={idx} className="bg-white dark:bg-[#2f2f2f] border border-gray-200 dark:border-gray-700 rounded-md p-3 mb-2 text-sm">
                  <div className="font-medium text-[#10a37f] mb-1">
                    [{idx + 1}] 出处：{src.file_name} (第 {src.page_number} 页)
                  </div>
                  <div className="text-gray-600 dark:text-gray-400 line-clamp-3">
                    {src.source_text}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
