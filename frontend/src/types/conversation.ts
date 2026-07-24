export type MessageRole = "user" | "assistant" | "system";

export type MessageStatus = "sending" | "streaming" | "complete" | "error";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  status: MessageStatus;
}

export interface ConversationState {
  messages: Message[];
  isTyping: boolean;
  isStreaming: boolean;
  streamingMessageId: string | null;
  inputValue: string;
  characterCount: number;
}

export const MAX_INPUT_CHARACTERS = 4000;
