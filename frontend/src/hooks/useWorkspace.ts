import { useCallback, useEffect } from "react";
import { useWorkspaceStore } from "@/store/workspaceStore";
import { workspaceService } from "@/services/workspace/WorkspaceService";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

export function useWorkspace() {
  const store = useWorkspaceStore();

  const loadFolders = useCallback(async () => {
    if (!IS_TAURI) return;
    store.setWatcherLoading(true);
    store.setWatcherError(null);
    try {
      const [folders, status] = await Promise.all([
        workspaceService.listFolders(),
        workspaceService.getWatcherStatus(),
      ]);
      store.setFolders(folders);
      store.setWatcherStatus(status);
    } catch (err) {
      store.setWatcherError(err instanceof Error ? err.message : "Failed to load folders");
    } finally {
      store.setWatcherLoading(false);
    }
  }, [store]);

  const loadDocuments = useCallback(
    async (workspacePath?: string) => {
      if (!IS_TAURI) return;
      store.setDocumentsLoading(true);
      store.setDocumentsError(null);
      try {
        const docs = await workspaceService.listDocuments(workspacePath);
        store.setDocuments(docs);
      } catch (err) {
        store.setDocumentsError(err instanceof Error ? err.message : "Failed to load documents");
      } finally {
        store.setDocumentsLoading(false);
      }
    },
    [store]
  );

  const addFolder = useCallback(
    async (path: string) => {
      if (!IS_TAURI) return;
      const folder = await workspaceService.addFolder(path);
      store.addFolder(folder);
      // Refresh watcher status after adding
      const status = await workspaceService.getWatcherStatus();
      store.setWatcherStatus(status);
      return folder;
    },
    [store]
  );

  const removeFolder = useCallback(
    async (folderId: string) => {
      if (!IS_TAURI) return;
      await workspaceService.removeFolder(folderId);
      store.removeFolder(folderId);
      const status = await workspaceService.getWatcherStatus();
      store.setWatcherStatus(status);
    },
    [store]
  );

  const indexFolder = useCallback(async (workspacePath: string): Promise<string> => {
    return workspaceService.indexFolder(workspacePath);
  }, []);

  // Load folders and watcher status on mount
  useEffect(() => {
    void loadFolders();
  }, [loadFolders]);

  return {
    folders: store.folders,
    watcherStatus: store.watcherStatus,
    watcherLoading: store.watcherLoading,
    watcherError: store.watcherError,
    documents: store.documents,
    documentsLoading: store.documentsLoading,
    documentsError: store.documentsError,
    filter: store.filter,
    sort: store.sort,
    activeTab: store.activeTab,
    setActiveTab: store.setActiveTab,
    setFilter: store.setFilter,
    setSort: store.setSort,
    resetFilter: store.resetFilter,
    loadFolders,
    loadDocuments,
    addFolder,
    removeFolder,
    indexFolder,
  };
}
