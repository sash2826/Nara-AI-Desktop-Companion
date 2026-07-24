import { MessageSquare } from "lucide-react";
import { PlaceholderPage } from "@/components/common/PlaceholderPage";

export function ChatPage() {
  return (
    <PlaceholderPage
      title="Chat"
      description="Conversations with your AI companion will appear here."
      icon={MessageSquare}
    />
  );
}
