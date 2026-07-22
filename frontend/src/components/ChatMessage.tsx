import React from "react";
import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion } from "framer-motion";

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
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        "w-full py-8 flex justify-center text-base border-b border-gray-100 dark:border-gray-800",
        isUser ? "bg-white dark:bg-[#0a0a0a]" : "bg-gradient-to-b from-[#F9F9F9] to-white dark:from-[#111111] dark:to-[#0a0a0a]"
      )}
    >
      <div className="flex w-full max-w-4xl gap-6 px-4">
        {/* Avatar */}
        <div className="shrink-0 flex flex-col relative items-end">
          <div
            className={cn(
              "w-10 h-10 rounded-full flex items-center justify-center text-white shadow-md",
              isUser ? "bg-gradient-to-br from-gray-400 to-gray-500" : "bg-gradient-to-br from-[#22887D] to-[#1A665E]"
            )}
          >
            {isUser ? <User size={22} /> : <Bot size={22} />}
          </div>
        </div>

        {/* Content */}
        <div className="flex flex-col min-w-0 w-full pb-2">
          {message.intentName && (
            <div className="text-xs font-medium text-[var(--color-zuel-blue)] dark:text-[var(--color-zuel-cyan)] bg-blue-50 dark:bg-cyan-950/30 w-fit px-2.5 py-1 rounded-full mb-3 flex items-center gap-1.5 shadow-sm border border-blue-100 dark:border-cyan-900/50">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-zuel-blue)] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-zuel-blue)] dark:bg-[var(--color-zuel-cyan)]"></span>
              </span>
              识别到意图：{message.intentName}
            </div>
          )}

          <div className="prose prose-slate prose-lg dark:prose-invert max-w-none break-words text-gray-800 dark:text-gray-200">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content + (message.isStreaming ? " ▍" : "")}
            </ReactMarkdown>
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-6 pt-6 border-t border-dashed border-gray-200 dark:border-gray-800"
            >
              <p className="text-sm font-semibold mb-4 flex items-center gap-2 text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                <span className="w-4 h-[1px] bg-gray-300 dark:bg-gray-600"></span>
                信息来源
                <span className="flex-1 h-[1px] bg-gray-200 dark:bg-gray-800"></span>
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {message.sources.map((src, idx) => (
                  <div key={idx} className="bg-white dark:bg-gray-900/50 border border-gray-200/60 dark:border-gray-800 rounded-xl p-4 text-sm shadow-sm hover:shadow-md transition-shadow group">
                    <div className="font-semibold text-[var(--color-zuel-blue)] dark:text-[var(--color-zuel-cyan)] mb-2 flex items-center gap-2">
                      <span className="bg-blue-50 dark:bg-cyan-950 text-[var(--color-zuel-blue)] dark:text-[var(--color-zuel-cyan)] w-5 h-5 rounded-full flex items-center justify-center text-xs">{idx + 1}</span>
                      <span className="truncate">{src.file_name}</span>
                      <span className="text-xs text-gray-400 font-normal ml-auto">P{src.page_number}</span>
                    </div>
                    <div className="text-gray-600 dark:text-gray-400 line-clamp-3 text-xs leading-relaxed group-hover:text-gray-800 dark:group-hover:text-gray-300 transition-colors">
                      {src.source_text}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
