import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import { AssistantAvatar } from "./AssistantAvatar";
import { CopyButton } from "@/components/common/CopyButton";
import { cn } from "@/lib/utils";
import type { Message } from "@/types/conversation";

interface MessageBubbleProps {
  message: Message;
}

// Custom renderers for react-markdown — defined outside the component
// to avoid re-creating on every render.
const MARKDOWN_COMPONENTS: Components = {
  code({ className, children, ...props }) {
    const isInline = !className;
    const language = className?.replace("language-", "") ?? "";
    const code = String(children).replace(/\n$/, "");

    if (isInline) {
      return (
        <code
          className="rounded-sm bg-muted px-1 py-0.5 font-mono text-xs text-foreground"
          {...props}
        >
          {children}
        </code>
      );
    }

    return (
      <div className="group relative my-2 overflow-hidden rounded-lg border border-border bg-muted">
        {language && (
          <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
            <span className="font-mono text-2xs text-muted-foreground">{language}</span>
            <CopyButton text={code} />
          </div>
        )}
        {!language && (
          <div className="absolute right-2 top-2 opacity-0 transition-opacity duration-fast group-hover:opacity-100">
            <CopyButton text={code} />
          </div>
        )}
        <pre className="overflow-x-auto p-3 text-xs">
          <code className="font-mono text-foreground">{children}</code>
        </pre>
      </div>
    );
  },

  table({ children }) {
    return (
      <div className="my-2 overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">{children}</table>
      </div>
    );
  },

  th({ children }) {
    return (
      <th className="border-b border-border bg-muted px-3 py-2 text-left text-xs font-semibold text-foreground">
        {children}
      </th>
    );
  },

  td({ children }) {
    return <td className="border-b border-border px-3 py-2 text-xs text-foreground">{children}</td>;
  },

  blockquote({ children }) {
    return (
      <blockquote className="my-2 border-l-2 border-primary pl-3 text-muted-foreground">
        {children}
      </blockquote>
    );
  },

  p({ children }) {
    return <p className="mb-2 last:mb-0 text-sm leading-relaxed">{children}</p>;
  },

  ul({ children }) {
    return <ul className="mb-2 ml-4 list-disc space-y-1 text-sm">{children}</ul>;
  },

  ol({ children }) {
    return <ol className="mb-2 ml-4 list-decimal space-y-1 text-sm">{children}</ol>;
  },

  li({ children }) {
    return <li className="leading-relaxed">{children}</li>;
  },

  h1({ children }) {
    return <h1 className="mb-2 text-lg font-bold text-foreground">{children}</h1>;
  },

  h2({ children }) {
    return <h2 className="mb-2 text-base font-semibold text-foreground">{children}</h2>;
  },

  h3({ children }) {
    return <h3 className="mb-1.5 text-sm font-semibold text-foreground">{children}</h3>;
  },

  strong({ children }) {
    return <strong className="font-semibold text-foreground">{children}</strong>;
  },
};

function UserBubble({ message }: { message: Message }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="flex justify-end px-4 py-1"
    >
      <div className="group flex max-w-[80%] flex-col items-end gap-1">
        <div className="rounded-2xl rounded-br-sm bg-primary px-3.5 py-2.5 text-sm text-primary-foreground">
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
        </div>
        <div className="flex items-center gap-2 opacity-0 transition-opacity duration-fast group-hover:opacity-100">
          <CopyButton text={message.content} />
          <span className="text-2xs text-muted-foreground">{formatTime(message.timestamp)}</span>
        </div>
      </div>
    </motion.div>
  );
}

function AssistantBubble({ message }: { message: Message }) {
  const isStreaming = message.status === "streaming";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="flex items-start gap-2.5 px-4 py-1"
    >
      <AssistantAvatar size="sm" className="mt-1" />

      <div className="group flex min-w-0 flex-1 flex-col gap-1">
        <div
          className={cn(
            "min-w-0 rounded-2xl rounded-tl-sm bg-muted px-3.5 py-2.5",
            "prose prose-sm max-w-none"
          )}
        >
          {message.content ? (
            <>
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={MARKDOWN_COMPONENTS}>
                {message.content}
              </ReactMarkdown>
              {/* Streaming cursor */}
              {isStreaming && (
                <motion.span
                  className="inline-block h-3.5 w-0.5 rounded-full bg-foreground align-middle"
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, ease: "easeInOut" }}
                  aria-hidden="true"
                />
              )}
            </>
          ) : (
            <span className="text-sm text-muted-foreground">…</span>
          )}
        </div>

        {!isStreaming && message.content && (
          <div className="flex items-center gap-2 opacity-0 transition-opacity duration-fast group-hover:opacity-100">
            <CopyButton text={message.content} />
            <span className="text-2xs text-muted-foreground">{formatTime(message.timestamp)}</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function SystemBubble({ message }: { message: Message }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="flex justify-center px-4 py-2"
      role="status"
      aria-live="polite"
    >
      <span className="rounded-full bg-muted px-3 py-1 text-2xs text-muted-foreground">
        {message.content}
      </span>
    </motion.div>
  );
}

export function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === "user") return <UserBubble message={message} />;
  if (message.role === "system") return <SystemBubble message={message} />;
  return <AssistantBubble message={message} />;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
