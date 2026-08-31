import type { LLMProvider, ToolDefinition, ParsedToolCall } from "@/services/ai/LLMProvider";
import type { APIMChatMessage } from "@/services/ai/APIMProvider";
import type { ContextSnapshot } from "@/services/context/ContextEngine";

export type { ContextSnapshot } from "@/services/context/ContextEngine";

/**
 * A prior conversation turn passed to the provider for multi-turn context.
 * Mirrors APIMChatMessage so ConversationService stays decoupled from
 * APIM-specific types at the call site — the cast happens here.
 */
export interface ConversationTurn {
  role: "user" | "assistant";
  content: string;
}

/**
 * Describes a folder index change that requires explicit user confirmation
 * before the action is executed.
 */
export interface PendingToolAction {
  type: "add_folder" | "remove_folder";
  toolCallId: string;
  path: string;
  folderId?: string;
  reason: string;
}

/**
 * ConversationService owns all conversation business logic.
 *
 * This class is completely framework-independent:
 * - No React imports.
 * - No Zustand imports.
 * - No JSX.
 * - No DOM APIs.
 *
 * It communicates results back to the caller through the ConversationCallbacks
 * interface, which the React layer (useConversation) implements using Zustand
 * store mutations. This inversion keeps the service decoupled from the UI.
 *
 * The service receives its LLMProvider through constructor injection.
 * Swapping providers (Mock ↔ APIM) requires only passing a different
 * implementation — this class never changes.
 */

export interface ConversationCallbacks {
  /** Called once before the provider begins generating a response. */
  onTypingStart(): void;

  /** Called when the provider produces the first chunk. */
  onTypingEnd(): void;

  /** Called when streaming begins. messageId identifies the message slot. */
  onStreamStart(messageId: string): void;

  /** Called for each incremental chunk of content. */
  onStreamChunk(messageId: string, accumulatedContent: string): void;

  /** Called when the full response has been delivered. */
  onStreamComplete(messageId: string): void;

  /** Called if the stream is cancelled before completion. */
  onStreamCancelled(messageId: string): void;

  /**
   * Called when the service needs a new message slot for the assistant response.
   * The callback must create the message and return its ID so the service can
   * reference it in subsequent chunk/complete/cancelled events.
   */
  onAssistantMessageCreate(): string;

  /**
   * Called when the model invokes a read-only tool (list_indexed_files,
   * list_indexed_folders). Must resolve with the tool result string so the
   * service can continue the conversation with the result injected.
   */
  onReadToolCall?(name: string, args: Record<string, unknown>): Promise<string>;

  /**
   * Called when the model proposes a write action (propose_add_folder,
   * propose_remove_folder) that requires explicit user confirmation.
   * The service stops streaming and waits for the user to confirm or cancel.
   */
  onPendingToolAction?(action: PendingToolAction): void;
}

// ─── Tool definitions ────────────────────────────────────────────────────────

