"use client";

import React from "react";
import { motion } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot } from "lucide-react";
import { cn } from "@/lib/utils";

interface TypingIndicatorProps {
  className?: string;
}

export function TypingIndicator({ className }: TypingIndicatorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
      className={cn("flex gap-3 w-full mb-6", className)}
    >
      {/* AI Avatar */}
      <Avatar className="h-9 w-9 shrink-0 border border-sc-cyan/20 bg-sc-cyan/5 shadow-[0_0_15px_rgba(0,240,255,0.1)]">
        <AvatarFallback className="bg-transparent text-sc-cyan">
          <Bot className="h-4 w-4" />
        </AvatarFallback>
      </Avatar>

      {/* Typing Animation */}
      <div className="flex flex-col gap-2 pt-1">
        <span className="text-[10px] text-sc-cyan/60 font-mono tracking-[0.15em] uppercase">
          Socratic
        </span>

        {/* Animated dots */}
        <div className="flex items-center gap-1.5 h-6">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              animate={{
                scale: [1, 1.3, 1],
                opacity: [0.4, 1, 0.4],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.15,
                ease: "easeInOut",
              }}
              className="w-2 h-2 rounded-full bg-sc-cyan/60"
            />
          ))}
        </div>

        {/* Skeleton lines for "thinking" effect */}
        <div className="flex flex-col gap-2 mt-1">
          <Skeleton className="h-3 w-48 bg-white/5" />
          <Skeleton className="h-3 w-32 bg-white/5" />
        </div>
      </div>
    </motion.div>
  );
}
