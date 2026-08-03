import { IPCClient, type BackupResult, type BackupSummary } from "@/services/ipc/IPCClient";

/**
 * Orchestrates settings-related side-effects that require IPC.
 *
 * Pure preference persistence is handled by settingsStore directly via
 * localStorage. This service handles operations that need the backend:
 * backup creation, listing, and deletion.
 */
export class SettingsService {
  async createBackup(notes: string = ""): Promise<BackupResult> {
    return IPCClient.createBackup(notes);
  }

  async listBackups(): Promise<BackupSummary[]> {
    return IPCClient.listBackups();
  }
}

export const settingsService = new SettingsService();
