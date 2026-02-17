import { MediaPlayer, MediaProvider } from '@vidstack/react';
import { DefaultVideoLayout, defaultLayoutIcons } from '@vidstack/react/player/layouts/default';
import '@vidstack/react/player/styles/default/theme.css';
import '@vidstack/react/player/styles/default/layouts/video.css';

interface CinematicPlayerProps {
  videoUrl: string;
  thumbnail?: string;
}

export function CinematicPlayer({ videoUrl, thumbnail }: CinematicPlayerProps) {
  return (
    <div className="group relative mx-auto w-full max-w-3xl rounded-3xl border-2 border-zinc-800 bg-zinc-900 shadow-xl transition-all duration-300 hover:border-indigo-500/50">

      {/* 1. Ambient Background Glow (The "Holographic" feel) */}
      <div className="absolute -top-24 left-1/2 -z-10 h-72 w-72 -translate-x-1/2 rounded-full bg-cyan-500/10 blur-[100px] transition-opacity duration-1000 group-hover:opacity-70" />

      {/* 2. Vidstack Player Instance */}
      <MediaPlayer
        title="AI Visual Proof"
        src={videoUrl}
        viewType="video"
        streamType="on-demand"
        logLevel="warn"
        crossOrigin
        playsInline
        className="overflow-hidden rounded-3xl"
      >
        <MediaProvider>
          {/* Optional: Add a custom poster overlay if needed */}
          {thumbnail && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/50 opacity-0 transition-opacity duration-500 data-visible:opacity-100">
              <img src={thumbnail} alt="Preview" className="h-full w-full object-cover opacity-50" />
            </div>
          )}
        </MediaProvider>

        {/* 3. The "Skin" - Customizing the Default Layout */}
        <DefaultVideoLayout
          icons={defaultLayoutIcons}
          colorScheme="dark"
          style={{
            // Brand Color Overrides (Playful Theme)
            '--video-brand': '#6366f1', // Indigo-500
            '--video-controls-color': '#e4e4e7', // Zinc-200
            '--video-slider-track-color': 'rgba(255, 255, 255, 0.1)',
            '--video-slider-track-fill-bg': '#6366f1',
            '--video-slider-thumb-bg': 'white',
          } as React.CSSProperties}
        />
      </MediaPlayer>

      {/* 4. "Metadata" Floating Bar (Under the video, inside the glass container) */}
      <div className="flex items-center justify-between border-t border-white/5 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
          <span className="font-sans text-[11px] font-bold uppercase tracking-wider text-zinc-500">
            Concept Visualization
          </span>
        </div>
        <button className="text-[10px] font-medium uppercase tracking-wider text-zinc-500 transition-colors hover:text-white">
          Save to Library
        </button>
      </div>

    </div>
  );
}