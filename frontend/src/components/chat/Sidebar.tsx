"use client";

import React, { useEffect, useState } from "react";
import { Plus, Settings, User, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { listChats, archiveChat, type Chat } from "@/lib/api";

interface SidebarProps {
  className?: string;
  onNewChat?: () => void;
  onSelectChat?: (chatId: string) => void;
  activeChatId?: string | null;
  refreshTrigger?: number; // increment to force refresh
}

function groupChatsByDate(chats: Chat[]) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);
  const weekAgo = new Date(today.getTime() - 7 * 86400000);
  const monthAgo = new Date(today.getTime() - 30 * 86400000);

  const groups: Record<string, Chat[]> = {
    Today: [],
    Yesterday: [],
    "Previous 7 Days": [],
    "Previous 30 Days": [],
    Older: [],
  };

  for (const chat of chats) {
    const d = new Date(chat.created_at);
    if (d >= today) groups["Today"].push(chat);
    else if (d >= yesterday) groups["Yesterday"].push(chat);
    else if (d >= weekAgo) groups["Previous 7 Days"].push(chat);
    else if (d >= monthAgo) groups["Previous 30 Days"].push(chat);
    else groups["Older"].push(chat);
  }

  return groups;
}

export function Sidebar({ className, onNewChat, onSelectChat, activeChatId, refreshTrigger }: SidebarProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchChats = async () => {
    try {
      const data = await listChats();
      setChats(data);
    } catch (err) {
      console.error("Failed to fetch chats:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChats();
  }, [refreshTrigger]);

  const handleDelete = async (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    try {
      await archiveChat(chatId);
      setChats((prev) => prev.filter((c) => c.id !== chatId));
    } catch (err) {
      console.error("Failed to delete chat:", err);
    }
  };

  const grouped = groupChatsByDate(chats);

  return (
    <div className={cn("hidden md:flex flex-col h-full w-[260px] bg-zinc-900/50 border-r border-zinc-800/50 backdrop-blur-xl transition-all duration-300", className)}>
      <div className="p-4">
        <Button
          variant="outline"
          onClick={onNewChat}
          className="w-full justify-start gap-2 bg-zinc-800/50 border-zinc-700/50 hover:bg-zinc-800 hover:text-white transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Chat</span>
        </Button>
      </div>

      <ScrollArea className="flex-1 px-2">
        <div className="space-y-4 p-2">
          {loading ? (
            <div className="text-xs text-zinc-500 px-2">Loading chats...</div>
          ) : chats.length === 0 ? (
            <div className="text-xs text-zinc-500 px-2">No chats yet. Start a new conversation!</div>
          ) : (
            Object.entries(grouped).map(([group, items]) => {
              if (items.length === 0) return null;

              return (
                <div key={group} className="space-y-1">
                  <h3 className="px-2 text-xs font-medium text-zinc-500 mb-2">{group}</h3>
                  {items.map((chat) => (
                    <div key={chat.id} className="relative group/item">
                      <Button
                        variant="ghost"
                        onClick={() => onSelectChat?.(chat.id)}
                        className={cn(
                          "w-full justify-start text-sm font-normal hover:text-zinc-100 hover:bg-zinc-800/50 h-auto py-2 px-2 pr-8",
                          activeChatId === chat.id
                            ? "text-white bg-zinc-800/70"
                            : "text-zinc-400"
                        )}
                      >
                        <div className="truncate text-left w-[180px]">
                          {chat.title}
                        </div>
                      </Button>
                      <button
                        onClick={(e) => handleDelete(e, chat.id)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover/item:opacity-100 transition-opacity text-zinc-500 hover:text-red-400 p-1"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-zinc-800/50 space-y-1">
        <Button variant="ghost" className="w-full justify-start gap-2 text-zinc-400 hover:text-zinc-100">
          <User className="w-4 h-4" />
          <span>Profile</span>
        </Button>
        <Button variant="ghost" className="w-full justify-start gap-2 text-zinc-400 hover:text-zinc-100">
          <Settings className="w-4 h-4" />
          <span>Settings</span>
        </Button>
      </div>
    </div>
  );
}
