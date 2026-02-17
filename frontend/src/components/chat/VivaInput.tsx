"use client";

import React, { useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, ArrowUp, Sparkles } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface VivaInputProps {
  onSend?: (message: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function VivaInput({
  onSend,
  placeholder = "Ask anything...",
  disabled = false
}: VivaInputProps) {
  const [isListening, setIsListening] = React.useState(false);
  const [value, setValue] = React.useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [value]);

  const handleSend = () => {
    if (value.trim()) {
      onSend?.(value.trim());
      setValue("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled) handleSend();
    }
  };

  return (
    <div className="w-full z-50 pointer-events-none">
      {/* Gradient fade effect */}
      <div className="absolute inset-x-0 bottom-0 h-32 bg-linear-to-t from-[#050505] via-[#050505]/80 to-transparent pointer-events-none" />

      <div className="relative flex justify-center px-4 pb-6 pt-2">
        {/* Main Input Container */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className={cn(
            "flex items-end gap-2 p-2 pl-6 rounded-full w-full max-w-2xl pointer-events-auto relative",
            "bg-zinc-900",
            "border-2 border-zinc-700 shadow-xl",
            "transition-all duration-300",
            disabled ? "opacity-50 pointer-events-none grayscale" : "focus-within:border-indigo-500/50 focus-within:shadow-2xl"
          )}
        >

          {/* Textarea */}
          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? "Waiting for response..." : placeholder}
            rows={1}
            disabled={disabled}
            className={cn(
              "flex-1 min-h-[44px] max-h-[120px] resize-none py-3",
              "bg-transparent border-none shadow-none",
              "text-white placeholder:text-zinc-500",
              "text-[1rem] font-medium tracking-wide",
              "focus-visible:ring-0 focus-visible:ring-offset-0",
              "scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent disabled:cursor-not-allowed"
            )}
          />

          {/* Action Buttons */}
          <div className="flex items-center gap-1 pb-0.5">
            <AnimatePresence mode="wait">
              {value.trim().length > 0 ? (
                <motion.div
                  key="send"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ duration: 0.15 }}
                >
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        onClick={handleSend}
                        size="icon"
                        className={cn(
                          "h-10 w-10 rounded-full",
                          "bg-indigo-500 text-white hover:bg-indigo-400",
                          "shadow-lg shadow-indigo-500/20",
                          "transition-all duration-200 hover:scale-110 active:scale-95"
                        )}
                      >
                        <ArrowUp className="h-5 w-5" strokeWidth={3} />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent
                      side="top"
                      className="bg-black/90 border-white/10 text-white/80 text-xs"
                    >
                      Send <span className="text-white/40 ml-1">↵</span>
                    </TooltipContent>
                  </Tooltip>
                </motion.div>
              ) : (
                <motion.div
                  key="mic"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="relative"
                >
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        onClick={() => setIsListening(!isListening)}
                        size="icon"
                        variant="ghost"
                        className={cn(
                          "h-10 w-10 rounded-full relative",
                          isListening
                            ? "bg-rose-500 text-white shadow-lg shadow-rose-500/20"
                            : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white",
                          "transition-all duration-300 hover:scale-110 active:scale-95"
                        )}
                      >
                        {/* Listening pulse ring */}
                        {isListening && (
                          <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{
                              opacity: [0.3, 0.6, 0.3],
                              scale: [1, 1.4, 1]
                            }}
                            transition={{
                              duration: 1.5,
                              repeat: Infinity,
                              ease: "easeInOut"
                            }}
                            className="absolute inset-0 rounded-full border-2 border-rose-500/40"
                          />
                        )}
                        <Mic className="h-5 w-5" strokeWidth={2.5} />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent
                      side="top"
                      className="bg-black/90 border-white/10 text-white/80 text-xs"
                    >
                      {isListening ? "Stop listening" : "Voice input"}
                    </TooltipContent>
                  </Tooltip>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Keyboard shortcut hint */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="absolute -top-6 left-1/2 -translate-x-1/2 pointer-events-none"
        >
          <span className="text-[10px] text-white/20 font-mono tracking-wide flex items-center gap-1.5">
            <Sparkles className="h-2.5 w-2.5" />
            Shift+Enter for new line
          </span>
        </motion.div>
      </div>
    </div>
  );
}
