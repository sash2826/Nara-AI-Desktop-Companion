/**
 * Integration tests: GlassPrompt ↔ ConversationService ↔ OrbController
 *
 * These tests mount the real providers and real components together.
 * No mocks are used for business logic — only for:
 *   - The LLMProvider (replaced with a controllable stub)
 *   - Framer Motion (replaced with plain divs — no animation frames)
 *
 * The stub provider lets each test control exactly when chunks arrive and
 * when the stream ends, so assertions about intermediate orb states are
 * deterministic.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { ConversationServiceContext } from "@/providers/ConversationServiceContext";
import { OrbControllerContext } from "@/providers/OrbControllerContext";
import { ConversationService } from "@/services/conversation/ConversationService";
import { OrbController } from "@/services/desktop/OrbController";
import { OrbState } from "@/services/orb/OrbState";
import { GlassPromptBody } from "@/components/glass-prompt/GlassPromptBody";
import type { LLMProvider, LLMStreamChunk, LLMRequestOptions } from "@/services/ai/LLMProvider";
import { useConversationStore } from "@/store/conversationStore";

// ── jsdom stubs ───────────────────────────────────────────────────────────────

// jsdom does not implement scrollIntoView. MessageList calls it on its sentinel
// element; stub it globally so the effect does not throw.
Element.prototype.scrollIntoView = vi.fn();

// ── Framer Motion stub ────────────────────────────────────────────────────────

// Strip all Framer-specific props (whileHover, whileFocus, initial, animate,
// exit, variants, transition, layoutId) before forwarding to the DOM element —
// otherwise React warns about unknown attributes on native elements.
function stripMotionProps<T extends Record<string, unknown>>(props: T): T {
  const MOTION_KEYS = new Set([
    "initial",
    "animate",
    "exit",
    "variants",
    "transition",
    "whileHover",
    "whileFocus",
    "whileTap",
    "whileDrag",
    "whileInView",
    "layoutId",
    "onAnimationStart",
    "onAnimationComplete",
    "onUpdate",
  ]);
  return Object.fromEntries(Object.entries(props).filter(([k]) => !MOTION_KEYS.has(k))) as T;
}

vi.mock("framer-motion", async (importOriginal) => {
  const actual = await importOriginal<typeof import("framer-motion")>();
  return {
    ...actual,
    AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    motion: {
      ...actual.motion,
      div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
        <div {...stripMotionProps(props as Record<string, unknown>)}>{children}</div>
      ),
      textarea: ({ children, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) => (
        <textarea {...stripMotionProps(props as Record<string, unknown>)}>{children}</textarea>
      ),
      span: ({ children, ...props }: React.HTMLAttributes<HTMLSpanElement>) => (
        <span {...stripMotionProps(props as Record<string, unknown>)}>{children}</span>
      ),
      button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
        <button {...stripMotionProps(props as Record<string, unknown>)}>{children}</button>
      ),
    },
  };
});

// ── Controllable LLM provider stub ────────────────────────────────────────────

/**
 * Creates a stub LLMProvider whose stream is driven externally.
 *
 * Call `emit(content)` to push a chunk, `finish()` to end the stream
 * cleanly, and `fail(error)` to simulate a provider error. The stub
 * records every prompt it receives so tests can assert on it.
 */
function makeControllableProvider() {
  let resolveNext: ((value: IteratorResult<LLMStreamChunk>) => void) | null = null;
  const queue: Array<() => IteratorResult<LLMStreamChunk>> = [];
  let cancelled = false;
  const prompts: string[] = [];

  function enqueue(item: () => IteratorResult<LLMStreamChunk>) {
    if (resolveNext) {
      resolveNext(item());
      resolveNext = null;
    } else {
      queue.push(item);
    }
  }

  const provider: LLMProvider = {
    generateResponse: vi.fn(async () => ""),

    streamResponse(_prompt: string, _options?: LLMRequestOptions): AsyncIterable<LLMStreamChunk> {
      prompts.push(_prompt);
      cancelled = false;

      return {
        [Symbol.asyncIterator]() {
          return {
            next(): Promise<IteratorResult<LLMStreamChunk>> {
              if (queue.length > 0) {
                return Promise.resolve(queue.shift()!());
              }
              return new Promise((resolve) => {
                resolveNext = resolve;
              });
            },
          };
        },
      };
    },

    cancel() {
      cancelled = true;
      if (resolveNext) {
        resolveNext({ value: { content: "", done: true }, done: true });
        resolveNext = null;
      }
    },
  };

  const controls = {
    emit(content: string) {
      enqueue(() => ({ value: { content, done: false }, done: false }));
    },
    finish() {
      enqueue(() => ({ value: { content: "", done: true }, done: true }));
    },
    get prompts() {
      return prompts;
    },
    get cancelled() {
      return cancelled;
    },
  };

  return { provider, controls };
}

// ── Render helper ─────────────────────────────────────────────────────────────

/**
 * Mounts GlassPromptBody wired to a real ConversationService (using a
 * stub provider) and a real OrbController (in Active state — simulating
 * the Glass Prompt being open).
 */
function renderIntegration() {
  const { provider, controls } = makeControllableProvider();
  const service = new ConversationService(provider);
  const controller = new OrbController();

  // Simulate the Glass Prompt being open: initialize the controller and
  // move it to Active state so the orb state arc can proceed.
  void controller.initialize();
  controller.onActivate();

  const utils = render(
    <ConversationServiceContext.Provider value={service}>
      <OrbControllerContext.Provider value={controller}>
        <GlassPromptBody />
      </OrbControllerContext.Provider>
    </ConversationServiceContext.Provider>
  );

  return { ...utils, service, controller, controls };
}

