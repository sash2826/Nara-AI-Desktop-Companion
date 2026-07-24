import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AssistantHeader } from "./AssistantHeader";
import { ConversationView } from "./ConversationView";
import { AssistantFooter } from "./AssistantFooter";
import { useConversation } from "@/hooks/useConversation";
import { cn } from "@/lib/utils";

interface AssistantWidgetProps {
  className?: string;
}

export function AssistantWidget({ className }: AssistantWidgetProps) {
  const { messages, isTyping, isStreaming, inputValue, setInputValue, clearMessages, sendMessage } =
    useConversation();

  const [isDragOver, setIsDragOver] = useState(false);

  const handleSend = useCallback(() => {
    void sendMessage(inputValue);
  }, [sendMessage, inputValue]);

  // Drag-and-drop placeholder handlers — no file processing implemented.
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    // File handling will be wired to the File Intelligence capability in a future phase.
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn("relative flex h-full flex-col overflow-hidden bg-background", className)}
      role="main"
      aria-label="AI Assistant"
    >
      <AssistantHeader
        isTyping={isTyping}
        isStreaming={isStreaming}
        onClearConversation={clearMessages}
      />

      <ConversationView messages={messages} isTyping={isTyping} />

      <AssistantFooter
        inputValue={inputValue}
        isStreaming={isStreaming}
        isTyping={isTyping}
        onInputChange={setInputValue}
        onSend={handleSend}
      />

      {/* Drag-and-drop overlay */}
      <AnimatePresence>
        {isDragOver && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.12 }}
            className={cn(
              "absolute inset-0 z-modal flex flex-col items-center justify-center gap-3",
              "surface-glass pointer-events-none"
            )}
            aria-hidden="true"
          >
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <span className="text-2xl">📎</span>
            </div>
            <p className="text-sm font-medium text-foreground">Drop files to attach</p>
            <p className="text-xs text-muted-foreground">File processing coming in Phase 01</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
