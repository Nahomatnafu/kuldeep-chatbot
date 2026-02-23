// Chat bubble components for AI Assistant and User messages
// Matches Figma design:
//   AI bubble: white card with rounded corners, robot avatar on left, dark text
//   User bubble: light gray pill/rounded rectangle, right-aligned, no avatar

// Import and re-export Message from the shared types file.
import type { Message } from "@/lib/types";
export type { Message };

// ─── AI Assistant Bubble ────────────────────────────────────────────────────

export function AssistantBubble({ content }: { content: string }) {
  return (
    <div className="flex items-start gap-3 w-full">
      {/* Avatar */}
      <div
        className="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-full"
        style={{ background: "linear-gradient(135deg, #a855f7 0%, #3b82f6 100%)" }}
      >
        <BotIcon className="w-5 h-5 text-white" />
      </div>

      {/* Bubble */}
      <div
        className="rounded-2xl rounded-tl-sm bg-white px-5 py-4 shadow-sm max-w-[75%]"
        style={{ border: "1px solid #e5e7eb" }}
      >
        <p className="text-[#2d3748] text-sm leading-relaxed whitespace-pre-wrap">
          {content}
        </p>
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

export function ChatBubble({ message }: { message: Message }) {
  if (message.role === "assistant") {
    return <AssistantBubble content={message.content} />;
  }
  return <UserBubble content={message.content} />;
}

// ─── Shared icon ─────────────────────────────────────────────────────────────

function BotIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
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
