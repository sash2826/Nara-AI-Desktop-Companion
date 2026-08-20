import { Paperclip } from "lucide-react";
import { cn } from "@/lib/utils";

interface AttachmentButtonProps {
  className?: string;
}

export function AttachmentButton({ className }: AttachmentButtonProps) {
  return (
    <button
      type="button"
      aria-label="Attach file (coming soon)"
      title="Attach file (coming soon)"
      disabled
      className={cn(
        "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full transition-colors duration-fast",
        "text-muted-foreground/50 cursor-not-allowed",
        className
      )}
    >
      <Paperclip size={15} strokeWidth={1.8} aria-hidden="true" />
    </button>
  );
}
