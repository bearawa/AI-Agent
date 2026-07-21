import React, { useEffect, useState } from "react";
import { MessageSquare, Plus, Trash2, Settings } from "lucide-react";
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
  }, [currentSessionId]);

  const fetchSessions = async () => {
    try {
      const res = await fetch("/api/sessions");
      const data = await res.json();
      setSessions(data);
    } catch (e) {
      console.error("Failed to fetch sessions", e);
    }
  };

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`/api/sessions/${id}`, { method: 'DELETE' });
      if (currentSessionId === id) {
        onNewSession();
      } else {
        fetchSessions();
      }
    } catch (err) {
      console.error("Failed to delete session", err);
    }
  };

  return (
    <div className="w-[260px] h-full bg-[#171717] text-white flex flex-col p-2">
      <button
        onClick={async () => {
          await onNewSession();
        }}
        className="flex items-center gap-2 p-3 rounded-md hover:bg-white/10 transition-colors border border-white/20 mb-4"
      >
        <Plus size={16} />
        <span className="text-sm">New chat</span>
      </button>

      <div className="flex-1 overflow-y-auto">
        <div className="text-xs text-gray-500 font-medium mb-2 px-2">History</div>
        {sessions.map((session) => (
          <div key={session.session_id} className="relative group flex items-center">
            <button
              onClick={() => onSelectSession(session.session_id)}
              className={cn(
                "w-full flex items-center gap-3 p-3 rounded-md hover:bg-white/10 transition-colors text-left",
                currentSessionId === session.session_id ? "bg-white/10" : ""
              )}
            >
              <MessageSquare size={16} className="text-gray-400 shrink-0" />
              <span className="text-sm truncate flex-1 pr-6">{session.title || "New chat"}</span>
            </button>
            <button
              onClick={(e) => handleDeleteSession(session.session_id, e)}
              className="absolute right-2 p-1 text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
              title="Delete session"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>

      <div className="mt-auto border-t border-white/10 pt-2">
         <a
          href="/admin"
          className="flex items-center gap-2 p-3 rounded-md hover:bg-white/10 transition-colors w-full text-left text-sm"
        >
          <Settings size={16} className="text-gray-400" />
          Settings & Admin
        </a>
      </div>
    </div>
  );
}
