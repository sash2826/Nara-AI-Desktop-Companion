/**
 * IPCClient — typed wrapper around the Tauri invoke API.
 *
 * All communication between the React frontend and the Rust/Python backend
 * flows through this client. No component or service should call `invoke`
 * directly — this is the single authoritative IPC boundary.
 *
 * Architecture:
 *   React component / hook
 *       │
 *   IPCClient.someCommand()        ← this file
 *       │
 *   invoke("some_command", payload) ← Tauri IPC
 *       │
 *   Tauri Rust command handler
 *       │
 *   HTTP POST to Python sidecar
 *       │
 *   FastAPI handler
 */

import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

// ─── Shared types ─────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: "ok";
}

// ─── Sidecar readiness ────────────────────────────────────────────────────────

/**
 * Returns a promise that resolves with the sidecar port once the backend emits
 * the `sidecar-ready` event. Rejects after `timeoutMs` if the event never fires.
 *
 * Use this in application startup to gate any IPC calls on sidecar readiness.
 */
export function waitForSidecar(timeoutMs = 30_000): Promise<number> {
  return new Promise<number>((resolve, reject) => {
    // Capture the listen promise so we can call unlisten regardless of whether
    // the cleanup runs before or after the listen() promise resolves.
    const listenPromise = listen<number>("sidecar-ready", (event) => {
      clearTimeout(timer);
      listenPromise.then((fn) => fn()).catch(() => {});
      resolve(event.payload);
    });

    const timer = setTimeout(() => {
      listenPromise.then((fn) => fn()).catch(() => {});
      reject(new Error("Sidecar did not become ready within the timeout period."));
    }, timeoutMs);

    listenPromise.catch((err: unknown) => {
      clearTimeout(timer);
      reject(err);
    });
  });
}

// ─── IPCClient ────────────────────────────────────────────────────────────────

/**
 * Calls the `health_check` Tauri command.
 *
 * Returns `{ status: "ok" }` when the Python sidecar is reachable.
 * Throws a string error message if the sidecar is not ready or unreachable.
 */
async function healthCheck(): Promise<HealthResponse> {
  return invoke<HealthResponse>("health_check");
}

export const IPCClient = {
  healthCheck,
} as const;
