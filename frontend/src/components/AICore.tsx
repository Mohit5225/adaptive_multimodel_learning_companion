'use client';

import { motion } from "framer-motion";

type AICoreProps = {
  status: 'idle' | 'processing' | 'speaking';
};

export const AICore = ({ status }: AICoreProps) => {
  return (
    <div className="relative w-32 h-32 flex items-center justify-center">
      {/* Outer Ring */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        className="absolute inset-0 rounded-full border-2 border-[var(--color-cyan)]/20 border-t-[var(--color-cyan)]/80"
      />
      
      {/* Middle Ring - Spinning faster when processing */}
      <motion.div
        animate={{ rotate: -360, scale: status === 'processing' ? [1, 1.1, 1] : 1 }}
        transition={{ duration: status === 'processing' ? 2 : 10, repeat: Infinity, ease: "linear" }}
        className={`absolute inset-4 rounded-full border-2 border-dashed ${
          status === 'processing' ? 'border-[var(--color-pink)]/50' : 'border-[var(--color-cyan)]/40'
        }`}
      />

      {/* Core Sphere */}
      <motion.div
        animate={{ 
          scale: status === 'speaking' ? [1, 1.2, 1] : [1, 1.05, 1],
          filter: status === 'processing' ? 'blur(2px)' : 'blur(0px)'
        }}
        transition={{ duration: status === 'speaking' ? 0.5 : 3, repeat: Infinity, ease: "easeInOut" }}
        className={`w-12 h-12 rounded-full blur-sm backdrop-blur-md shadow-[0_0_30px_currentColor] transition-colors duration-500 ${
          status === 'processing' ? 'bg-[var(--color-pink)] text-[var(--color-pink)]' : 'bg-[var(--color-cyan)] text-[var(--color-cyan)]'
        }`}
      />
      
      {/* Core Glow - Intense when processing */}
       <motion.div
        animate={{ opacity: status === 'processing' ? [0.5, 1, 0.5] : 0.5 }}
        transition={{ duration: 1, repeat: Infinity }}
        className={`absolute inset-0 rounded-full bg-gradient-to-tr from-transparent to-white/10 pointer-events-none mix-blend-overlay`}
      />
    </div>
  );
};