// ── Test setup ────────────────────────────────────────────────────────────────

beforeEach(() => {
  // Reset the Zustand conversation store before each test.
  useConversationStore.setState({
    messages: [],
    isTyping: false,
    isStreaming: false,
    streamingMessageId: null,
    inputValue: "",
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("GlassPrompt ↔ ConversationService ↔ OrbController integration", () => {
  // ── Rendering ──────────────────────────────────────────────────────────────

  it("renders the prompt input and send button", () => {
    renderIntegration();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument();
  });

  it("send button is disabled when input is empty", () => {
    renderIntegration();
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("send button becomes enabled when input has text", async () => {
    renderIntegration();
    const input = screen.getByRole("textbox");
    await act(async () => {
      fireEvent.change(input, { target: { value: "hello" } });
    });
    expect(screen.getByRole("button", { name: /send/i })).not.toBeDisabled();
  });

  // ── Orb state arc ──────────────────────────────────────────────────────────

  it("orb starts in Active state when Glass Prompt is open", () => {
    const { controller } = renderIntegration();
    expect(controller.getState().orbState).toBe(OrbState.Active);
  });

  it("orb moves to Processing when a message is sent", async () => {
    const { controller, controls } = renderIntegration();
    const input = screen.getByRole("textbox");

    await act(async () => {
      fireEvent.change(input, { target: { value: "hello" } });
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });

    // Provider has not yet yielded any chunk — orb should be Processing.
    expect(controller.getState().orbState).toBe(OrbState.Processing);

    // Drain the stream so the service doesn't hang.
    await act(async () => {
      controls.finish();
      await Promise.resolve();
    });
  });

  it("orb moves to Streaming when the first chunk arrives", async () => {
    const { controller, controls } = renderIntegration();
    const input = screen.getByRole("textbox");

    await act(async () => {
      fireEvent.change(input, { target: { value: "hello" } });
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await act(async () => {
      controls.emit("Hi");
      await Promise.resolve();
    });

    expect(controller.getState().orbState).toBe(OrbState.Streaming);

    // Drain.
    await act(async () => {
      controls.finish();
      await Promise.resolve();
    });
  });

  it("orb moves to Success when the stream completes", async () => {
    const { controller, controls } = renderIntegration();
    const input = screen.getByRole("textbox");

    await act(async () => {
      fireEvent.change(input, { target: { value: "hello" } });
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await act(async () => {
      controls.emit("Hi");
      await Promise.resolve();
    });
    await act(async () => {
      controls.finish();
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(controller.getState().orbState).toBe(OrbState.Success);
    });
  });

  it("orb returns to Active after the Success pause", async () => {
    const { controller, controls } = renderIntegration();
    const input = screen.getByRole("textbox");

    await act(async () => {
      fireEvent.change(input, { target: { value: "hello" } });
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await act(async () => {
      controls.emit("Hi");
      await Promise.resolve();
    });
    await act(async () => {
      controls.finish();
      await Promise.resolve();
    });

    // Wait for the 800 ms onReturnToActive setTimeout in GlassPromptBody to fire.
    await waitFor(
      () => {
        expect(controller.getState().orbState).toBe(OrbState.Active);
      },
      { timeout: 2000 }
    );
  });

  // ── Message content ────────────────────────────────────────────────────────

  it("user message appears in the store after sending", async () => {
    const { controls } = renderIntegration();
    const input = screen.getByRole("textbox");

    await act(async () => {
      fireEvent.change(input, { target: { value: "test prompt" } });
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });

    const messages = useConversationStore.getState().messages;
    expect(messages.some((m) => m.role === "user" && m.content === "test prompt")).toBe(true);

    await act(async () => {
      controls.finish();
      await Promise.resolve();
    });
  });

  it("assistant message accumulates streamed chunks", async () => {
    const { controls } = renderIntegration();
    const input = screen.getByRole("textbox");

    await act(async () => {
      fireEvent.change(input, { target: { value: "hello" } });
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await act(async () => {
      controls.emit("Hello");
      await Promise.resolve();
    });
    await act(async () => {
      controls.emit(", world");
      await Promise.resolve();
    });
    await act(async () => {
      controls.finish();
      await Promise.resolve();
    });

    const messages = useConversationStore.getState().messages;
    const assistant = messages.find((m) => m.role === "assistant");
    expect(assistant?.content).toBe("Hello, world");
  });

  it("input is cleared after sending", async () => {
    const { controls } = renderIntegration();
    const input = screen.getByRole("textbox");

    await act(async () => {
      fireEvent.change(input, { target: { value: "clear me" } });
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });

    expect((input as HTMLTextAreaElement | HTMLInputElement).value).toBe("");

    await act(async () => {
      controls.finish();
      await Promise.resolve();
    });
  });

  // ── Prompt forwarded to provider ──────────────────────────────────────────

  it("passes the user prompt to the LLM provider", async () => {
    const { controls } = renderIntegration();
    const input = screen.getByRole("textbox");

    await act(async () => {
      fireEvent.change(input, { target: { value: "what is Volvo?" } });
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await act(async () => {
      controls.finish();
      await Promise.resolve();
    });

    expect(controls.prompts).toContain("what is Volvo?");
  });
});
