import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Pause, Box, Code, Share2 } from "lucide-react";
import { GlassContainer } from "./GlassContainer";

interface HolographicVideoPlayerProps {
  onPlay?: () => void;
}

export function HolographicVideoPlayer({ onPlay }: HolographicVideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0);

  // Minimal loading simulation
  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer);
          setLoading(false);
          return 100;
        }
        return prev + 1.5;
      });
    }, 40);
    return () => clearInterval(timer);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ y: -5, transition: { duration: 0.5, ease: "easeOut" } }}
      className="relative w-full max-w-3xl mx-auto my-12 group z-20"
    >
      <GlassContainer
        intensity="high"
        className="overflow-hidden p-0 rounded-3xl border border-white/5 bg-black/80 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8)]"
      >
        <div className="bg-[#020202] relative aspect-video flex items-center justify-center overflow-hidden">

          {/* Header - Ultra minimal */}
          <div className="absolute top-4 left-6 flex items-center gap-3 z-30">
            <span className="w-1.5 h-1.5 rounded-full bg-sc-cyan shadow-[0_0_8px_rgba(0,240,255,0.8)]" />
            <span className="text-[10px] text-white/30 font-mono tracking-[0.2em] uppercase">Render V2</span>
          </div>

          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div
                key="loading"
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col items-center gap-8 z-20"
              >
                {/* Ultra Minimal Loader */}
                <div className="relative w-16 h-16">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0 rounded-full border-[1.5px] border-t-white/80 border-r-white/20 border-b-white/20 border-l-white/20"
                  />
                  <div className="absolute inset-0 flex items-center justify-center font-mono text-white/50 text-[10px]">
                    {Math.round(progress)}%
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="video"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1 }}
                className="w-full h-full relative z-0"
              >
                {/* Minimal Abstract Placeholder */}
                <div className="absolute inset-0 bg-transparent flex items-center justify-center">
                  {/* Static geometry placeholder */}
                  <div className="w-[1px] h-[100px] bg-gradient-to-b from-transparent via-sc-cyan/20 to-transparent" />
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ duration: 1.5, delay: 0.2 }}
                    className="w-[200px] h-[1px] bg-gradient-to-r from-transparent via-sc-cyan/20 to-transparent absolute"
                  />

                  {/* Play Button - Centered & Minimal */}
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="group-hover:scale-110 transition-transform duration-500 p-6 rounded-full bg-white/5 backdrop-blur-md border border-white/10 hover:bg-white/10 text-white shadow-2xl"
                  >
                    {isPlaying ? <Pause fill="currentColor" size={20} /> : <Play fill="currentColor" size={20} className="ml-1" />}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Minimal Action Bar - Floating inside the container bottom */}
        <div className="absolute bottom-6 left-0 right-0 flex justify-center gap-6 z-30 opacity-0 group-hover:opacity-100 transition-opacity duration-500 transform translate-y-2 group-hover:translate-y-0">
          <ActionButton icon={<Box size={14} />} label="3D View" />
          <ActionButton icon={<Code size={14} />} label="Code" />
          <ActionButton icon={<Share2 size={14} />} label="Share" />
        </div>
      </GlassContainer>
    </motion.div>
  );
}

function ActionButton({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <motion.button
      whileHover={{ y: -2 }}
      className="flex items-center gap-2 px-5 py-2.5 bg-black/40 backdrop-blur-xl border border-white/5 rounded-full text-[11px] text-white/70 font-medium tracking-wide hover:bg-white/5 hover:text-white transition-all hover:border-white/20"
    >
      {icon}
      <span>{label}</span>
    </motion.button>
  );
}
