// Chat bubble components for AI Assistant and User messages
// Matches Figma design:
//   AI bubble: white card with rounded corners, robot avatar on left, dark text
//   User bubble: light gray pill/rounded rectangle, right-aligned, no avatar

"use client";

import { useState } from "react";
import type { Message, Source, Clarification } from "@/lib/types";

// ─── AI Assistant Bubble ────────────────────────────────────────────────────

export function AssistantBubble({
  content,
  sources,
  clarification,
  onOptionSelect,
}: {
  content: string;
  sources?: Source[];
  clarification?: Clarification;
  onOptionSelect?: (label: string) => void;
}) {
  const [showSources, setShowSources] = useState(false);
  const hasSources = sources && sources.length > 0;

  return (
    <div className="flex items-start gap-3 w-full">
      {/* Avatar */}
      <div
        className="shrink-0 flex items-center justify-center w-9 h-9 rounded-full"
        style={{ background: "linear-gradient(135deg, #a855f7 0%, #3b82f6 100%)" }}
      >
        <BotIcon className="w-5 h-5 text-white" />
      </div>

      {/* Bubble + sources */}
      <div className="flex flex-col gap-2 max-w-[75%]">
        <div
          className="rounded-2xl rounded-tl-sm bg-white px-5 py-4 shadow-sm"
          style={{ border: "1px solid #e5e7eb" }}
        >
          <p className="text-[#2d3748] text-sm leading-relaxed whitespace-pre-wrap">
            {content}
          </p>
          {clarification && onOptionSelect && (
            <div className="mt-3 flex flex-wrap gap-2">
              {clarification.options.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => onOptionSelect(opt.label)}
                  className="rounded-full border border-purple-300 px-3 py-1.5 text-xs text-purple-700 hover:bg-purple-50 transition-colors"
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Source toggle */}
        {hasSources && (
          <div>
            <button
              onClick={() => setShowSources((v) => !v)}
              className="flex items-center gap-1.5 text-xs text-[#6b7280] hover:text-[#374151] transition-colors"
            >
              <BookIcon className="w-3.5 h-3.5" />
              {showSources ? "Hide" : "Show"} {sources.length} source
              {sources.length !== 1 ? "s" : ""}
              <ChevronIcon
                className={`w-3 h-3 transition-transform ${showSources ? "rotate-180" : ""}`}
              />
            </button>

            {showSources && (
              <div className="mt-2 flex flex-col gap-1.5">
                {sources.map((src) => (
                  <div
                    key={src.id}
                    className="rounded-lg bg-white px-3 py-2 text-xs shadow-sm"
                    style={{ border: "1px solid #e5e7eb" }}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      {/* File name */}
                      <span className="font-medium text-[#374151] truncate max-w-45">
                        {src.file}
                      </span>
                      {/* Page badge */}
                      <span
                        className="shrink-0 rounded-full px-2 py-0.5 text-white text-[10px] font-semibold"
                        style={{ background: "linear-gradient(135deg, #a855f7 0%, #3b82f6 100%)" }}
                      >
                        p.{src.page}
                      </span>
                    </div>
                    <p className="text-[#6b7280] leading-snug line-clamp-2">{src.snippet}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── User Bubble ─────────────────────────────────────────────────────────────

export function UserBubble({ content }: { content: string }) {
  return (
    <div className="flex justify-end w-full">
      <div
        className="rounded-2xl rounded-tr-sm px-5 py-3 max-w-[75%]"
        style={{ backgroundColor: "#e5e7eb" }}
      >
        <p className="text-[#374151] text-sm leading-relaxed">
          {content}
        </p>
      </div>
    </div>
  );
}

// ─── Generic ChatBubble dispatcher ──────────────────────────────────────────

export function ChatBubble({ message, onOptionSelect }: { message: Message; onOptionSelect?: (label: string) => void }) {
  if (message.role === "assistant") {
    return <AssistantBubble content={message.content} sources={message.sources} clarification={message.clarification} onOptionSelect={onOptionSelect} />;
  }
  return <UserBubble content={message.content} />;
}

// ─── Icons ───────────────────────────────────────────────────────────────────

function BotIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <rect x="11" y="1" width="2" height="3" rx="1" />
      <circle cx="12" cy="1.5" r="1.5" />
      <rect x="4" y="4" width="16" height="12" rx="3" />
      <circle cx="9" cy="9" r="1.5" opacity="0.35" />
      <circle cx="15" cy="9" r="1.5" opacity="0.35" />
      <circle cx="9" cy="9" r="0.75" fill="white" />
      <circle cx="15" cy="9" r="0.75" fill="white" />
      <rect x="8" y="12" width="8" height="1.5" rx="0.75" fill="white" opacity="0.7" />
      <rect x="7" y="16" width="10" height="6" rx="2" />
      <rect x="2" y="17" width="4" height="4" rx="2" />
      <rect x="18" y="17" width="4" height="4" rx="2" />
    </svg>
  );
}

function BookIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  );
}

function ChevronIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}
