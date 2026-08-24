import { useCallback } from "react";
import { motion } from "framer-motion";
import { ConversationView } from "./ConversationView";
import { AssistantFooter } from "./AssistantFooter";
import { useConversation } from "@/hooks/useConversation";
import { useDashboard } from "@/hooks/useDashboard";
import { cn } from "@/lib/utils";

interface AssistantWidgetProps {
  className?: string;
}

export function AssistantWidget({ className }: AssistantWidgetProps) {
  const {
    messages,
    isTyping,
    isStreaming,
    inputValue,
    setInputValue,
    cancelStream,
    clearMessages,
    sendMessage,
  } = useConversation();

  const { suggestions, reshuffleSuggestions } = useDashboard();

  const handleSend = useCallback(() => {
    void sendMessage(inputValue);
  }, [sendMessage, inputValue]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={cn("relative flex h-full flex-col overflow-hidden bg-background", className)}
      role="main"
      aria-label="AI Assistant"
    >
      <ConversationView messages={messages} isTyping={isTyping} onQuickPrompt={setInputValue} />

      <AssistantFooter
        inputValue={inputValue}
        isStreaming={isStreaming}
        isTyping={isTyping}
        onInputChange={setInputValue}
        onSend={handleSend}
        onStop={cancelStream}
        onClear={clearMessages}
        hasMessages={messages.length > 0}
        suggestions={suggestions}
        onReshuffle={reshuffleSuggestions}
      />
    </motion.div>
  );
}
