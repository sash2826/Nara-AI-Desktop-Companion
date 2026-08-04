export type MessageRole = "user" | "assistant" | "system";

export type MessageStatus = "sending" | "streaming" | "complete" | "error" | "cancelled";

/** Metadata for one retrieved chunk that was used to ground an assistant response. */
export interface CitationMeta {
  chunkId: string;
  documentPath: string;
  chunkIndex: number;
  /** Normalised RRF score from hybrid search (0–1 range after normalisation). */
  rrfScore: number;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  status: MessageStatus;
  /** Retrieved chunks that grounded this response. Present on assistant messages only. */
  citations?: CitationMeta[] | null;
  /** Running token count during streaming; final count once complete. */
  tokenCount?: number;
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
