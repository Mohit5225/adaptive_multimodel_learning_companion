import { cn } from "@/lib/utils";
import { motion, HTMLMotionProps } from "framer-motion";
import React from "react";

interface GlassContainerProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  className?: string;
  intensity?: "low" | "medium" | "high";
  glow?: boolean;
}

export const GlassContainer = React.forwardRef<HTMLDivElement, GlassContainerProps>(
  ({ children, className, intensity = "medium", glow = false, ...props }, ref) => {
    // Ultra-minimal dark glass styles
    const blurMap = {
      low: "backdrop-blur-md bg-black/40 border-white/5",
      medium: "backdrop-blur-xl bg-black/60 border-white/5 shadow-2xl",
      high: "backdrop-blur-3xl bg-black/80 border-white/10 shadow-2xl",
    };

    return (
      <motion.div
        ref={ref}
        className={cn(
          "rounded-3xl border transition-all duration-500 relative overflow-hidden",
          blurMap[intensity],
          // Subtle glow logic - avoid harsh cyan borders unless interactive state
          glow && "shadow-[0_0_40px_-10px_rgba(0,0,0,0.5)] border-white/10 hover:border-sc-cyan/20 hover:shadow-[0_0_30px_-5px_rgba(0,240,255,0.1)]",
          className
        )}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.98 }}
        {...props}
      >
        {/* Extremely subtle noise texture for realism (optional, keep minimal) */}
        <div className="absolute inset-0 bg-transparent pointer-events-none opacity-[0.02] mix-blend-overlay" />

        <div className="relative z-10">
          {children}
        </div>
      </motion.div>
    );
  }
);

GlassContainer.displayName = "GlassContainer";
