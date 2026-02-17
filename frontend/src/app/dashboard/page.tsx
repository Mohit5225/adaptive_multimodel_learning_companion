'use client'

import { UserButton, useUser, useAuth } from "@clerk/nextjs";
import { useEffect, useState, useRef } from "react";
import { apiCall } from "@/lib/api";
import { Mic, Home, Film, User, Play, Loader2, Sparkles, Activity, ShieldCheck, Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AICore } from "@/components/AICore";
import { DecryptionText } from "@/components/DecryptionText";

// --- Types ---
type Project = {
  id: string;
  prompt: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  video_url?: string;
  error?: string;
};

// --- Mock Data ---
const SYSTEM_CHIPS = [
  { label: "Gravity Visualizer", icon: <Zap className="w-4 h-4" /> },
  { label: "Pi Derivation", icon: <Activity className="w-4 h-4" /> },
  { label: "Fractal Render", icon: <Sparkles className="w-4 h-4" /> },
];

export default function Dashboard() {
  const { user, isLoaded } = useUser();
  const { isSignedIn } = useAuth();
  const router = useRouter();
  
  const [userData, setUserData] = useState<any>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [prompt, setPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const [aiStatus, setAiStatus] = useState<'idle' | 'processing' | 'speaking'>('idle');

  // Authentication check
  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.push("/");
    }
  }, [isLoaded, isSignedIn, router]);

  useEffect(() => {
    if (isLoaded && user) {
      fetchUserData();
      fetchProjects();
      startPolling();
    }
    return () => stopPolling();
  }, [isLoaded, user]);

  const startPolling = () => {
    stopPolling();
    pollingRef.current = setInterval(fetchProjects, 3000); 
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const fetchUserData = async () => {
    try {
      const response = await apiCall('/api/users/me');
      const data = await response.json();
      setUserData(data);
    } catch (error) {
      console.error('Error fetching user data:', error);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await apiCall('/api/projects');
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
        
        const hasActiveJobs = data.some((p: Project) => 
          p.status === 'pending' || p.status === 'processing'
        );
        
        if (hasActiveJobs) {
            setAiStatus('processing');
        } else if (aiStatus === 'processing') {
            setAiStatus('idle');
        }
      }
    } catch (error) {
      console.error('Error fetching projects:', error);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsGenerating(true);
    setAiStatus('processing');
    
    // Simulate audio feedback
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.5);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.5);
    
    try {
      const response = await apiCall('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prompt })
      });

      if (response.ok) {
        setPrompt("");
        await fetchProjects();
        startPolling(); 
      }
    } catch (error) {
      console.error('Error starting generation:', error);
      setAiStatus('idle');
    }
    setIsGenerating(false);
  };

  const handleMicClick = () => {
      setIsListening(!isListening);
      if (!isListening) {
          // Simulate listening state visually
          setAiStatus('speaking');
      } else {
          setAiStatus('idle');
      }
  };

  const handleChipClick = (chipLabel: string) => {
    setPrompt(chipLabel);
  };

  if (!isLoaded) return null;

  return (
    <div className="min-h-screen flex bg-[var(--color-void)] text-white font-sans overflow-hidden">
      
      {/* Sidebar Navigation (Icon-First) */}
      <nav className="hidden md:flex flex-col w-24 bg-[#0A0A15] border-r-2 border-white/10 p-6 items-center gap-12 z-50 h-screen sticky top-0">
          
          {/* Logo / Home */}
          <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center jelly-button cursor-pointer shadow-[0_0_20px_rgba(255,255,255,0.2)]">
             <div className="w-8 h-8 bg-black rounded-full" />
          </div>
          
          {/* Main Nav Links */}
          <div className="flex flex-col gap-8 w-full items-center">
              <Link href="/dashboard" className="flex flex-col items-center gap-2 group jelly-button">
                  <div className="w-14 h-14 rounded-2xl bg-[var(--color-cyan)] flex items-center justify-center text-black group-hover:scale-110 transition-transform shadow-[0_0_15px_var(--color-cyan)]">
                      <Home className="w-7 h-7 stroke-[3px]" />
                  </div>
                  <span className="text-xs font-bold text-white tracking-widest opacity-0 group-hover:opacity-100 transition-opacity absolute left-20 bg-black px-2 py-1 rounded border border-white/20">HOME</span>
              </Link>
          </div>
          
          {/* Bottom Profile - Glass Capsule */}
          <div className="mt-auto mb-4">
             <div className="p-1 rounded-2xl border-2 border-white/10 bg-white/5 hover:bg-white/10 transition-colors jelly-button">
                 <Link href="/profile" className="flex flex-col items-center gap-1 group">
                    <UserButton afterSignOutUrl="/" appearance={{
                        elements: {
                            userButtonAvatarBox: "w-12 h-12 rounded-xl border-2 border-white/20"
                        }
                    }}/>
                 </Link>
             </div>
          </div>
      </nav>

      <main className="flex-1 p-6 md:p-12 overflow-y-auto relative">
        
        {/* Top Header */}
        <header className="flex justify-between items-center mb-12">
            <div>
                <motion.h1 
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="text-4xl md:text-5xl font-bold mb-2 tracking-tight"
                >
                    Hello, <span className="text-[var(--color-cyan)]">{user?.firstName || 'Creator'}</span>
                </motion.h1>
                <p className="text-xl text-gray-400">Ready to create magic?</p>
            </div>
            <div className="hidden md:block">
               <div className="flex items-center gap-2 px-4 py-2 bg-[#0A0A15] rounded-xl border-2 border-white/10">
                   <Activity className="w-5 h-5 text-emerald-400" />
                   <span className="font-bold">System Visuals Active</span>
               </div>
            </div>
        </header>

        {/* Mega-Mic & Input Section */}
        <section className="max-w-4xl mx-auto mb-16 relative z-10">
           
           <div className="bg-[#0A0A15] border-2 border-white/10 rounded-[2rem] p-2 flex items-center shadow-2xl relative hover-spotlight group transition-all duration-300 focus-within:border-[var(--color-cyan)]">
               
               {/* Mega-Mic Button */}
               <motion.button 
                   whileTap={{ scale: 0.9 }}
                   onClick={handleMicClick}
                   className={`w-20 h-20 rounded-full flex-shrink-0 flex items-center justify-center mr-4 transition-all duration-300 ${
                       isListening 
                       ? 'bg-[var(--color-pink)] animate-heartbeat shadow-[0_0_30px_var(--color-pink)]' 
                       : 'bg-[#1A1A2E] hover:bg-[var(--color-pink)]'
                   }`}
               >
                   <Mic className={`w-8 h-8 stroke-[3px] ${isListening ? 'text-white' : 'text-gray-400 group-hover:text-white'}`} />
               </motion.button>

               <form onSubmit={handleGenerate} className="flex-1 flex items-center pr-4">
                   <input 
                       type="text" 
                       value={prompt}
                       onChange={(e) => setPrompt(e.target.value)}
                       placeholder={isListening ? "Listening..." : "Describe your video idea..."}
                       className="w-full bg-transparent border-none text-2xl text-white placeholder-gray-600 focus:ring-0 font-medium h-16"
                       disabled={isGenerating}
                   />
                   
                   <button 
                       type="submit"
                       disabled={!prompt.trim() || isGenerating}
                       className="jelly-button px-8 py-4 bg-[var(--color-cyan)] text-black rounded-xl font-bold text-lg disabled:opacity-50 disabled:grayscale hover:shadow-[0_0_20px_var(--color-cyan)]"
                   >
                       {isGenerating ? <Loader2 className="w-6 h-6 animate-spin" /> : "CREATE"}
                   </button>
               </form>
           </div>
           
           {/* Quick Chips */}
           <div className="flex justify-center gap-4 mt-8">
               {SYSTEM_CHIPS.map((chip, i) => (
                   <button
                       key={i}
                       onClick={() => handleChipClick(chip.label)}
                       className="jelly-button px-6 py-3 bg-[#0A0A15] border-2 border-white/10 rounded-xl flex items-center gap-2 hover:border-white/50 hover:bg-white/5 transition-all group"
                   >
                       <span className="text-[var(--color-cyan)] group-hover:text-white transition-colors">{chip.icon}</span>
                       <span className="font-bold text-sm tracking-wide">{chip.label}</span>
                   </button>
               ))}
           </div>
        </section>

        {/* Gallery Grid (Universal Cards) */}
        <section className="max-w-6xl mx-auto">
             <div className="flex items-center gap-3 mb-8">
                 <Film className="w-8 h-8 text-[var(--color-purple)]" />
                 <h2 className="text-3xl font-bold">Your Gallery</h2>
             </div>

             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                 <AnimatePresence>
                     {projects.map((project, index) => (
                         <motion.div
                            key={project.id}
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: index * 0.05 }}
                            className="universal-card group flex flex-col h-full min-h-[300px]"
                         >
                             {/* Video/Preview Area */}
                             <div className="flex-1 bg-black rounded-xl mb-4 relative overflow-hidden border-2 border-white/5">
                                 {project.status === 'completed' && project.video_url ? (
                                     <video 
                                        src={project.video_url} 
                                        className="w-full h-full object-cover"
                                        controls
                                     />
                                 ) : (
                                     <div className="absolute inset-0 flex items-center justify-center">
                                         {project.status === 'processing' || project.status === 'pending' ? (
                                             <div className="flex flex-col items-center gap-4">
                                                 <AICore status="processing" />
                                                 <span className="font-bold animate-pulse text-[var(--color-cyan)]">GENERATING...</span>
                                             </div>
                                         ) : (
                                             <span className="text-xl font-bold text-gray-600">PREVIEW</span>
                                         )}
                                     </div>
                                 )}
                             </div>
                             
                             {/* Details */}
                             <h3 className="text-xl font-bold leading-tight mb-2 line-clamp-2">{project.prompt}</h3>
                             <div className="flex justify-between items-center mt-auto">
                                 <span className="text-sm font-bold text-gray-400 uppercase">{project.status}</span>
                                 {project.status === 'completed' && (
                                     <button className="jelly-button w-10 h-10 bg-white rounded-full flex items-center justify-center text-black">
                                         <Play className="w-4 h-4 fill-current ml-0.5" />
                                     </button>
                                 )}
                             </div>
                         </motion.div>
                     ))}
                 </AnimatePresence>
                 
                 {/* Empty State visual */}
                 {projects.length === 0 && (
                     <div className="col-span-full py-20 text-center border-4 border-dashed border-white/10 rounded-3xl">
                         <div className="w-20 h-20 bg-[#1A1A2E] rounded-full flex items-center justify-center mx-auto mb-6">
                             <Sparkles className="w-10 h-10 text-gray-400" />
                         </div>
                         <h3 className="text-2xl font-bold text-gray-400">No creations yet</h3>
                         <p className="text-lg text-gray-600 mt-2">Use the Mega-Mic to start!</p>
                     </div>
                 )}
             </div>
        </section>

      </main>
    </div>
  );
}
