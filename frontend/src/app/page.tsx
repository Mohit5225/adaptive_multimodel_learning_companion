'use client';

import { SignedIn, SignedOut, SignInButton } from "@clerk/nextjs";
import Link from "next/link";
import { ArrowRight, Sparkles, Play, Zap, Mic, Cpu } from "lucide-react";
import { color, motion } from "framer-motion";

export default function Home() {
  return (
    <div className="min-h-screen relative overflow-hidden font-sans bg-[var(--color-void)] text-white">
      
      {/* Navigation */}
      <nav className="absolute top-0 left-0 right-0 p-6 flex justify-between items-center z-50">
        <div className="flex items-center gap-3 group cursor-pointer">
            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center jelly-button">
                <div className="w-6 h-6 bg-black rounded-full" />
            </div>
            <span className="text-2xl font-bold tracking-tight group-hover:text-[var(--color-cyan)] transition-colors">ManimGen</span>
        </div>
        
        <div className="flex items-center gap-4">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="jelly-button px-6 py-3 bg-white/5 hover:bg-white text-white hover:text-black border-2 border-white/20 rounded-xl font-bold transition-all">
                  Sign In
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <Link href="/dashboard">
                <button className="jelly-button px-6 py-3 bg-[var(--color-cyan)] text-black rounded-xl font-bold hover:shadow-[0_0_20px_var(--color-cyan)] border-2 border-transparent">
                  Dashboard
                </button>
              </Link>
            </SignedIn>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex flex-col justify-center items-center text-center px-4 pt-20">
        
        {/* Floating Abstract Shapes */}
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-[var(--color-purple)]/20 rounded-full blur-[100px] animate-float-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[var(--color-cyan)]/20 rounded-full blur-[100px] animate-float-slow" style={{ animationDelay: '1s' }} />

        <div className="relative z-10 max-w-5xl mx-auto">
            {/* Status Batch */}
            <motion.div 
               initial={{ y: 20, opacity: 0 }}
               animate={{ y: 0, opacity: 1 }}
               className="inline-flex items-center gap-2 px-4 py-2 rounded-full border-2 border-white/10 bg-white/5 backdrop-blur-md mb-8"
            >
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-sm font-bold tracking-wide">SYSTEM OPERATIONAL v2.4</span>
            </motion.div>

            <motion.h1 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="text-6xl md:text-8xl font-display font-medium leading-[0.9] text-white tracking-tight mb-8"
            >
              Personal <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--color-cyan)] to-[var(--color-purple)]" style={{color: "#418fe7ff"}}>Learning.</span>
            </motion.h1>

            <motion.p 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-xl md:text-2xl text-gray-300 max-w-2xl mx-auto mb-12 leading-relaxed"
            >
              Give your learning a curve. <br/>
              Lets Start Learning with Prakash.
            </motion.p>

            <motion.div 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-6"
            >
               <SignedOut>
                   <SignInButton mode="modal">
                       <button className="jelly-button group relative px-10 py-5 bg-white text-black text-xl font-bold rounded-2xl overflow-hidden hover:shadow-[0_0_40px_rgba(255,255,255,0.3)]">
                           <span className="relative z-10 flex items-center gap-2">
                               START CREATING <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
                           </span>
                           {/* Pulse Effect */}
                           <div className="absolute inset-0 bg-[var(--color-cyan)]/20 animate-pulse opacity-0 group-hover:opacity-100 transition-opacity" />
                       </button>
                   </SignInButton>
               </SignedOut>
               <SignedIn>
                   <Link href="/dashboard">
                       <button className="jelly-button px-10 py-5 bg-[var(--color-cyan)] text-black text-xl font-bold rounded-2xl hover:shadow-[0_0_30px_var(--color-cyan)] flex items-center gap-3">
                           ENTER STUDIO <Zap className="w-6 h-6 fill-black" />
                       </button>
                   </Link>
               </SignedIn>
               
               <button className="jelly-button px-8 py-5 bg-white/5 border-2 border-white/10 text-white text-xl font-bold rounded-2xl hover:bg-white/10 flex items-center gap-3">
                   <Play className="w-6 h-6 fill-white" /> WATCH DEMO
               </button>
            </motion.div>
        </div>

        {/* Feature Grid with Guided Attention */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto mt-32 w-full px-6">
            {[
                { title: "No-Code Velocity", desc: "Speak your vision.", icon: <Mic className="w-8 h-8 text-[var(--color-cyan)]" /> },
                { title: "Fluid Physics", desc: "Dopamine-driven UI.", icon: <Sparkles className="w-8 h-8 text-[var(--color-purple)]" /> },
                { title: "Universal Mesh", desc: "Connects everything.", icon: <Cpu className="w-8 h-8 text-emerald-400" /> },
            ].map((feature, i) => (
                <motion.div
                   key={i}
                   initial={{ opacity: 0, y: 50 }}
                   whileInView={{ opacity: 1, y: 0 }}
                   viewport={{ once: true }}
                   transition={{ delay: i * 0.2 }}
                   className="universal-card group text-left hover:bg-white/5 bg-[#0A0A15]/50 backdrop-blur-sm"
                >
                    <div className="w-16 h-16 rounded-2xl bg-white/5 border-2 border-white/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                        {feature.icon}
                    </div>
                    <h3 className="text-2xl font-bold mb-2">{feature.title}</h3>
                    <p className="text-gray-400 text-lg leading-relaxed">{feature.desc}</p>
                </motion.div>
            ))}
        </div>

      </section>

      {/* Footer */}
      <footer className="py-12 text-center border-t-2 border-white/5 mt-20">
          <p className="text-gray-500 font-bold tracking-widest text-sm">UNIVERSAL DESIGN SYSTEM &copy; 2026</p>
      </footer>

    </div>
  );
}
