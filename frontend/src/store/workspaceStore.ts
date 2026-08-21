import { create } from "zustand";
import type {
  WatchedFolder,
  WatcherStatus,
  IndexedDocument,
  DocumentFilter,
  DocumentSort,
} from "@/types/workspace";

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
}));
