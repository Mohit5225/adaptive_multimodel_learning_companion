'use client';

import { useUser, useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Shield, Activity, Database, Key, CreditCard, ChevronLeft } from "lucide-react";
import { DecryptionText } from "@/components/DecryptionText";
import Link from "next/link";

export default function ProfilePage() {
  const { user, isLoaded } = useUser();
  const { isSignedIn } = useAuth();
  const router = useRouter();

  // Authentication check
  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.push("/");
    }
  }, [isLoaded, isSignedIn, router]);

  if (!isLoaded || !user) return null;

  return (
    <div className="min-h-screen bg-[var(--color-void)] text-white font-sans relative overflow-hidden flex items-center justify-center p-6">
      
      {/* Background Elements */}
      <div className="fixed inset-0 pointer-events-none">
         <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[var(--color-azure)] to-transparent opacity-20" />
         <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[var(--color-pink)] to-transparent opacity-20" />
      </div>

      <div className="max-w-4xl w-full grid grid-cols-1 md:grid-cols-3 gap-8 relative z-10">
        
        {/* Navigation Back */}
        <Link href="/dashboard" className="absolute -top-16 left-0 flex items-center gap-2 text-[var(--color-mist)] hover:text-white transition-colors group">
            <ChevronLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-mono-tech text-xs tracking-widest uppercase">Return_to_Dashboard</span>
        </Link>
        
        {/* Left Column: The Card */}
        <motion.div 
           initial={{ rotateY: -90, opacity: 0 }}
           animate={{ rotateY: 0, opacity: 1 }}
           transition={{ duration: 0.8, type: "spring" }}
           className="md:col-span-1"
        >
            <div className="glass-card p-1 rounded-2xl h-full min-h-[400px] relative overflow-hidden group perspective-1000">
                {/* Holographic Sheen */}
                <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none z-20" />
                
                <div className="bg-black/80 backdrop-blur-xl rounded-xl h-full p-6 flex flex-col items-center text-center relative z-10 border border-white/5">
                    
                    {/* Avatar Hexagon */}
                    <div className="w-32 h-32 relative mb-6">
                        <div className="absolute inset-0 bg-[var(--color-azure)]/20 animate-pulse rounded-full blur-xl" />
                        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-2xl">
                            <mask id="hex-mask">
                                <path d="M50 0 L93.3 25 L93.3 75 L50 100 L6.7 75 L6.7 25 Z" fill="white" />
                            </mask>
                            <image 
                                href={user.imageUrl} 
                                x="0" y="0" width="100" height="100" 
                                mask="url(#hex-mask)" 
                                preserveAspectRatio="xMidYMid slice"
                            />
                            {/* Rotating Ring */}
                            <path 
                                d="M50 0 L93.3 25 L93.3 75 L50 100 L6.7 75 L6.7 25 Z" 
                                fill="none" 
                                stroke="var(--color-azure)" 
                                strokeWidth="2"
                                strokeDasharray="10 5"
                                className="origin-center animate-[spin_10s_linear_infinite]"
                            />
                        </svg>
                        
                        <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-[var(--color-azure)] rounded-full text-[10px] font-bold tracking-widest text-white border border-white/20 shadow-[0_0_10px_var(--color-azure)]">
                            LVL.05
                        </div>
                    </div>

                    <h2 className="font-display text-2xl text-white mb-1">{user.fullName}</h2>
                    <DecryptionText text={`ID: ${user.id.slice(0, 12)}...`} className="text-[10px] text-[var(--color-mist)] mb-6 block" animateOnHover speed={50} />

                    {/* Status Chips */}
                    <div className="flex flex-col gap-2 w-full mt-auto">
                        <div className="flex items-center justify-between p-2 rounded bg-white/5 border border-white/5">
                            <span className="text-[10px] font-mono-tech text-[var(--color-mist)] uppercase">Clearance</span>
                            <span className="text-xs font-bold text-[var(--color-azure)]">ALPHA</span>
                        </div>
                        <div className="flex items-center justify-between p-2 rounded bg-white/5 border border-white/5">
                            <span className="text-[10px] font-mono-tech text-[var(--color-mist)] uppercase">Status</span>
                            <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> ACTIVE
                            </span>
                        </div>
                    </div>

                </div>
                
                {/* Tech Corners */}
                <div className="absolute top-2 left-2 w-2 h-2 border-t border-l border-[var(--color-azure)]/50" />
                <div className="absolute bottom-2 right-2 w-2 h-2 border-b border-r border-[var(--color-azure)]/50" />
            </div>
        </motion.div>

        {/* Right Column: Stats & Data */}
        <motion.div 
           initial={{ x: 50, opacity: 0 }}
           animate={{ x: 0, opacity: 1 }}
           transition={{ duration: 0.8, delay: 0.2 }}
           className="md:col-span-2 flex flex-col gap-6"
        >
            {/* Header */}
            <div className="border-b border-white/10 pb-4 flex items-end justify-between">
                <div>
                   <h1 className="font-display text-4xl text-white mb-1">Operative Manifest</h1>
                   <p className="text-[var(--color-mist)] text-sm font-light">Digital footprint and neural link statistics.</p>
                </div>
                <Database className="w-6 h-6 text-[var(--color-mist)] opacity-50" />
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
               {[
                   { label: "Neural Renders", value: "34", icon: <Activity className="w-4 h-4 text-[var(--color-pink)]" /> },
                   { label: "Token Usage", value: "8,920", icon: <Key className="w-4 h-4 text-[var(--color-azure)]" /> },
                   { label: "Credits", value: "$12.50", icon: <CreditCard className="w-4 h-4 text-emerald-400" /> },
               ].map((stat, i) => (
                   <motion.div 
                     key={i}
                     whileHover={{ scale: 1.02 }}
                     className="glass-card p-4 rounded-xl flex flex-col gap-2 hover:border-[var(--color-azure)]/30 transition-colors"
                   >
                       <div className="flex items-center justify-between">
                           <span className="font-mono-tech text-[10px] text-[var(--color-mist)] uppercase">{stat.label}</span>
                           {stat.icon}
                       </div>
                       <div className="font-display text-3xl text-white">
                           {stat.value}
                       </div>
                   </motion.div>
               ))}
            </div>

            {/* Recent Activity Log (Mock) */}
            <div className="flex-1 bg-black/40 border border-white/10 rounded-xl p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-50">
                    <DecryptionText text="ENCRYPTED_LOG_V2" className="text-[10px] text-[var(--color-mist)]" />
                </div>
                
                <h3 className="font-display text-lg text-white mb-6">Neural Link Logs</h3>
                
                <div className="space-y-4">
                    {[
                        { action: "Render Initiated", target: "Fractal_v2.py", time: "2m ago", status: "success" },
                        { action: "System Uplink", target: "Auth_Protocol", time: "1h ago", status: "success" },
                        { action: "Token Refresh", target: "Credits_API", time: "5h ago", status: "pending" },
                    ].map((log, i) => (
                        <div key={i} className="flex items-center justify-between border-b border-white/5 pb-2 last:border-0 hover:bg-white/5 p-2 rounded transition-colors group cursor-default">
                             <div className="flex flex-col">
                                 <span className="text-sm text-white group-hover:text-[var(--color-azure)] transition-colors">{log.action}</span>
                                 <span className="text-[10px] font-mono-tech text-[var(--color-mist)]">{log.target}</span>
                             </div>
                             <div className="text-right">
                                 <DecryptionText text={log.time} className="text-[10px] text-[var(--color-mist)] block" speed={50} />
                                 <span className={`text-[9px] uppercase tracking-widest ${
                                     log.status === 'success' ? 'text-emerald-500' : 'text-amber-500'
                                 }`}>
                                     {log.status}
                                 </span>
                             </div>
                        </div>
                    ))}
                </div>
            </div>
        </motion.div>

      </div>
    </div>
  );
}
