"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Bot, User } from "lucide-react";
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  role: "user" | "ai";
  content: string;
  timestamp?: string;
}

export function MessageBubble({ role, content, timestamp }: MessageBubbleProps) {
  const isUser = role === "user";
  const displayTime = timestamp ?? new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <motion.div
      initial={{ opacity: 0, y: 15, x: isUser ? 20 : -20 }}
      animate={{ opacity: 1, y: 0, x: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "flex gap-4 w-full mb-8 group",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <Tooltip>
        <TooltipTrigger asChild>
          <Avatar className={cn(
            "h-10 w-10 shrink-0 border-2 transition-all duration-300",
            isUser
              ? "border-transparent bg-zinc-700 hidden" // Hide user avatar for cleaner look
              : "border-indigo-200 bg-indigo-500 text-white shadow-sm"
          )}>
            {isUser ? (
              <>
                <AvatarImage src="" alt="You" />
                <AvatarFallback className="bg-transparent text-white/70">
                  <User className="h-4 w-4" />
                </AvatarFallback>
              </>
            ) : (
              <>
                <AvatarImage src="" alt="Socratic AI" />
                <AvatarFallback className="bg-transparent text-white">
                  <Bot className="h-5 w-5" strokeWidth={2.5} />
                </AvatarFallback>
              </>
            )}
          </Avatar>
        </TooltipTrigger>
        <TooltipContent
          side={isUser ? "left" : "right"}
          className="bg-black/90 border-white/10 text-white/80 text-xs"
        >
          {isUser ? "You" : "Socratic AI"}
        </TooltipContent>
      </Tooltip>

      {/* Message Content */}
      <Tooltip>
        <TooltipTrigger asChild>
          <Card className={cn(
            "max-w-[85%] border-0 shadow-none",
            isUser
              ? "bg-zinc-800 rounded-2xl rounded-tr-sm text-white"
              : "bg-transparent pl-0"
          )}>
            <CardContent className={cn(
              "p-0",
              isUser ? "px-5 py-3" : "py-1"
            )}>
              {!isUser && (
                <span className="text-xs text-zinc-400 font-bold mb-1 block uppercase tracking-wide">
                  Socratic AI
                </span>
              )}
              <div className={cn(
                "text-[1rem] leading-relaxed break-words",
                isUser
                  ? "font-medium"
                  : "text-zinc-200 font-normal"
              )}>
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </TooltipTrigger>
        <TooltipContent
          side="bottom"
          className="bg-black/90 border-white/10 text-white/50 text-[10px] font-mono opacity-0 group-hover:opacity-100 transition-opacity"
        >
          {displayTime}
        </TooltipContent>
      </Tooltip>
    </motion.div>
  );
}
