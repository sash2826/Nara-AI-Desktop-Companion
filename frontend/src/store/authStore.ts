import { create } from "zustand";

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  userDisplayName: string | null;
  tokenExpiresAt: number | null;
}

interface AuthActions {
  setAuthenticated: (value: boolean, displayName?: string | null) => void;
  setLoading: (value: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState: AuthState = {
  isAuthenticated: false,
  isLoading: true,
  error: null,
  userDisplayName: null,
  tokenExpiresAt: null,
};

export const useAuthStore = create<AuthState & AuthActions>()((set) => ({
  ...initialState,

  setAuthenticated: (value, displayName = null) =>
    set({ isAuthenticated: value, userDisplayName: displayName, isLoading: false, error: null }),

  setLoading: (value) => set({ isLoading: value }),

  setError: (error) => set({ error, isLoading: false }),

  reset: () => set({ ...initialState, isLoading: false }),
}));
