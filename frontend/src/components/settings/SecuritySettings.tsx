import { Eye, EyeOff, ShieldCheck, ShieldOff, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { IPCClient } from "@/services/ipc/IPCClient";
import { cn } from "@/lib/utils";

const KEYCHAIN_SERVICE = "eac";
const KEYCHAIN_KEY = "apim-key";

type KeychainStatus = "loading" | "stored" | "missing" | "error";

export function SecuritySettings() {
  const [status, setStatus] = useState<KeychainStatus>("loading");
  const [draft, setDraft] = useState("");
  const [showDraft, setShowDraft] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: "success" | "error"; text: string } | null>(
    null
  );

  useEffect(() => {
    IPCClient.loadCredential(KEYCHAIN_SERVICE, KEYCHAIN_KEY)
      .then((val) => setStatus(val ? "stored" : "missing"))
      .catch(() => setStatus("error"));
  }, []);

  function clearFeedback() {
    setFeedback(null);
  }

  async function handleSave() {
    const trimmed = draft.trim();
    if (!trimmed) return;
    clearFeedback();
    try {
      await IPCClient.storeCredential(KEYCHAIN_SERVICE, KEYCHAIN_KEY, trimmed);
      setDraft("");
      setStatus("stored");
      setFeedback({ kind: "success", text: "Key saved to OS keychain." });
    } catch (err) {
      setFeedback({ kind: "error", text: String(err) });
    }
  }

  async function handleDelete() {
    clearFeedback();
    try {
      await IPCClient.deleteCredential(KEYCHAIN_SERVICE, KEYCHAIN_KEY);
      setStatus("missing");
      setFeedback({ kind: "success", text: "Key removed from OS keychain." });
    } catch (err) {
      setFeedback({ kind: "error", text: String(err) });
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Security</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Credentials are stored in the OS keychain (Windows Credential Manager). They are never
          written to localStorage, log files, or the application bundle.
        </p>
      </div>

      {/* APIM subscription key */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-foreground">APIM Subscription Key</p>
            <p className="text-xs text-muted-foreground">
              Used as the <code className="font-mono">api-key</code> header for all LLM requests.
            </p>
          </div>
          <KeychainBadge status={status} />
        </div>

        <div className="relative">
          <Input
            id="apim-key-input"
            type={showDraft ? "text" : "password"}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void handleSave();
            }}
            placeholder={
              status === "stored" ? "Enter new key to replace…" : "Enter subscription key…"
            }
            className="pr-9 font-mono text-xs"
            aria-label="APIM subscription key"
          />
          <button
            type="button"
            onClick={() => setShowDraft((v) => !v)}
            aria-label={showDraft ? "Hide key" : "Show key"}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            {showDraft ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>

        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={() => void handleSave()}
            disabled={!draft.trim()}
            className="gap-1.5"
          >
            <ShieldCheck size={13} />
            Save to keychain
          </Button>
          {status === "stored" && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => void handleDelete()}
              className="gap-1.5 text-destructive hover:text-destructive"
            >
              <Trash2 size={13} />
              Remove
            </Button>
          )}
        </div>

        {feedback && (
          <p
            className={cn(
              "text-xs",
              feedback.kind === "success"
                ? "text-green-600 dark:text-green-400"
                : "text-destructive"
            )}
          >
            {feedback.text}
          </p>
        )}
      </section>
    </div>
  );
}

function KeychainBadge({ status }: { status: KeychainStatus }) {
  if (status === "loading") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
        Checking…
      </span>
    );
  }
  if (status === "stored") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
        <ShieldCheck size={11} />
        Stored in OS keychain
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-destructive/10 px-2 py-0.5 text-xs font-medium text-destructive">
        <ShieldOff size={11} />
        Keychain error
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
      <ShieldOff size={11} />
      Not configured
    </span>
  );
}
