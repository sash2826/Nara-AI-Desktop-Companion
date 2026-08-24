import { create } from "zustand";
import { IPCClient } from "@/services/ipc/IPCClient";
import type {
  WatchedFolder,
  WatcherStatus,
  IndexedDocument,
  DocumentFilter,
  DocumentSort,
} from "@/types/workspace";

export interface PendingDelete {
  ids: string[];
  docs: IndexedDocument[];
}

// Module-level timers — not tied to any component lifecycle.
let _deleteTimer: ReturnType<typeof setTimeout> | null = null;
let _countdownInterval: ReturnType<typeof setInterval> | null = null;

function _clearDeleteTimers() {
  if (_deleteTimer !== null) {
    clearTimeout(_deleteTimer);
    _deleteTimer = null;
  }
  if (_countdownInterval !== null) {
    clearInterval(_countdownInterval);
    _countdownInterval = null;
  }
}

const DEFAULT_FILTER: DocumentFilter = {
  workspacePath: null,
  extension: null,
  search: "",
};

const DEFAULT_SORT: DocumentSort = {
  key: "indexed_at",
  direction: "desc",
};

interface WorkspaceStore {
  // Watcher
  folders: WatchedFolder[];
  watcherStatus: WatcherStatus | null;
  watcherLoading: boolean;
  watcherError: string | null;

  // Documents
  documents: IndexedDocument[];
  documentsLoading: boolean;
  documentsError: string | null;
  filter: DocumentFilter;
  sort: DocumentSort;

  // Active tab
  activeTab: "explorer" | "indexing" | "errors" | "organise";

  // Explorer folder scope (null = all files; supports both watched roots and derived subfolders)
  selectedFolderPath: string | null;

  // Error badge
  errorCount: number;

  // Watcher actions
  setFolders: (folders: WatchedFolder[]) => void;
  addFolder: (folder: WatchedFolder) => void;
  removeFolder: (folderId: string) => void;
  setWatcherStatus: (status: WatcherStatus) => void;
  setWatcherLoading: (loading: boolean) => void;
  setWatcherError: (error: string | null) => void;

  // Document actions
  setDocuments: (documents: IndexedDocument[]) => void;
  setDocumentsLoading: (loading: boolean) => void;
  setDocumentsError: (error: string | null) => void;
  setFilter: (filter: Partial<DocumentFilter>) => void;
  setSort: (sort: DocumentSort) => void;
  resetFilter: () => void;

  // Document selection
  selectedDocumentIds: Set<string>;
  toggleDocumentSelection: (id: string) => void;
  selectAllDocuments: (ids: string[]) => void;
  clearDocumentSelection: () => void;

  // Pending delete (undo window)
  pendingDelete: PendingDelete | null;
  deleteCountdown: number;
  startDelete: (ids: string[]) => void;
  undoDelete: () => void;

  // Tab
  setActiveTab: (tab: "explorer" | "indexing" | "errors" | "organise") => void;

  // Explorer folder scope
  setSelectedFolder: (folderPath: string | null) => void;

  // Error badge
  setErrorCount: (count: number) => void;
}

export const useWorkspaceStore = create<WorkspaceStore>((set) => ({
  folders: [],
  watcherStatus: null,
  watcherLoading: false,
  watcherError: null,

  documents: [],
  documentsLoading: false,
  documentsError: null,
  filter: DEFAULT_FILTER,
  sort: DEFAULT_SORT,

  activeTab: "explorer",
  selectedFolderPath: null,
  errorCount: 0,
  selectedDocumentIds: new Set<string>(),
  pendingDelete: null,
  deleteCountdown: 0,

  setFolders: (folders) => set({ folders }),
  addFolder: (folder) => set((state) => ({ folders: [...state.folders, folder] })),
  removeFolder: (folderId) =>
    set((state) => ({ folders: state.folders.filter((f) => f.id !== folderId) })),
  setWatcherStatus: (watcherStatus) => set({ watcherStatus }),
  setWatcherLoading: (watcherLoading) => set({ watcherLoading }),
  setWatcherError: (watcherError) => set({ watcherError }),

  setDocuments: (documents) => set({ documents }),
  setDocumentsLoading: (documentsLoading) => set({ documentsLoading }),
  setDocumentsError: (documentsError) => set({ documentsError }),
  setFilter: (filter) => set((state) => ({ filter: { ...state.filter, ...filter } })),
  setSort: (sort) => set({ sort }),
  resetFilter: () => set({ filter: DEFAULT_FILTER }),

  toggleDocumentSelection: (id) =>
    set((state) => {
      const next = new Set(state.selectedDocumentIds);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { selectedDocumentIds: next };
    }),
  selectAllDocuments: (ids) => set({ selectedDocumentIds: new Set(ids) }),
  clearDocumentSelection: () => set({ selectedDocumentIds: new Set() }),

  setActiveTab: (activeTab) => set({ activeTab }),
  setSelectedFolder: (selectedFolderPath) => set({ selectedFolderPath }),
  setErrorCount: (errorCount) => set({ errorCount }),

  startDelete: (ids) => {
    const { documents } = useWorkspaceStore.getState();
    if (ids.length === 0) return;
    const docsToRemove = documents.filter((d) => ids.includes(d.id));
    const remaining = documents.filter((d) => !ids.includes(d.id));
    _clearDeleteTimers();

    set({
      documents: remaining,
      selectedDocumentIds: new Set(),
      pendingDelete: { ids, docs: docsToRemove },
      deleteCountdown: 5,
    });

    _countdownInterval = setInterval(() => {
      set((s) => {
        const next = Math.max(0, s.deleteCountdown - 1);
        return { deleteCountdown: next };
      });
    }, 1000);

    _deleteTimer = setTimeout(() => {
      _clearDeleteTimers();
      set({ pendingDelete: null, deleteCountdown: 0 });
      void IPCClient.bulkDeleteDocuments(ids);
    }, 5000);
  },

  undoDelete: () => {
    const { pendingDelete } = useWorkspaceStore.getState();
    if (!pendingDelete) return;
    _clearDeleteTimers();
    const currentDocs = useWorkspaceStore.getState().documents;
    const existingIds = new Set(currentDocs.map((d) => d.id));
    const toRestore = pendingDelete.docs.filter((d) => !existingIds.has(d.id));
    set({ documents: [...currentDocs, ...toRestore], pendingDelete: null, deleteCountdown: 0 });
  },
}));
