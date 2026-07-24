import type { AIConfig } from "@/config/ai";
import type { AIProvider } from "@/services/ai/AIProvider";
import { MockProvider } from "@/services/ai/MockProvider";

/**
 * Creates and returns the active AI provider based on the supplied configuration.
 *
 * Design — plain factory function (not a class, not a singleton):
 * - Each call creates a fresh provider instance with no shared state.
 * - The caller (ConversationServiceProvider) decides lifetime and owns the ref.
 * - Trivial to test: pass any AIConfig, assert the returned type.
 * - Adding a new provider requires only a new case here — nothing else changes.
 *
 * Future providers are added by importing their class and adding a case:
 *
 *   case "openai":   return new OpenAIProvider(config);
 *   case "claude":   return new ClaudeProvider(config);
 *   case "ollama":   return new OllamaProvider(config);
 *   case "azure-openai": return new AzureOpenAIProvider(config);
 *   case "gemini":   return new GeminiProvider(config);
 *   case "openrouter": return new OpenRouterProvider(config);
 */
export function createAIProvider(config: AIConfig): AIProvider {
  switch (config.provider) {
    case "mock":
      return new MockProvider();

    default:
      // Exhaustive check: TypeScript will error here if a new AIProviderKey
      // is added to config/ai.ts without a corresponding case above.
      throw new Error(
        `AI provider "${config.provider}" is not yet implemented. ` +
          `Add a case to ProviderFactory and implement the AIProvider interface.`
      );
  }
}
