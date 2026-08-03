import { IPCClient } from "@/services/ipc/IPCClient";
import type { WatchedFolder, WatcherStatus, IndexedDocument } from "@/types/workspace";

export class WorkspaceService {
  async listFolders(): Promise<WatchedFolder[]> {
    return IPCClient.listWatchedFolders();
  }

  async addFolder(path: string): Promise<WatchedFolder> {
    return IPCClient.addWatchedFolder(path);
  }

  async removeFolder(folderId: string): Promise<void> {
    return IPCClient.removeWatchedFolder(folderId);
  }

  async getWatcherStatus(): Promise<WatcherStatus> {
    return IPCClient.getWatcherStatus();
  }

  async listDocuments(workspacePath?: string): Promise<IndexedDocument[]> {
    return IPCClient.listDocuments(workspacePath);
  }

  async indexFolder(workspacePath: string): Promise<string> {
    const response = await IPCClient.indexWorkspace(workspacePath);
    return response.task_id;
  }
}

export const workspaceService = new WorkspaceService();
