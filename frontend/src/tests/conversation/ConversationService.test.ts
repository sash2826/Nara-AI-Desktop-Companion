import { describe, it, expect, vi, beforeEach } from "vitest";
import { ConversationService } from "@/services/conversation/ConversationService";
import type {
  ConversationCallbacks,
  ConversationTurn,
} from "@/services/conversation/ConversationService";
import type { ContextSnapshot } from "@/services/context/ContextEngine";
import type { LLMProvider, LLMRequestOptions, LLMStreamChunk } from "@/services/ai/LLMProvider";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makeChunks(...words: string[]): LLMStreamChunk[] {
  return [
    ...words.map((w) => ({ content: w, done: false as const })),
    { content: "", done: true as const },
  ];
}

function makeProvider(chunks: LLMStreamChunk[] = makeChunks("hello")): {
  provider: LLMProvider;
  capturedOptions: () => LLMRequestOptions | undefined;
  capturedPrompt: () => string | undefined;
} {
  let lastPrompt: string | undefined;
  let lastOptions: LLMRequestOptions | undefined;

  const provider: LLMProvider = {
    generateResponse: vi.fn(),
    cancel: vi.fn(),
    async *streamResponse(prompt, options) {
      lastPrompt = prompt;
      lastOptions = options;
      for (const chunk of chunks) {
        yield chunk;
      }
    },
  };

  return {
    provider,
    capturedOptions: () => lastOptions,
    capturedPrompt: () => lastPrompt,
  };
}

function makeCallbacks(): ConversationCallbacks & { messages: string[] } {
  const messages: string[] = [];
  let idCounter = 0;
  return {
    messages,
    onTypingStart: vi.fn(),
    onTypingEnd: vi.fn(),
    onStreamStart: vi.fn(),
    onStreamChunk: vi.fn((_id, content) => messages.push(content)),
    onStreamComplete: vi.fn(),
    onStreamCancelled: vi.fn(),
    onAssistantMessageCreate: vi.fn(() => `msg-${++idCounter}`),
  };
}

// ─── System message construction (tested via captured provider options) ───────

describe("ConversationService — system message injection", () => {
  it("passes no systemMessage when context is undefined", async () => {
    const { provider, capturedOptions } = makeProvider();
    const service = new ConversationService(provider);
    await service.send("hello", makeCallbacks());
    expect(capturedOptions()?.systemMessage).toBeUndefined();
  });

  it("passes no systemMessage when context has no meaningful signals", async () => {
    const { provider, capturedOptions } = makeProvider();
    const service = new ConversationService(provider);
    const emptyContext: ContextSnapshot = {
      activeProjectFolder: null,
      recentDocuments: [],
      explicitContext: null,
      retrievedChunks: null,
      retrievedContext: null,
      conversationSummary: null,
    };
    await service.send("hello", makeCallbacks(), undefined, emptyContext);
    expect(capturedOptions()?.systemMessage).toBeUndefined();
  });

  it("includes activeProjectFolder in the system message", async () => {
    const { provider, capturedOptions } = makeProvider();
    const service = new ConversationService(provider);
    const context: ContextSnapshot = {
      activeProjectFolder: "/projects/my-app/src",
      recentDocuments: [],
      explicitContext: null,
      retrievedChunks: null,
      retrievedContext: null,
      conversationSummary: null,
    };
    await service.send("hello", makeCallbacks(), undefined, context);
    expect(capturedOptions()?.systemMessage).toContain(
      "Active workspace folder: /projects/my-app/src"
    );
  });

  it("includes recentDocuments in the system message", async () => {
    const { provider, capturedOptions } = makeProvider();
    const service = new ConversationService(provider);
    const context: ContextSnapshot = {
      activeProjectFolder: null,
      recentDocuments: ["/projects/a.ts", "/projects/b.ts"],
      explicitContext: null,
      retrievedChunks: null,
      retrievedContext: null,
      conversationSummary: null,
    };
    await service.send("hello", makeCallbacks(), undefined, context);
    const msg = capturedOptions()?.systemMessage ?? "";
    expect(msg).toContain("/projects/a.ts");
    expect(msg).toContain("/projects/b.ts");
  });

  it("includes explicitContext in the system message", async () => {
    const { provider, capturedOptions } = makeProvider();
    const service = new ConversationService(provider);
    const context: ContextSnapshot = {
      activeProjectFolder: null,
      recentDocuments: [],
      explicitContext: "Focus on TypeScript best practices.",
      retrievedChunks: null,
      retrievedContext: null,
      conversationSummary: null,
    };
    await service.send("hello", makeCallbacks(), undefined, context);
    expect(capturedOptions()?.systemMessage).toContain("Focus on TypeScript best practices.");
  });

  it("combines all three signals into one system message", async () => {
    const { provider, capturedOptions } = makeProvider();
    const service = new ConversationService(provider);
    const context: ContextSnapshot = {
      activeProjectFolder: "/projects/app",
      recentDocuments: ["/projects/app/main.ts"],
      explicitContext: "Be concise.",
      retrievedChunks: null,
      retrievedContext: null,
      conversationSummary: null,
    };
    await service.send("hello", makeCallbacks(), undefined, context);
    const msg = capturedOptions()?.systemMessage ?? "";
    expect(msg).toContain("Active workspace folder: /projects/app");
    expect(msg).toContain("/projects/app/main.ts");
    expect(msg).toContain("Be concise.");
  });

  it("system message contains activeProjectFolder text", async () => {
    const { provider, capturedOptions } = makeProvider();
    const service = new ConversationService(provider);
    const context: ContextSnapshot = {
      activeProjectFolder: "/projects/app",
      recentDocuments: [],
      retrievedChunks: null,
      retrievedContext: null,
      conversationSummary: null,
      explicitContext: null,
    };
    await service.send("hello", makeCallbacks(), undefined, context);
    expect(capturedOptions()?.systemMessage).toContain("Active workspace folder: /projects/app");
  });
});

