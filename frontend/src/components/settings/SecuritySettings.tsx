import { useState, useEffect } from "react";
import { KeyRound, Eye, EyeOff, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { IPCClient } from "@/services/ipc/IPCClient";
import { useSettingsStore } from "@/store/settingsStore";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

export function SecuritySettings() {
  const [key, setKey] = useState("");
  const [visible, setVisible] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const bumpApiKeyVersion = useSettingsStore((s) => s.bumpApiKeyVersion);

  // Pre-populate from keychain on mount.
  useEffect(() => {
    if (!IS_TAURI) return;
    IPCClient.loadCredential("eac", "apim-key")
      .then((stored) => {
        if (stored) setKey(stored);
      })
      .catch(() => undefined);
  }, []);

  async function handleSave() {
    if (!IS_TAURI || !key.trim()) return;
    setSaving(true);
    try {
      await IPCClient.storeCredential("eac", "apim-key", key.trim());
      bumpApiKeyVersion();
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Security</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Enter your APIM subscription key. It is stored in the Windows Credential Manager and never
          committed to the repository.
        </p>
      </div>

      <section className="space-y-3">
        <div>
          <p className="text-xs font-medium text-foreground">APIM Subscription Key</p>
          <p className="text-xs text-muted-foreground">
            Authorises LLM calls to the Volvo GenAI Hub.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <KeyRound
              size={13}
              className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
            />
            <Input
              type={visible ? "text" : "password"}
              value={key}
              onChange={(e) => {
                setKey(e.target.value);
                setSaved(false);
              }}
              placeholder="Paste your subscription key…"
              className="pl-8 pr-9 font-mono text-xs"
              onKeyDown={(e) => {
                if (e.key === "Enter") void handleSave();
              }}
            />
            <button
              type="button"
              onClick={() => setVisible((v) => !v)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={visible ? "Hide key" : "Show key"}
            >
              {visible ? <EyeOff size={13} /> : <Eye size={13} />}
            </button>
          </div>

          <Button
            size="sm"
            onClick={() => void handleSave()}
            disabled={saving || !key.trim()}
            className="gap-1.5 shrink-0"
          >
            {saving ? (
              <Loader2 size={13} className="animate-spin" />
            ) : saved ? (
              <CheckCircle2 size={13} className="text-green-500" />
            ) : null}
            {saved ? "Saved" : "Save"}
          </Button>
        </div>
      </section>
    </div>
  );
}
