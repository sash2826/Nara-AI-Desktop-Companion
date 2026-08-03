import { Eye, EyeOff, Info } from "lucide-react";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { AIProviderSettings as AIProviderSettingsType } from "@/store/settingsStore";

interface AIProviderSettingsProps {
  settings: AIProviderSettingsType;
  onChange: (patch: Partial<AIProviderSettingsType>) => void;
}

function FieldLabel({ htmlFor, label, hint }: { htmlFor: string; label: string; hint?: string }) {
  return (
    <div className="mb-1.5">
      <label htmlFor={htmlFor} className="text-xs font-medium text-foreground">
        {label}
      </label>
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

export function AIProviderSettings({ settings, onChange }: AIProviderSettingsProps) {
  const [showKey, setShowKey] = useState(false);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-foreground">AI Provider</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Connection settings for the Azure API Management gateway. These values come from your
          environment variables by default.
        </p>
      </div>

      {/* Endpoint */}
      <div>
        <FieldLabel
          htmlFor="apim-endpoint"
          label="APIM Endpoint"
          hint="The full URL of your Azure API Management gateway."
        />
        <Input
          id="apim-endpoint"
          type="url"
          value={settings.endpoint}
          onChange={(e) => onChange({ endpoint: e.target.value })}
          placeholder="https://your-apim.azure-api.net/..."
          className="font-mono text-xs"
        />
      </div>

      {/* Subscription key */}
      <div>
        <FieldLabel
          htmlFor="apim-key"
          label="Subscription Key"
          hint="Your APIM subscription key (api-key header). Stored locally only."
        />
        <div className="relative">
          <Input
            id="apim-key"
            type={showKey ? "text" : "password"}
            value={settings.subscriptionKey}
            onChange={(e) => onChange({ subscriptionKey: e.target.value })}
            placeholder="••••••••••••••••"
            className="pr-9 font-mono text-xs"
          />
          <button
            type="button"
            onClick={() => setShowKey((v) => !v)}
            aria-label={showKey ? "Hide subscription key" : "Show subscription key"}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>
      </div>

      {/* Model */}
      <div>
        <FieldLabel
          htmlFor="apim-model"
          label="Model Deployment ID"
          hint="The model deployment identifier passed in request bodies."
        />
        <Input
          id="apim-model"
          type="text"
          value={settings.model}
          onChange={(e) => onChange({ model: e.target.value })}
          placeholder="gpt-5.4-mini_gb_2026-03-17"
          className="font-mono text-xs"
        />
      </div>

      {/* Advanced — timeout and retries side by side */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <FieldLabel htmlFor="apim-timeout" label="Timeout (ms)" />
          <Input
            id="apim-timeout"
            type="number"
            min={1000}
            max={120_000}
            step={1000}
            value={settings.timeoutMs}
            onChange={(e) => onChange({ timeoutMs: Number(e.target.value) })}
          />
        </div>
        <div>
          <FieldLabel htmlFor="apim-retries" label="Max Retries" />
          <Input
            id="apim-retries"
            type="number"
            min={0}
            max={10}
            value={settings.maxRetries}
            onChange={(e) => onChange({ maxRetries: Number(e.target.value) })}
          />
        </div>
      </div>

      {/* Note about env vars */}
      <div
        className={cn(
          "flex items-start gap-2 rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground"
        )}
      >
        <Info size={13} className="mt-0.5 flex-shrink-0" />
        <span>
          These settings override <code className="font-mono">VITE_APIM_ENDPOINT</code> and{" "}
          <code className="font-mono">VITE_APIM_SUBSCRIPTION_KEY</code> environment variables at
          runtime. Credentials are persisted to localStorage — never sent to any server.
        </span>
      </div>
    </div>
  );
}