// ─── Streaming callbacks ───────────────────────────────────────────────────────

describe("ConversationService — streaming lifecycle", () => {
  let service: ConversationService;
  let callbacks: ReturnType<typeof makeCallbacks>;

  beforeEach(() => {
    const { provider } = makeProvider(makeChunks("Hello", " world"));
    service = new ConversationService(provider);
    callbacks = makeCallbacks();
  });

  it("calls onTypingStart before the first chunk", async () => {
    await service.send("hi", callbacks);
    expect(callbacks.onTypingStart).toHaveBeenCalledOnce();
  });

  it("calls onAssistantMessageCreate to reserve a slot", async () => {
    await service.send("hi", callbacks);
    expect(callbacks.onAssistantMessageCreate).toHaveBeenCalledOnce();
  });

  it("calls onStreamComplete when stream finishes normally", async () => {
    await service.send("hi", callbacks);
    expect(callbacks.onStreamComplete).toHaveBeenCalledOnce();
    expect(callbacks.onStreamCancelled).not.toHaveBeenCalled();
  });

  it("accumulates chunks correctly", async () => {
    await service.send("hi", callbacks);
    const lastContent = callbacks.messages.at(-1);
    expect(lastContent).toBe("Hello world");
  });
});

// ─── History forwarding ────────────────────────────────────────────────────────

describe("ConversationService — history forwarding", () => {
  it("forwards conversation history to the provider", async () => {
    const { provider, capturedOptions } = makeProvider();
    const service = new ConversationService(provider);

    const history: ConversationTurn[] = [
      { role: "user", content: "First question" },
      { role: "assistant", content: "First answer" },
    ];

    await service.send("Second question", makeCallbacks(), history);

    const forwarded = capturedOptions()?.history ?? [];
    expect(forwarded).toHaveLength(2);
    expect(forwarded[0]).toMatchObject({ role: "user", content: "First question" });
    expect(forwarded[1]).toMatchObject({ role: "assistant", content: "First answer" });
  });

  it("passes no history when none is provided", async () => {
    const { provider, capturedOptions } = makeProvider();
    const service = new ConversationService(provider);
    await service.send("hello", makeCallbacks());
    expect(capturedOptions()?.history).toBeUndefined();
  });
});
