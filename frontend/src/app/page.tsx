"use client";

import { useState, useCallback, useRef } from "react";
import Header from "@/components/Header";
import WelcomePage from "@/components/WelcomePage";
import ChatPage from "@/components/ChatPage";
import DocumentSidebar from "@/components/DocumentSidebar";
import type { Message } from "@/lib/types";
import { sendMessage } from "@/lib/chatApi";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const sessionIdRef = useRef<string | undefined>(undefined);

  const handleSend = useCallback(async (text: string) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Snapshot history before the new user message (setMessages is async)
      const history = messages.map(({ role, content }) => ({ role, content }));

      const response = await sendMessage(text, history, sessionIdRef.current);

      // Persist session ID for stateful backends
      if (response.session_id) {
        sessionIdRef.current = response.session_id;
      }

      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: response.reply,
        timestamp: new Date().toISOString(),
        sources: response.metadata?.sources,
        clarification: response.metadata?.clarification,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error("[chat] API call failed:", err);

      const errorContent =
        err instanceof Error
          ? err.message
          : "Sorry, something went wrong. Please try again.";

      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: errorContent,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [messages]);

  const hasMessages = messages.length > 0 || isLoading;

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header onDocsClick={() => setIsSidebarOpen(true)} />

      <DocumentSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {hasMessages ? (
        <ChatPage
          messages={messages}
          onSend={handleSend}
          isLoading={isLoading}
        />
      ) : (
        <WelcomePage onSend={handleSend} />
      )}
    </div>
  );
}
