import { useCallback, useState } from "react";
import { Paperclip } from "lucide-react";
import { open } from "@tauri-apps/plugin-dialog";
import { cn } from "@/lib/utils";
import { IPCClient } from "@/services/ipc/IPCClient";
import { useConversationStore } from "@/store/conversationStore";

interface AttachmentButtonProps {
  className?: string;
  disabled?: boolean;
}

export function AttachmentButton({ className, disabled }: AttachmentButtonProps) {
  const [isPending, setIsPending] = useState(false);
  const addMessage = useConversationStore((s) => s.addMessage);

  const handleClick = useCallback(async () => {
    if (isPending) return;

    try {
      setIsPending(true);
      const selected = await open({
        directory: true,
        multiple: false,
        title: "Add folder to index",
      });
      if (!selected) return; // User cancelled the picker.

      const folderPath = typeof selected === "string" ? selected : selected[0];
      if (!folderPath) return;

      await IPCClient.addWatchedFolder(folderPath);
      addMessage(
        "assistant",
        `Got it! I've added **${folderPath}** to the index and will start processing the files in the background — they'll be searchable shortly.`,
        "complete"
      );
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      addMessage(
        "assistant",
        `Sorry, I couldn't add that folder to the index: ${errMsg}`,
        "complete"
      );
      console.warn("[AttachmentButton] folder indexing failed:", err);
    } finally {
      setIsPending(false);
    }
  }, [isPending, addMessage]);

  return (
    <button
      type="button"
      aria-label="Add folder to index"
      title="Add folder to index"
      disabled={disabled || isPending}
      onClick={() => void handleClick()}
      className={cn(
        "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full transition-colors duration-fast",
        disabled || isPending
          ? "cursor-not-allowed text-muted-foreground/50"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
        className
      )}
    >
      <Paperclip size={15} strokeWidth={1.8} aria-hidden="true" />
    </button>
  );
}
