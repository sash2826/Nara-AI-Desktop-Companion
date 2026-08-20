import { useEffect, useCallback } from "react";
import { listen } from "@tauri-apps/api/event";
import { useAuthStore } from "@/store/authStore";
import { IPCClient } from "@/services/ipc/IPCClient";

interface AuthStateEvent {
  is_authenticated: boolean;
  user_display_name?: string | null;
}

/**
 * Primary hook for Azure AD authentication.
 *
 * On first call it checks for a persisted session in the OS keychain (no login
 * screen if the token is still valid). It also listens for the Tauri
 * "auth-state-changed" event so that token refreshes propagate to the UI.
 */
export function useAuth() {
  const {
    isAuthenticated,
    isLoading,
    error,
    userDisplayName,
    setAuthenticated,
    setLoading,
    setError,
    reset,
  } = useAuthStore();

  // Restore session on mount and subscribe to auth-state-changed events.
  useEffect(() => {
    let unlisten: (() => void) | undefined;

    async function init() {
      // Subscribe before calling auth_check so we don't miss an event that fires
      // during the check (e.g. an immediate silent refresh).
      const unlistenFn = await listen<AuthStateEvent>("auth-state-changed", (event) => {
        const { is_authenticated, user_display_name } = event.payload;
        if (is_authenticated) {
          setAuthenticated(true, user_display_name ?? null);
        } else {
          reset();
        }
      });
      unlisten = unlistenFn;

      try {
        const authenticated = await IPCClient.authCheck();
        setAuthenticated(authenticated);
      } catch (err) {
        console.error("[useAuth] auth_check failed:", err);
        setAuthenticated(false);
      }
    }

    void init();
    return () => {
      unlisten?.();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await IPCClient.authLogin();
      // auth-state-changed event will update the store; auth_login resolves
      // only after the token is stored, so we can also set directly.
      setAuthenticated(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    }
  }, [setAuthenticated, setError, setLoading]);

  const logout = useCallback(async () => {
    try {
      await IPCClient.authLogout();
      reset();
    } catch (err) {
      console.error("[useAuth] logout failed:", err);
      reset();
    }
  }, [reset]);

  return { isAuthenticated, isLoading, error, userDisplayName, login, logout };
}
