/**
 * LLM provider configuration for the Enterprise AI Companion.
 *
 * Provider selection is automatic:
 *
 *   "apim"  — Selected when VITE_APIM_ENDPOINT is present in the environment.
 *             Routes all requests through Azure API Management.
 *             The subscription key is loaded at runtime from the OS keychain —
 *             it is never baked into the JS bundle.
 *
 *   "mock"  — Selected when VITE_APIM_ENDPOINT is absent. Returns local
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
   * Loaded at runtime from the OS keychain via IPCClient.loadCredential().
   * Empty string until the keychain resolves — requests made before that point
   * will fail with a 401 from APIM, which is the correct safe default.
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
const providerOverride = import.meta.env.VITE_LLM_PROVIDER as string | undefined;

function resolveProvider(): LLMProviderKey {
  if (providerOverride === "mock") return "mock";
  if (providerOverride === "apim") return "apim";
  // Auto-detect: use APIM when an endpoint is configured.
  // The subscription key is loaded at runtime from the OS keychain, not the bundle.
  return apimEndpoint ? "apim" : "mock";
}

function resolveAPIMConfig(): APIMConfig | undefined {
  if (!apimEndpoint) return undefined;
  return {
    endpoint: apimEndpoint,
    model: "gpt-5.4-mini_gb_2026-03-17",
    // Subscription key starts empty; ConversationServiceProvider injects the
    // keychain value via APIMProvider.setSubscriptionKey() after mount.
    subscriptionKey: "",
    timeoutMs: 30_000,
    maxRetries: 3,
  };
}

// ── Active configuration ───────────────────────────────────────────────────────

export const LLM_CONFIG: LLMConfig = {
  provider: resolveProvider(),
  apim: resolveAPIMConfig(),
};
