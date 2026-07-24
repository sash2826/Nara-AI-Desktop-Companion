import type { LLMConfig } from "@/config/ai";
import type { LLMProvider } from "@/services/ai/LLMProvider";
import { MockProvider } from "@/services/ai/MockProvider";
import { APIMProvider } from "@/services/ai/APIMProvider";

/**
 * Creates and returns the active LLMProvider based on the supplied configuration.
 *
 * Design — plain factory function (not a class, not a singleton):
 * - Each call produces a fresh provider instance with independent state.
 * - The caller (ConversationServiceProvider) decides lifetime.
 * - Trivial to test: pass any LLMConfig, assert the returned type.
 * - Adding a provider requires only a new import and a new case here.
 *   No UI, hook, service, or other factory code changes.
 *
 * The desktop application supports exactly two providers:
 *
 *   "mock"  — Development and testing. No network calls.
 *   "apim"  — Production. Routes through Azure API Management.
 *
 * The desktop application never imports or instantiates vendor-specific
 * LLM SDKs. All vendor concerns (model selection, routing, credentials)
 * are encapsulated behind APIM.
 */
export function createLLMProvider(config: LLMConfig): LLMProvider {
  switch (config.provider) {
    case "mock":
      return new MockProvider();

    case "apim": {
      if (!config.apim) {
        throw new Error(
          'LLM_CONFIG.apim must be provided when provider is "apim". ' +
            "Supply endpoint and subscriptionKey from environment configuration."
        );
      }
      return new APIMProvider(config.apim);
    }

    default:
      // Exhaustive check: TypeScript reports an error here if a new
      // LLMProviderKey is added to config/ai.ts without a matching case.
      return assertNever(config.provider);
  }
}

function assertNever(value: never): never {
  throw new Error(`Unhandled LLM provider key: "${String(value)}"`);
}
