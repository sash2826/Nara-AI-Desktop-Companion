/**
 * LLM provider configuration for the Enterprise AI Companion.
 *
 * The desktop application communicates with exactly two provider
 * implementations:
 *
 *   "mock"  — MockProvider. Local keyword matching. No network calls.
 *             Used during development and automated testing.
 *
 *   "apim"  — APIMProvider. Routes all requests through Azure API Management.
 *             Used in all production and staging deployments.
 *
 * Switching from development to production requires only changing
 * LLM_CONFIG.provider from "mock" to "apim".
 *
 * The desktop application never communicates directly with any LLM vendor.
 * Model selection (GPT, Claude, Gemini, Mistral, Llama, etc.) is an APIM
 * policy concern — invisible to the desktop application.
 */

export type LLMProviderKey = "mock" | "apim";

/**
 * Configuration specific to the APIMProvider.
 *
 * Values must come from environment variables or a secure configuration
 * store. They must never be hardcoded in source code.
 *
 * ── TODO (Phase 01): Populate these from the application configuration
 * service once infrastructure is established.
 */
export interface APIMConfig {
  /** APIM gateway endpoint for LLM requests. */
  endpoint: string;

  /**
   * APIM subscription key used for API-key authentication.
   * Will be replaced by an Azure AD bearer token in Phase 02.
   */
  subscriptionKey: string;
}

export interface LLMConfig {
  provider: LLMProviderKey;

  /**
   * Required when provider is "apim".
   * Omitted for "mock" — MockProvider needs no network configuration.
   */
  apim?: APIMConfig;
}

/**
 * Active configuration.
 *
 * Development default: MockProvider.
 * Production: set provider to "apim" and supply apim credentials via
 * environment variables before instantiation.
 */
export const LLM_CONFIG: LLMConfig = {
  provider: "mock",
};
