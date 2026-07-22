import React, { useEffect, useState } from "react";
import { MessageSquare, Plus, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Session {
  session_id: string;
  title: string;
}

interface SidebarProps {
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
}

export default function Sidebar({ currentSessionId, onSelectSession, onNewSession }: SidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await fetch("/api/sessions");
      const data = await res.json();
      setSessions(data);
    } catch (e) {
      console.error("Failed to fetch sessions", e);
    }
  };

  return (
    <div className="w-[280px] h-full bg-[#014F7A] text-white flex flex-col p-4 shadow-xl z-10">
      <div className="mb-6 flex items-center justify-center bg-white/5 rounded-2xl p-4 border border-white/10 backdrop-blur-sm">
        <img
          src="/images/zuel-logo.webp"
          alt="ZUEL Logo"
          className="h-14 object-contain filter invert opacity-90"
        />
      </div>

      <button
        onClick={async () => {
          await onNewSession();
          fetchSessions();
        }}
        className="flex items-center justify-between p-3.5 rounded-xl bg-[var(--color-zuel-cyan)] hover:bg-[var(--color-zuel-cyan-dark)] active:scale-[0.98] transition-all font-medium mb-6 shadow-md"
      >
        <span className="text-sm tracking-wide">新建智能咨询</span>
        <Plus size={18} />
      </button>

      <div className="flex-1 overflow-y-auto pr-1 -mr-1 custom-scrollbar">
        <div className="text-xs text-blue-200 uppercase tracking-wider font-bold mb-3 px-1">会话历史</div>
        <div className="flex flex-col gap-1.5">
          {sessions.map((session) => (
            <button
              key={session.session_id}
              onClick={() => onSelectSession(session.session_id)}
              className={cn(
                "w-full flex items-center gap-3 p-3 rounded-xl transition-all text-left group",
                currentSessionId === session.session_id
                  ? "bg-white/15 text-white shadow-sm ring-1 ring-white/20"
                  : "text-blue-100 hover:bg-white/10 hover:text-white"
              )}
            >
              <MessageSquare size={16} className={cn(
                "shrink-0 transition-colors",
                currentSessionId === session.session_id ? "text-[var(--color-zuel-cyan)]" : "text-blue-300 group-hover:text-blue-200"
              )} />
              <span className="text-sm truncate flex-1 font-medium">{session.title || "新对话"}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
