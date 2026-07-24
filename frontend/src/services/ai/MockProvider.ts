import type { AIProvider, AIRequestOptions, AIStreamChunk } from "./AIProvider";

/**
 * Simulates AI provider behaviour using predefined keyword-matched responses.
 *
 * Responsibilities:
 * - Keyword matching against the user prompt.
 * - Returning markdown-formatted responses with code blocks and tables.
 * - Simulating a typing/thinking delay before the first chunk.
 * - Simulating token-by-token streaming.
 *
 * No UI, framework, or Zustand dependency. Pure TypeScript.
 */

interface MockResponseEntry {
  keywords: string[];
  response: string;
}

const STREAM_INTERVAL_MS = 18;
const THINKING_DELAY_MS = 600;

const MOCK_RESPONSE_TABLE: MockResponseEntry[] = [
  {
    keywords: ["hello", "hi", "hey", "greetings"],
    response:
      "Hello! Great to hear from you. I'm ready to help with your documents and knowledge base. What would you like to explore today?",
  },
  {
    keywords: ["summarise", "summarize", "summary"],
    response:
      "## Document Summary\n\nDocument analysis will be available once your workspace is indexed. Here's what I'll be able to do:\n\n- **Extract key points** from any document\n- **Identify themes** across multiple files\n- **Generate structured summaries** in any format\n\nIndex your first folder to get started.",
  },
  {
    keywords: ["search", "find", "look for"],
    response:
      'Semantic search across your workspace will be available after indexing. I\'ll be able to:\n\n```\nQuery: "project deadlines Q3"\nResults: 12 relevant documents found\n  → report-q3-2025.pdf (92% match)\n  → meeting-notes-july.docx (87% match)\n  → timeline.xlsx (81% match)\n```\n\nConnect your workspace to enable full-text and semantic search.',
  },
  {
    keywords: ["explain", "what is", "how does", "describe"],
    response:
      "I can explain any concept found in your documents or provide general knowledge explanations. Once your workspace is connected, my explanations will be grounded in **your specific documents and context**.\n\nWhat would you like me to explain?",
  },
  {
    keywords: ["note", "notes", "generate"],
    response:
      "## Generated Notes\n\nI can generate structured notes from:\n\n- Meeting transcripts\n- Research papers\n- Long-form documents\n- Web articles\n\nNote generation requires an indexed workspace. Would you like to set that up?",
  },
  {
    keywords: ["translate", "translation", "language"],
    response:
      "Translation support will be available in a future update. I'll be able to translate documents and conversations across multiple languages while preserving formatting and structure.",
  },
  {
    keywords: ["help", "what can you do", "capabilities"],
    response:
      "Here's what I can help you with:\n\n| Capability | Status |\n|---|---|\n| Document summarisation | Coming soon |\n| Semantic search | Coming soon |\n| Concept explanation | Available |\n| Note generation | Coming soon |\n| Translation | Planned |\n| Knowledge graph | Coming soon |\n\nConnect your workspace to unlock all capabilities.",
  },
];

const FALLBACK_RESPONSE =
  "That's an interesting question. Once your workspace is indexed and AI services are connected, I'll be able to give you a detailed, context-aware answer grounded in your documents.\n\nFor now, I'm operating in demo mode. Try asking me to **summarise**, **search**, or **explain** something.";

function resolveResponse(prompt: string): string {
  const lower = prompt.toLowerCase();
  const match = MOCK_RESPONSE_TABLE.find((entry) =>
    entry.keywords.some((kw) => lower.includes(kw))
  );
  return match ? match.response : FALLBACK_RESPONSE;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class MockProvider implements AIProvider {
  private cancelled = false;

  async generateResponse(prompt: string, options?: AIRequestOptions): Promise<string> {
    this.cancelled = false;
    await sleep(THINKING_DELAY_MS);

    if (this.cancelled || options?.signal?.aborted) {
      return "";
    }

    return resolveResponse(prompt);
  }

  async *streamResponse(prompt: string, options?: AIRequestOptions): AsyncIterable<AIStreamChunk> {
    this.cancelled = false;

    // Simulate model thinking delay before the first token.
    await sleep(THINKING_DELAY_MS);

    if (this.cancelled || options?.signal?.aborted) {
      return;
    }

    const fullResponse = resolveResponse(prompt);

    for (const char of fullResponse) {
      if (this.cancelled || options?.signal?.aborted) {
        return;
      }

      yield { content: char, done: false };
      await sleep(STREAM_INTERVAL_MS);
    }

    yield { content: "", done: true };
  }

  cancel(): void {
    this.cancelled = true;
  }
}