const AGENT_TOOLS: ToolDefinition[] = [
  {
    type: "function",
    function: {
      name: "list_indexed_folders",
      description:
        "List all folders I am currently watching and indexing. Call this before claiming no folders are indexed.",
      parameters: {
        type: "object",
        properties: {},
        required: [],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "list_indexed_files",
      description:
        "List all files currently in the knowledge base. Call this before claiming no files are indexed.",
      parameters: {
        type: "object",
        properties: {
          workspace_path: {
            type: "string",
            description: "Optional: limit results to a specific workspace folder path.",
          },
        },
        required: [],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "propose_add_folder",
      description:
        "Propose adding a folder to the index. The user will be shown a confirmation card before any action is taken.",
      parameters: {
        type: "object",
        properties: {
          path: { type: "string", description: "Absolute path of the folder to add." },
          reason: {
            type: "string",
            description: "Brief explanation of why this folder should be indexed.",
          },
        },
        required: ["path", "reason"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "propose_remove_folder",
      description:
        "Propose removing a watched folder from the index. The user will confirm before anything is removed.",
      parameters: {
        type: "object",
        properties: {
          folder_id: { type: "string", description: "The ID of the watched folder to remove." },
          folder_path: {
            type: "string",
            description: "The path of the folder (shown in the confirmation UI).",
          },
          reason: {
            type: "string",
            description: "Brief explanation of why this folder should be removed.",
          },
        },
        required: ["folder_id", "folder_path", "reason"],
      },
    },
  },
];

const READ_TOOL_NAMES = new Set(["list_indexed_files", "list_indexed_folders"]);

// ─── Service ─────────────────────────────────────────────────────────────────

export class ConversationService {
  private readonly provider: LLMProvider;
  private abortController: AbortController | null = null;

  constructor(provider: LLMProvider) {
    this.provider = provider;
  }

  /**
   * Sends a user prompt and streams the provider response.
   * Cancels any in-flight request before starting a new one.
   *
   * When the model calls a read-only tool (list_indexed_files / list_indexed_folders),
   * the service executes it via callbacks.onReadToolCall, injects the result, and
   * re-invokes the provider automatically — the user sees a single flowing response.
   *
   * When the model calls a write tool (propose_add_folder / propose_remove_folder),
   * the service emits the action via callbacks.onPendingToolAction and stops streaming.
   * The UI then shows a confirmation card; the user's choice is handled by
   * useConversation.confirmToolAction.
   */
  async send(
    prompt: string,
    callbacks: ConversationCallbacks,
    history?: ConversationTurn[],
    context?: ContextSnapshot
  ): Promise<void> {
    // Cancel any previous request before starting a new one.
    this.cancel();

    this.abortController = new AbortController();
    const { signal } = this.abortController;

    callbacks.onTypingStart();

    const assistantMessageId = callbacks.onAssistantMessageCreate();
    let accumulated = "";
    let streamStarted = false;

    try {
      const apimHistory = history?.map<APIMChatMessage>((t) => ({
        role: t.role,
        content: t.content,
      }));

      const systemMessage = this.buildSystemMessage(context);

      // Tool exchange history appended on read-tool re-loops.
      // Starts with the original user message so the continuation is coherent.
      const toolExchangeHistory: APIMChatMessage[] = [];
      let userMsgAddedToExchange = false;

      let continueLoop = true;
      while (continueLoop) {
        continueLoop = false;

        // On re-loops, pass "" as prompt — the user message is already in
        // toolExchangeHistory and buildMessages skips empty prompts.
        const loopPrompt = userMsgAddedToExchange ? "" : prompt;
        const combinedHistory: APIMChatMessage[] = [...(apimHistory ?? []), ...toolExchangeHistory];

        const stream = this.provider.streamResponse(loopPrompt, {
          signal,
          history: combinedHistory.length > 0 ? combinedHistory : undefined,
          systemMessage,
          tools: AGENT_TOOLS,
        });

        for await (const chunk of stream) {
          if (signal.aborted) break;

          if (!streamStarted) {
            callbacks.onTypingEnd();
            callbacks.onStreamStart(assistantMessageId);
            streamStarted = true;
          }

          // Tool call response — handle and optionally re-loop.
          if (chunk.toolCalls && chunk.toolCalls.length > 0) {
            await this.handleToolCalls(
              chunk.toolCalls,
              prompt,
              toolExchangeHistory,
              userMsgAddedToExchange,
              callbacks,
              (reloop) => {
                continueLoop = reloop;
              },
              () => {
                userMsgAddedToExchange = true;
              }
            );
            break; // Exit chunk loop — either re-loop or done.
          }

          if (!chunk.done) {
            accumulated += chunk.content;
            callbacks.onStreamChunk(assistantMessageId, accumulated);
          }
        }
      }

      // Ensure typing indicator is cleared even if no chunks arrived.
      if (!streamStarted) {
        callbacks.onTypingEnd();
        callbacks.onStreamStart(assistantMessageId);
      }

      if (signal.aborted) {
        callbacks.onStreamCancelled(assistantMessageId);
      } else {
        callbacks.onStreamComplete(assistantMessageId);
      }
    } catch (err) {
      console.error("[AI] request failed:", err instanceof Error ? err.message : err);
      if (!streamStarted) callbacks.onTypingEnd();
      callbacks.onStreamCancelled(assistantMessageId);
    } finally {
      this.abortController = null;
    }
  }

  /**
   * Processes tool calls from the model.
   *
   * Read tools are executed immediately; write tools surface as pending
   * confirmations. The setReloop and setUserMsgAdded callbacks mutate loop
   * state in the parent send() closure without coupling this method to it.
   */
  private async handleToolCalls(
    toolCalls: ParsedToolCall[],
    originalPrompt: string,
    toolExchangeHistory: APIMChatMessage[],
    userMsgAlreadyAdded: boolean,
    callbacks: ConversationCallbacks,
    setReloop: (reloop: boolean) => void,
    setUserMsgAdded: () => void
  ): Promise<void> {
    const toolCall = toolCalls[0]; // Handle first tool call per response.

    if (READ_TOOL_NAMES.has(toolCall.name)) {
      const result = callbacks.onReadToolCall
        ? await callbacks.onReadToolCall(toolCall.name, toolCall.arguments)
        : "Tool not available.";

      // First read-tool call: prepend the original user message so the
      // continued conversation is coherent from the model's perspective.
      if (!userMsgAlreadyAdded) {
        toolExchangeHistory.push({ role: "user", content: originalPrompt });
        setUserMsgAdded();
      }

      // Append the assistant's tool_calls turn and the tool result.
      toolExchangeHistory.push({
        role: "assistant",
        content: null,
        tool_calls: [
          {
            id: toolCall.id,
            type: "function",
            function: {
              name: toolCall.name,
              arguments: JSON.stringify(toolCall.arguments),
            },
          },
        ],
      });
      toolExchangeHistory.push({
        role: "tool",
        tool_call_id: toolCall.id,
        content: result,
      });

      setReloop(true);
    } else if (toolCall.name === "propose_add_folder") {
      if (callbacks.onPendingToolAction) {
        callbacks.onPendingToolAction({
          type: "add_folder",
          toolCallId: toolCall.id,
          path: String(toolCall.arguments.path ?? ""),
          reason: String(toolCall.arguments.reason ?? ""),
        });
      }
    } else if (toolCall.name === "propose_remove_folder") {
      if (callbacks.onPendingToolAction) {
        callbacks.onPendingToolAction({
          type: "remove_folder",
          toolCallId: toolCall.id,
          path: String(toolCall.arguments.folder_path ?? ""),
          folderId: String(toolCall.arguments.folder_id ?? ""),
          reason: String(toolCall.arguments.reason ?? ""),
        });
      }
    }
  }

  /**
   * Builds a structured system message from a context snapshot.
   *
   * When retrieved chunks are present the message instructs the LLM to:
   * - Synthesise across all provided excerpts rather than echoing one.
   * - Cite every factual claim using the exact source path in the format
   *   `[path/to/file]` immediately after the claim.
   * - Distinguish clearly between knowledge-base facts and general knowledge.
   *
   * Returns undefined when the snapshot carries no meaningful signals so
   * the provider sends no system message rather than an empty one.
   */
  private buildSystemMessage(context?: ContextSnapshot): string | undefined {
    const parts: string[] = [];

    if (context) {
      // Prepend compressed prior-session memory so the LLM can reference earlier
      // conclusions without re-reading the full message history.
      if (context.conversationSummary) {
        parts.push(
          `CONVERSATION MEMORY (compressed summary of earlier turns):\n${context.conversationSummary}`
        );
      }

      if (context.activeProjectFolder) {
        parts.push(`Active workspace folder: ${context.activeProjectFolder}`);
      }
      if (context.explicitContext) {
        parts.push(context.explicitContext);
      }

      const hasChunks = context.retrievedChunks && context.retrievedChunks.length > 0;
      const hasLegacyContext = !hasChunks && Boolean(context.retrievedContext);

      if (hasChunks && context.retrievedChunks) {
        const excerptBlock = context.retrievedChunks
          .map((c, i) => {
            const filename = c.documentPath.replace(/\\/g, "/").split("/").at(-1) ?? c.documentPath;
            return `[${i + 1}] ${filename}\n${c.content}`;
          })
          .join("\n\n---\n\n");

        parts.push(
          `You are an AI assistant with access to the user's indexed knowledge base.\n` +
            `The following document excerpts were retrieved and ranked by relevance to the user's query.\n` +
            `Excerpt [1] is the most relevant; lower-numbered excerpts should be weighted accordingly,\n` +
            `but you MUST synthesise across all of them — do not ignore later excerpts.\n\n` +
            `CITATION RULES — you MUST follow ALL of these exactly:\n` +
            `1. Cite sources using their excerpt number in square brackets immediately after the claim, e.g. [1] or [2].\n` +
            `   Do NOT include file paths or folder names in your response — the UI displays sources separately.\n` +
            `2. Synthesise across ALL provided excerpts — do not rely on only the first one.\n` +
            `3. If excerpts conflict, surface the contradiction explicitly.\n` +
            `4. Clearly distinguish between information from the excerpts and your general knowledge.\n` +
            `5. If the excerpts do not contain enough information to answer, say so — do NOT fill gaps with invented details.\n\n` +
            `Retrieved excerpts (ordered by relevance, most relevant first):\n\n${excerptBlock}`
        );
      } else if (hasLegacyContext && context.retrievedContext) {
        parts.push(
          `The following document excerpts were retrieved from the user's indexed knowledge base.\n` +
            `You may ONLY cite file paths that appear verbatim in the excerpts below — do not invent any paths.\n` +
            `When answering, cite the exact file path in square brackets after each factual claim.\n\n` +
            `Retrieved excerpts:\n${context.retrievedContext}`
        );
      } else {
        parts.push(
          `You are a helpful AI assistant with access to the user's indexed knowledge base.\n` +
            `No relevant documents were retrieved for this specific query via semantic search.\n` +
            `If the user asks what files or folders are indexed, use the list_indexed_files or list_indexed_folders tool first — do NOT claim nothing is indexed without checking.\n` +
            `For conversational or general questions, answer helpfully without mentioning the index.`
        );
      }
    }

    // Tool awareness note — always appended so the model knows what's available.
    parts.push(
      `TOOLS AVAILABLE:\n` +
        `- list_indexed_folders: check which folders are being watched. Call before stating no folders exist.\n` +
        `- list_indexed_files: list all indexed files. Call before stating nothing is indexed.\n` +
        `- propose_add_folder: suggest a folder to add to the index (user confirms first).\n` +
        `- propose_remove_folder: suggest removing a folder from the index (user confirms first).\n` +
        `Use these tools proactively when the user asks about their index or wants to manage which folders are indexed.`
    );

    return parts.length > 0 ? parts.join("\n\n") : undefined;
  }

  /**
   * Cancels the active stream. Safe to call when no stream is in progress.
   */
  cancel(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    this.provider.cancel();
  }
}
