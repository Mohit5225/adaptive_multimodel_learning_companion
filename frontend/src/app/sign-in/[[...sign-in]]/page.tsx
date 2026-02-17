import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#050510] relative overflow-hidden">
      
      {/* 1. THE NEBULA: Large, slow-spinning gradient orb */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-gradient-to-br from-[var(--color-cyan)]/20 to-[var(--color-purple)]/20 blur-[120px] animate-spin-slow pointer-events-none opacity-60" />

      {/* 2. THE MONOLITH: Frosted Obsidian Card */}
      <div className="relative z-10 w-full max-w-3xl bg-black/40 backdrop-blur-3xl border-2 border-white/10 p-12 md:p-24 shadow-[0_0_100px_rgba(6,182,212,0.1)] rounded-3xl">
        
        {/* Header */}
        <div className="mb-16 text-center">
            <h1 className="text-5xl font-display font-bold text-white mb-4 tracking-tight">INITIALIZE SESSION</h1>
            <p className="text-gray-400 uppercase tracking-widest text-lg font-bold">Access your cognitive workspace</p>
        </div>

        <SignIn />
        
        {/* Decorative Technical Markings */}
        <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-white/30" />
        <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-white/30" />
        <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-white/30" />
        <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-white/30" />
      </div>
      
    </div>
  );
}
