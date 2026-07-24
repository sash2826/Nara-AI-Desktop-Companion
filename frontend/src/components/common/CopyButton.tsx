import { useState, useCallback } from "react";
import { Check, Copy } from "lucide-react";
import { cn } from "@/lib/utils";

interface CopyButtonProps {
  text: string;
  className?: string;
}

export function CopyButton({ text, className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // Clipboard API unavailable — silently ignore
    }
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      aria-label={copied ? "Copied" : "Copy to clipboard"}
      className={cn(
        "flex h-6 w-6 items-center justify-center rounded-md transition-colors duration-fast",
        "text-muted-foreground hover:bg-muted hover:text-foreground",
        className
      )}
    >
      {copied ? (
        <Check size={12} strokeWidth={2.5} className="text-success" />
      ) : (
        <Copy size={12} strokeWidth={2} />
      )}
    </button>
  );
}
