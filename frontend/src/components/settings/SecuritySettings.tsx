import { ShieldCheck, ShieldOff, LogOut, Loader2, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

export function SecuritySettings() {
  const { isAuthenticated, isLoading, userDisplayName, login, logout } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Security</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Authentication uses Volvo Group single sign-on (Azure AD). Your access token is stored in
          Windows Credential Manager and refreshed automatically.
        </p>
      </div>

      {/* Azure AD session */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-foreground">Volvo Account</p>
            <p className="text-xs text-muted-foreground">
              Authorises LLM and APIM access via Azure AD bearer token.
            </p>
          </div>
          <AuthBadge isAuthenticated={isAuthenticated} isLoading={isLoading} />
        </div>

        {isAuthenticated ? (
          <div className="flex items-center gap-3">
            {userDisplayName && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <User size={12} />
                <span>{userDisplayName}</span>
              </div>
            )}
            <Button
              size="sm"
              variant="ghost"
              onClick={() => void logout()}
              className={cn("gap-1.5 text-muted-foreground hover:text-foreground")}
            >
              <LogOut size={13} />
              Sign out
            </Button>
          </div>
        ) : (
          <Button size="sm" onClick={() => void login()} disabled={isLoading} className="gap-1.5">
            {isLoading ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />}
            {isLoading ? "Opening browser…" : "Sign in with Microsoft"}
          </Button>
        )}
      </section>
    </div>
  );
}

function AuthBadge({
  isAuthenticated,
  isLoading,
}: {
  isAuthenticated: boolean;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
        Checking…
      </span>
    );
  }
  if (isAuthenticated) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
        <ShieldCheck size={11} />
        Signed in
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
      <ShieldOff size={11} />
      Not signed in
    </span>
  );
}
