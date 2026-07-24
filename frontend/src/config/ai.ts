/**
 * AI provider configuration.
 *
 * Switching the active provider requires only changing `AI_CONFIG.provider`.
 * No UI, hook, or service implementation needs modification.
 *
 * Future values: "openai" | "claude" | "ollama" | "azure-openai" | "gemini" | "openrouter"
 */

export type AIProviderKey =
  "mock" | "openai" | "claude" | "ollama" | "azure-openai" | "gemini" | "openrouter";

export interface AIConfig {
  provider: AIProviderKey;
}

export const AI_CONFIG: AIConfig = {
  provider: "mock",
};
