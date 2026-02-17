"use client";

import React from "react";
import { Sidebar } from "./Sidebar";
import { PDFSidebar } from "./PDFSidebar";
import { Button } from "@/components/ui/button";
import { FileText } from "lucide-react";

interface ChatLayoutProps {
  children: React.ReactNode;
  chatInput?: React.ReactNode;
  onNewChat?: () => void;
  onSelectChat?: (chatId: string) => void;
  onChatCreated?: (chatId: string) => void;
  activeChatId?: string | null;
  sidebarRefresh?: number;
}

export function ChatLayout({ children, chatInput, onNewChat, onSelectChat, onChatCreated, activeChatId, sidebarRefresh }: ChatLayoutProps) {
  const [showLeftSidebar, setShowLeftSidebar] = React.useState(true);
  const [showRightSidebar, setShowRightSidebar] = React.useState(false);

  const toggleRightSidebar = () => {
    if (!showRightSidebar) {
      // Opening right sidebar -> Close left
      setShowRightSidebar(true);
      setShowLeftSidebar(false);
    } else {
      // Closing right sidebar -> Open left (optional, or keep it closed)
      setShowRightSidebar(false);
      setShowLeftSidebar(true);
    }
  };

  return (
    <div className="relative h-screen w-full bg-zinc-950 overflow-hidden flex font-sans tracking-wide">
      {/* Background - Matte Dot Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#ffffff33_1px,transparent_1px)] bg-[length:24px_24px] pointer-events-none opacity-[0.1]" />

      {/* Left Sidebar */}
      {showLeftSidebar && (
        <Sidebar
          className="shrink-0"
          onNewChat={onNewChat}
          onSelectChat={onSelectChat}
          activeChatId={activeChatId}
          refreshTrigger={sidebarRefresh}
        />
      )}

      {/* Main Content Area */}
      <div className="relative z-10 flex-1 flex flex-col h-full overflow-hidden transition-all duration-300">

        {/* Helper Toggle for PDF (Temporary Placement) */}
        {!showRightSidebar && (
          <div className="absolute top-4 right-4 z-50">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleRightSidebar}
              className="text-zinc-500 hover:text-white hover:bg-zinc-800/50 gap-2"
            >
              <FileText className="w-4 h-4" />
              <span>View PDF</span>
            </Button>
          </div>
        )}

        {/* Scrollable Area */}
        <div
          data-chat-scroll-container
          className="flex-1 min-h-0 w-full overflow-y-auto"
        >
          <div className="p-4 md:p-8 space-y-6 pb-40 max-w-4xl mx-auto w-full">
            {children}
          </div>
        </div>

        {/* Chat Input Area */}
        {chatInput && (
          <div className="absolute bottom-0 left-0 right-0 z-50">
            {chatInput}
          </div>
        )}
      </div>

      {/* Right Sidebar */}
      <PDFSidebar 
        isOpen={showRightSidebar} 
        onClose={toggleRightSidebar} 
        activeChatId={activeChatId ?? null}
        onChatCreated={onChatCreated}
      />
    </div>
  );
}
