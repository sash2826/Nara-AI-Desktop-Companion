import { useCallback, useEffect } from "react";
import { useWorkspaceStore } from "@/store/workspaceStore";
import { workspaceService } from "@/services/workspace/WorkspaceService";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

export function useWorkspace() {
  // Individual selectors — each re-renders only when its own slice changes
  const folders = useWorkspaceStore((s) => s.folders);
  const watcherStatus = useWorkspaceStore((s) => s.watcherStatus);
  const watcherLoading = useWorkspaceStore((s) => s.watcherLoading);
  const watcherError = useWorkspaceStore((s) => s.watcherError);
  const documents = useWorkspaceStore((s) => s.documents);
  const documentsLoading = useWorkspaceStore((s) => s.documentsLoading);
  const documentsError = useWorkspaceStore((s) => s.documentsError);
  const filter = useWorkspaceStore((s) => s.filter);
  const sort = useWorkspaceStore((s) => s.sort);
  const activeTab = useWorkspaceStore((s) => s.activeTab);
  const setActiveTab = useWorkspaceStore((s) => s.setActiveTab);
  const setFilter = useWorkspaceStore((s) => s.setFilter);
  const setSort = useWorkspaceStore((s) => s.setSort);
  const resetFilter = useWorkspaceStore((s) => s.resetFilter);

  // Use getState() inside async callbacks so they don't capture a stale store
  // reference and don't need the store in their dependency arrays.
  const loadFolders = useCallback(async () => {
    if (!IS_TAURI) return;
    const { setWatcherLoading, setWatcherError, setFolders, setWatcherStatus } =
      useWorkspaceStore.getState();
    setWatcherLoading(true);
    setWatcherError(null);
    try {
      const [fetchedFolders, status] = await Promise.all([
        workspaceService.listFolders(),
        workspaceService.getWatcherStatus(),
      ]);
      setFolders(fetchedFolders);
      setWatcherStatus(status);
    } catch (err) {
      setWatcherError(err instanceof Error ? err.message : "Failed to load folders");
    } finally {
      useWorkspaceStore.getState().setWatcherLoading(false);
    }
  }, []);

  const loadDocuments = useCallback(async (workspacePath?: string) => {
    if (!IS_TAURI) return;
    const { setDocumentsLoading, setDocumentsError, setDocuments } = useWorkspaceStore.getState();
    setDocumentsLoading(true);
    setDocumentsError(null);
    try {
      const docs = await workspaceService.listDocuments(workspacePath);
      setDocuments(docs);
    } catch (err) {
      setDocumentsError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      useWorkspaceStore.getState().setDocumentsLoading(false);
    }
  }, []);

  const addFolder = useCallback(async (path: string) => {
    if (!IS_TAURI) return;
    const folder = await workspaceService.addFolder(path);
    const { addFolder: storeAdd, setWatcherStatus } = useWorkspaceStore.getState();
    storeAdd(folder);
    const status = await workspaceService.getWatcherStatus();
    setWatcherStatus(status);
    return folder;
  }, []);

  const removeFolder = useCallback(async (folderId: string) => {
    if (!IS_TAURI) return;
    await workspaceService.removeFolder(folderId);
    const { removeFolder: storeRemove, setWatcherStatus } = useWorkspaceStore.getState();
    storeRemove(folderId);
    const status = await workspaceService.getWatcherStatus();
    setWatcherStatus(status);
  }, []);

  const indexFolder = useCallback(async (workspacePath: string): Promise<string> => {
    return workspaceService.indexFolder(workspacePath);
  }, []);

  // Stable deps — loadFolders identity never changes, so this runs exactly once
  useEffect(() => {
    void loadFolders();
  }, [loadFolders]);

  return {
    folders,
    watcherStatus,
    watcherLoading,
    watcherError,
    documents,
    documentsLoading,
    documentsError,
    filter,
    sort,
    activeTab,
    setActiveTab,
    setFilter,
    setSort,
    resetFilter,
    loadFolders,
    loadDocuments,
    addFolder,
    removeFolder,
    indexFolder,
  };
}
