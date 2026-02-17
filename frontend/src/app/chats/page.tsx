"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { ChatLayout } from "@/components/chat/ChatLayout";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { CinematicPlayer } from "@/components/chat/CinematicPlayer";
import { VivaInput } from "@/components/chat/VivaInput";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AnimatePresence } from "framer-motion";
import {
  sendChatMessage,
  getChatMessages,
  getVideoStatus,
  setAuthTokenGetter,
  type ChatMessage as APIChatMessage,
  type SendMessageResponse,
} from "@/lib/api";
import { ModeSelector } from "@/components/chat/ModeSelector";

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface DisplayMessage {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: string;
  type: "text" | "video" | "video_pending";
  videoUrl?: string;
  projectId?: string; // For polling video status
}

/** Convert API message to display messages (one user + one AI response) */
function apiMessageToDisplay(msg: APIChatMessage): DisplayMessage[] {
  const time = new Date(msg.created_at).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  const messages: DisplayMessage[] = [];

  // User message
  messages.push({
    id: `${msg.id}-user`,
    role: "user",
    content: msg.user_message,
    timestamp: time,
    type: "text",
  });

  // AI response
  if (msg.routed_to === "video_generation") {
    if (msg.video_url) {
      // Video is ready
      messages.push({
        id: `${msg.id}-ai`,
        role: "ai",
        content: msg.system_response || "Here's your visualization!",
        timestamp: time,
        type: "video",
        videoUrl: msg.video_url,
      });
    } else {
      // Video still generating
      messages.push({
        id: `${msg.id}-ai`,
        role: "ai",
        content: msg.system_response || "🎬 Generating your visualization...",
        timestamp: time,
        type: "video_pending",
      });
    }
  } else {
    // Text response
    if (msg.system_response) {
      messages.push({
        id: `${msg.id}-ai`,
        role: "ai",
        content: msg.system_response,
        timestamp: time,
        type: "text",
      });
    }
  }

  return messages;
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export default function SocraticChatPage() {
  const { getToken, isSignedIn, isLoaded } = useAuth();
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [sidebarRefresh, setSidebarRefresh] = useState(0);
  const [pendingVideos, setPendingVideos] = useState<Map<string, string>>(new Map()); // projectId -> messageId
  const [authReady, setAuthReady] = useState(false);
  const [activeMode, setActiveMode] = useState<string>("socratic");
  const scrollRef = useRef<HTMLDivElement>(null);
  const pendingVideosRef = useRef<Map<string, string>>(new Map()); // Stable ref to avoid effect re-runs

  // ── Inject Clerk auth token into API layer ───────────────────────────
  useEffect(() => {
    if (isSignedIn) {
      setAuthTokenGetter(async () => {
        const token = await getToken();
        return token;
      });
      console.log("[🔐 Auth] ✅ Token getter injected — API calls will be authenticated");
      setAuthReady(true);
      // Trigger sidebar to fetch now that auth is ready
      setSidebarRefresh((n) => n + 1);
    }
  }, [isSignedIn, getToken]);

  // ── Lock body scroll so scrollIntoView can't push the page ─────────
  useEffect(() => {
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';
    return () => {
      document.documentElement.style.overflow = '';
      document.body.style.overflow = '';
    };
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      const container = scrollRef.current.closest('[data-chat-scroll-container]');
      if (container) {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
      }
    }
  }, [messages, isTyping]);

  // ── Poll for pending video completions ───────────────────────────────
  // Uses useRef to avoid re-running effect when pendingVideos changes
  useEffect(() => {
    // Keep ref in sync with state
    pendingVideosRef.current = new Map(pendingVideos);

    // If no pending videos, don't start polling
    if (pendingVideos.size === 0) {
      console.log(`[💬 Chat] 🛑 No pending videos, stopping poll`);
      return;
    }

    console.log(`[💬 Chat] 🔄 Starting video polling for ${pendingVideos.size} video(s)`);

    const interval = setInterval(async () => {
      // Use ref to get current pending videos without re-running effect
      const currentPending = new Map(pendingVideosRef.current);
      
      if (currentPending.size === 0) {
        console.log(`[💬 Chat] 🛑 No more pending videos, stopping poll`);
        return;
      }

      for (const [projectId, messageId] of currentPending) {
        try {
          console.log(`[💬 Chat] 🔍 Polling video status for project: ${projectId}`);
          const status = await getVideoStatus(projectId);
          console.log(`[💬 Chat] ✅ Poll response: ${status.status}`);

          if (status.status === "completed" && status.video_url) {
            console.log(`[💬 Chat] 🎉 Video completed! URL: ${status.video_url}`);
            // Video is ready — update the message
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === messageId
                  ? {
                      ...msg,
                      type: "video" as const,
                      videoUrl: status.video_url!,
                      content: "Here's your visualization!",
                    }
                  : msg
              )
            );
            // Update both state and ref
            setPendingVideos((prev) => {
              const next = new Map(prev);
              next.delete(projectId);
              return next;
            });
            pendingVideosRef.current.delete(projectId);
          } else if (status.status === "failed") {
            console.log(`[💬 Chat] ❌ Video generation failed: ${status.error}`);
            // Failed — update message with error
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === messageId
                  ? {
                      ...msg,
                      type: "text" as const,
                      content: `Video generation failed: ${status.error || "Unknown error"}. Please try again.`,
                    }
                  : msg
              )
            );
            // Update both state and ref
            setPendingVideos((prev) => {
              const next = new Map(prev);
              next.delete(projectId);
              return next;
            });
            pendingVideosRef.current.delete(projectId);
          }
        } catch (err) {
          console.error("❌ [💬 Chat] Poll error:", err);
        }
      }
    }, 5000); // Poll every 5 seconds

    return () => {
      console.log(`[💬 Chat] 🧹 Clearing poll interval`);
      clearInterval(interval);
    };
  }, [pendingVideos]);

  // ── Load chat messages when switching chats ──────────────────────────
  const loadChat = useCallback(async (chatId: string) => {
    setActiveChatId(chatId);
    setMessages([]);
    setIsTyping(false);
    pendingVideosRef.current = new Map();
    setPendingVideos(new Map());

    try {
      const apiMessages = await getChatMessages(chatId);
      const display: DisplayMessage[] = [];
      for (const msg of apiMessages) {
        display.push(...apiMessageToDisplay(msg));
      }
      setMessages(display);
    } catch (err) {
      console.error("Failed to load chat:", err);
    }
  }, []);

  // ── Send message ─────────────────────────────────────────────────────
  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    console.log(`\n${'═'.repeat(60)}`);
    console.log(`[💬 Chat] User sending message: "${content.substring(0, 80)}${content.length > 80 ? '...' : ''}"`);
    console.log(`[💬 Chat] Chat ID: ${activeChatId || 'NEW'}`);

    const timestamp = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    // 1. Immediately show user message
    console.log(`[💬 Chat] 📝 Adding user message to UI...`);
    const userMsgId = `temp-${Date.now()}`;
    const userMsg: DisplayMessage = {
      id: userMsgId,
      role: "user",
      content,
      timestamp,
      type: "text",
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    console.log(`[💬 Chat] ✅ User message displayed (ID: ${userMsgId})`);

    try {
      // 2. Send to backend (classifier + response generation)
      console.log(`[💬 Chat] 📤 Sending to backend (mode: ${activeMode})...`);
      const sendStartTime = performance.now();
      const response: SendMessageResponse = await sendChatMessage(
        content,
        activeChatId || undefined,
        activeMode
      );
      const sendDuration = (performance.now() - sendStartTime).toFixed(2);
      console.log(`[💬 Chat] ✅ Backend response received in ${sendDuration}ms`);
      console.log(`[💬 Chat]   Status: ${response.status}`);
      console.log(`[💬 Chat]   Chat ID: ${response.chat_id}`);
      console.log(`[💬 Chat]   Is New Chat: ${response.is_new_chat}`);
      console.log(`[💬 Chat]   Routed to: ${response.message.routed_to}`);
      console.log(`[💬 Chat]   Classification: ${response.message.classification.category}`);

      // If this created a new chat, update state
      if (response.is_new_chat) {
        console.log(`[💬 Chat] 🆕 New chat created, updating sidebar...`);
        setActiveChatId(response.chat_id);
        setSidebarRefresh((n) => n + 1); // Refresh sidebar
      }

      // 3. Process response based on status
      const aiTime = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      if (response.status === "video_generating") {
        console.log(`[💬 Chat] 🎬 Video pipeline activated`);
        console.log(`[💬 Chat]   Project ID: ${response.project_id}`);
        // Video is being generated in background
        const aiMsgId = `${response.message.id}-ai`;
        const aiMsg: DisplayMessage = {
          id: aiMsgId,
          role: "ai",
          content: "🎬 Generating your visualization... This may take 2-4 minutes. I'll update when it's ready!",
          timestamp: aiTime,
          type: "video_pending",
          projectId: response.project_id,
        };
        console.log(`[💬 Chat] ⏳ Showing pending video message...`);
        setMessages((prev) => [...prev, aiMsg]);

        // Start polling for video completion
        if (response.project_id) {
          console.log(`[💬 Chat] 🔄 Starting video polling...`);
          const newPending = new Map(pendingVideosRef.current).set(response.project_id!, aiMsgId);
          pendingVideosRef.current = newPending;
          setPendingVideos(newPending);
        }
      } else {
        console.log(`[💬 Chat] 💬 Text pipeline returned response`);
        // Text response — show immediately
        const aiMsg: DisplayMessage = {
          id: `${response.message.id}-ai`,
          role: "ai",
          content: response.message.system_response || "I couldn't generate a response. Please try again.",
          timestamp: aiTime,
          type: "text",
        };
        console.log(`[💬 Chat] ✅ AI Response ready (${response.message.system_response?.length || 0} chars)`);
        setMessages((prev) => [...prev, aiMsg]);
      }

      // Update active chat ID if it wasn't set
      if (!activeChatId) {
        setActiveChatId(response.chat_id);
      }
      console.log(`${'═'.repeat(60)}\n`);
    } catch (error: any) {
      console.error(`[❌ Error] Failed to send message:`, error);
      console.error(`[❌ Error] Details:`, error.message);
      const errMsg: DisplayMessage = {
        id: `error-${Date.now()}`,
        role: "ai",
        content: `Sorry, something went wrong: ${error.message || "Please try again."}`,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        type: "text",
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  // ── New chat ─────────────────────────────────────────────────────────
  const handleNewChat = () => {
    setActiveChatId(null);
    setMessages([]);
    setIsTyping(false);
    pendingVideosRef.current = new Map();
    setPendingVideos(new Map());
  };

  // ── Select existing chat ─────────────────────────────────────────────
  const handleSelectChat = (chatId: string) => {
    loadChat(chatId);
  };

  // ── Chat created from PDF upload (auto-create) ──────────────────────
  const handleChatCreatedFromPDF = (chatId: string) => {
    console.log(`[Chat] New chat created from PDF upload: ${chatId}`);
    setActiveChatId(chatId);
    loadChat(chatId); // Load the (empty) chat messages
    setSidebarRefresh((prev) => prev + 1); // Refresh sidebar to show new chat
  };

  // Wait for Clerk auth to be ready before rendering
  if (!isLoaded || !authReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-zinc-950 text-zinc-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-zinc-600 border-t-indigo-500 rounded-full animate-spin" />
          <span className="text-sm font-mono">Initializing...</span>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider delayDuration={300}>
      <ChatLayout
        chatInput={
          <VivaInput
            onSend={handleSendMessage}
            placeholder="Ask anything..."
            disabled={isTyping}
          />
        }
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onChatCreated={handleChatCreatedFromPDF}
        activeChatId={activeChatId}
        sidebarRefresh={sidebarRefresh}
      >
        <div className="space-y-6 w-full max-w-4xl mx-auto pb-4">
          {/* Header */}
          <div className="flex flex-col items-center gap-3 mb-8">
            <div className="h-px w-32 bg-linear-to-r from-transparent via-zinc-700 to-transparent" />
            <ModeSelector activeMode={activeMode} onModeChange={setActiveMode} />
            <div className="h-px w-32 bg-linear-to-r from-transparent via-zinc-700 to-transparent" />
          </div>

          {/* Empty state */}
          {messages.length === 0 && !isTyping && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-6">
                <span className="text-2xl">🧠</span>
              </div>
              <h2 className="text-xl font-semibold text-zinc-200 mb-2">
                Start a Conversation
              </h2>
              <p className="text-sm text-zinc-500 max-w-md">
                Ask me anything about math, science, or any topic. Say{" "}
                <span className="text-indigo-400 font-medium">&quot;show me&quot;</span> or{" "}
                <span className="text-indigo-400 font-medium">&quot;visualize&quot;</span> to get
                an animated video explanation!
              </p>
            </div>
          )}

          {/* Message List */}
          {messages.map((msg) => (
            <React.Fragment key={msg.id}>
              {msg.type === "video" && msg.videoUrl ? (
                <div>
                  {msg.content && (
                    <MessageBubble
                      role="ai"
                      content={msg.content}
                      timestamp={msg.timestamp}
                    />
                  )}
                  <CinematicPlayer videoUrl={msg.videoUrl} />
                </div>
              ) : msg.type === "video_pending" ? (
                <MessageBubble
                  role="ai"
                  content={msg.content}
                  timestamp={msg.timestamp}
                />
              ) : (
                <MessageBubble
                  role={msg.role}
                  content={msg.content}
                  timestamp={msg.timestamp}
                />
              )}
            </React.Fragment>
          ))}

          {/* Typing Indicator */}
          <AnimatePresence>{isTyping && <TypingIndicator />}</AnimatePresence>

          {/* Invisible div for auto-scrolling */}
          <div ref={scrollRef} />
        </div>
      </ChatLayout>
    </TooltipProvider>
  );
}
