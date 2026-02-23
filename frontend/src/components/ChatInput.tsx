"use client";

import { useState, useRef, KeyboardEvent } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  };

  return (
    <div
      className="flex items-center gap-3 bg-white rounded-2xl px-4 py-3"
      style={{
        boxShadow: "0 4px 24px 0 rgba(0,0,0,0.10)",
        border: "1px solid #e5e7eb",
      }}
    >
      {/* Attachment icon */}
      <button
        className="shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
        aria-label="Attach file"
        type="button"
      >
        <PaperclipIcon className="w-5 h-5" />
      </button>

      {/* Text input */}
      <textarea
        ref={textareaRef}
        rows={1}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        placeholder="Ask Kuldeep about manuals, SOPs, or processes..."
        disabled={disabled}
        className="flex-1 resize-none bg-transparent text-[#374151] placeholder-gray-400 text-sm leading-relaxed focus:outline-none"
        style={{ minHeight: "24px", maxHeight: "160px" }}
      />

      {/* Mic icon */}
      <button
        className="shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
        aria-label="Voice input"
        type="button"
      >
        <MicIcon className="w-5 h-5" />
      </button>

      {/* Send button */}
      <button
        onClick={handleSend}
        disabled={!value.trim() || disabled}
        className="shrink-0 flex items-center justify-center w-8 h-8 rounded-full transition-opacity"
        style={{ backgroundColor: "#3B82F6" }}
        aria-label="Send message"
        type="button"
      >
        <SendIcon className="w-4 h-4 text-white" />
      </button>
    </div>
  );
}

// ─── Icons ────────────────────────────────────────────────────────────────────

function PaperclipIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  );
}

function MicIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );
}

function SendIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M22 2L11 13" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
      <path d="M22 2L15 22L11 13L2 9L22 2Z" fill="white"/>
    </svg>
  );
}
