import { create } from "zustand";
import type { CitationMeta, Message, MessageRole, MessageStatus } from "@/types/conversation";
import { MAX_INPUT_CHARACTERS } from "@/types/conversation";
import type { PendingToolAction } from "@/services/conversation/ConversationService";

let _messageCounter = 0;

function makeId(): string {
  _messageCounter += 1;
  return `msg-${_messageCounter}`;
}

interface ConversationStore {
  messages: Message[];
  isTyping: boolean;
  isStreaming: boolean;
  streamingMessageId: string | null;
  inputValue: string;
  pendingToolAction: PendingToolAction | null;

  addMessage: (role: MessageRole, content: string, status?: MessageStatus) => string;
  updateMessageContent: (id: string, content: string) => void;
  updateMessageStatus: (id: string, status: MessageStatus) => void;
  updateMessageCitations: (id: string, citations: CitationMeta[]) => void;
  updateMessageTokenCount: (id: string, tokenCount: number) => void;
  setTyping: (typing: boolean) => void;
  setStreaming: (streaming: boolean, messageId?: string | null) => void;
  setInputValue: (value: string) => void;
  clearInput: () => void;
  clearMessages: () => void;
  setPendingToolAction: (action: PendingToolAction | null) => void;
  clearPendingToolAction: () => void;
}

export const useConversationStore = create<ConversationStore>((set) => ({
  messages: [],
  isTyping: false,
  isStreaming: false,
  streamingMessageId: null,
  inputValue: "",
  pendingToolAction: null,

  addMessage: (role, content, status = "complete") => {
    const id = makeId();
    const message: Message = {
      id,
      role,
      content,
      timestamp: new Date(),
      status,
    };
    set((state) => ({ messages: [...state.messages, message] }));
    return id;
  },

  updateMessageContent: (id, content) =>
    set((state) => ({
      messages: state.messages.map((m) => (m.id === id ? { ...m, content } : m)),
    })),

  updateMessageStatus: (id, status) =>
    set((state) => ({
      messages: state.messages.map((m) => (m.id === id ? { ...m, status } : m)),
    })),

  updateMessageCitations: (id, citations) =>
    set((state) => ({
      messages: state.messages.map((m) => (m.id === id ? { ...m, citations } : m)),
    })),

  updateMessageTokenCount: (id, tokenCount) =>
    set((state) => ({
      messages: state.messages.map((m) => (m.id === id ? { ...m, tokenCount } : m)),
    })),

  setTyping: (typing) => set({ isTyping: typing }),

  setStreaming: (streaming, messageId = null) =>
    set({ isStreaming: streaming, streamingMessageId: streaming ? messageId : null }),

  setInputValue: (value) => set({ inputValue: value.slice(0, MAX_INPUT_CHARACTERS) }),

  clearInput: () => set({ inputValue: "" }),

  clearMessages: () => set({ messages: [] }),

  setPendingToolAction: (action) => set({ pendingToolAction: action }),
  clearPendingToolAction: () => set({ pendingToolAction: null }),
}));
