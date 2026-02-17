"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getModes, type ModeInfo } from "@/lib/api";

// Fallback modes in case API hasn't loaded yet
const FALLBACK_MODES: ModeInfo[] = [
  { key: "socratic", label: "Socratic", description: "Guided discovery through questions", icon: "🧠" },
  { key: "quiz", label: "Quiz", description: "Test knowledge with MCQs and challenges", icon: "📝" },
  { key: "casual", label: "Casual", description: "Laid-back learning like chatting with a friend", icon: "😎" },
  { key: "eli5", label: "ELI5", description: "Super simple explanations", icon: "👶" },
  { key: "exam_prep", label: "Exam Prep", description: "Focused revision and board exam strategy", icon: "🎯" },
];

interface ModeSelectorProps {
  activeMode: string;
  onModeChange: (mode: string) => void;
}

export function ModeSelector({ activeMode, onModeChange }: ModeSelectorProps) {
  const [modes, setModes] = useState<ModeInfo[]>(FALLBACK_MODES);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch modes from backend
  useEffect(() => {
    getModes()
      .then((data) => {
        if (data && data.length > 0) setModes(data);
      })
      .catch(() => {
        // Fallback modes already set
      });
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const current = modes.find((m) => m.key === activeMode) || modes[0];

  return (
    <div ref={dropdownRef} className="relative inline-block">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-full
                   bg-zinc-900/80 border border-zinc-700/50 backdrop-blur-sm
                   hover:border-zinc-600 hover:bg-zinc-800/80
                   transition-all duration-200 cursor-pointer group"
      >
        <span className="text-sm">{current.icon}</span>
        <span className="text-[11px] font-mono tracking-wide text-zinc-300 group-hover:text-zinc-100 transition-colors">
          {current.label.toUpperCase()}
        </span>
        <svg
          className={`w-3 h-3 text-zinc-500 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="absolute left-0 top-full mt-2 z-50 w-64
                       bg-zinc-900/95 border border-zinc-700/60 rounded-xl
                       backdrop-blur-xl shadow-2xl shadow-black/40 overflow-hidden"
          >
            <div className="px-3 py-2 border-b border-zinc-800/80">
              <span className="text-[10px] font-mono text-zinc-500 tracking-widest uppercase">
                Teaching Mode
              </span>
            </div>

            <div className="py-1">
              {modes.map((mode) => {
                const isActive = mode.key === activeMode;
                return (
                  <button
                    key={mode.key}
                    onClick={() => {
                      onModeChange(mode.key);
                      setIsOpen(false);
                    }}
                    className={`w-full flex items-start gap-3 px-3 py-2.5 text-left
                               transition-all duration-150 cursor-pointer
                               ${isActive
                                 ? "bg-indigo-500/10 border-l-2 border-indigo-500"
                                 : "border-l-2 border-transparent hover:bg-zinc-800/60"
                               }`}
                  >
                    <span className="text-lg mt-0.5 shrink-0">{mode.icon}</span>
                    <div className="min-w-0">
                      <div className={`text-sm font-medium ${isActive ? "text-indigo-300" : "text-zinc-200"}`}>
                        {mode.label}
                      </div>
                      <div className="text-[11px] text-zinc-500 leading-tight mt-0.5">
                        {mode.description}
                      </div>
                    </div>
                    {isActive && (
                      <div className="ml-auto shrink-0 mt-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
