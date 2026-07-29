/**
 * LLM provider configuration for the Enterprise AI Companion.
 *
 * Provider selection is automatic:
 *
 *   "apim"  — Selected when VITE_APIM_ENDPOINT and VITE_APIM_SUBSCRIPTION_KEY
 *             are both present in the environment. Routes all requests through
 *             Azure API Management. Used in production and staging.
 *
 *   "mock"  — Selected when either APIM env var is absent. Returns local
 *             keyword-matched responses with no network calls. Used during
 *             development when APIM credentials are not available.
 *
 * Override auto-detection by setting VITE_LLM_PROVIDER explicitly.
 *
 * The desktop application never communicates directly with any LLM vendor.
 * Model selection (GPT, Claude, Gemini, etc.) is an APIM policy concern
 * that is invisible to the desktop application.
 */

export type LLMProviderKey = "mock" | "apim";

/**
 * Configuration specific to the APIMProvider.
 *
 * Values come from environment variables — never hardcoded.
 */
export interface APIMConfig {
  /** APIM gateway endpoint for LLM requests. */
  endpoint: string;

  /**
   * Model deployment ID passed in the request body.
   * For GenAI Hub: e.g. "gpt-5.4-mini_gb_2026-03-17"
   */
  model: string;

  /**
   * APIM subscription key (api-key header).
   * Will be replaced by an Azure AD bearer token in Phase 02.
   */
  subscriptionKey: string;

  /**
   * Request timeout in milliseconds. Defaults to 30 000 ms.
   * Applies to both streaming and non-streaming requests.
   */
  timeoutMs: number;

  /**
   * Maximum number of retry attempts for retryable errors (429, 503).
   * Defaults to 3.
   */
  maxRetries: number;
}

export interface LLMConfig {
  provider: LLMProviderKey;

  /**
   * Required when provider is "apim".
   * Omitted for "mock" — MockProvider needs no network configuration.
   */
  apim?: APIMConfig;
}

// ── Environment variable resolution ───────────────────────────────────────────

const apimEndpoint = import.meta.env.VITE_APIM_ENDPOINT as string | undefined;
const apimKey = import.meta.env.VITE_APIM_SUBSCRIPTION_KEY as string | undefined;
const providerOverride = import.meta.env.VITE_LLM_PROVIDER as string | undefined;

function resolveProvider(): LLMProviderKey {
  if (providerOverride === "mock") return "mock";
  if (providerOverride === "apim") return "apim";
  // Auto-detect: use APIM when both credentials are present and non-empty.
  return apimEndpoint && apimKey ? "apim" : "mock";
}

function resolveAPIMConfig(): APIMConfig | undefined {
  if (!apimEndpoint || !apimKey) return undefined;
  return {
    endpoint: apimEndpoint,
    model: "gpt-5.4-mini_gb_2026-03-17",
    subscriptionKey: apimKey,
    timeoutMs: 30_000,
    maxRetries: 3,
  };
}

// ── Active configuration ───────────────────────────────────────────────────────

export const LLM_CONFIG: LLMConfig = {
  provider: resolveProvider(),
  apim: resolveAPIMConfig(),
};
