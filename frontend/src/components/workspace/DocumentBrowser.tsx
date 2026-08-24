import { useCallback, useEffect, useMemo } from "react";
import { Loader2, FileSearch, Trash2, Check, Minus, X } from "lucide-react";
import { DocumentFilters } from "./DocumentFilters";
import { DocumentRow } from "./DocumentRow";
import { useWorkspace } from "@/hooks/useWorkspace";
import { useWorkspaceStore } from "@/store/workspaceStore";
import type { IndexedDocument } from "@/types/workspace";

function folderName(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).pop() ?? path;
}

function applyFiltersAndSort(
  docs: IndexedDocument[],
  search: string,
  extension: string | null,
  sortKey: string,
  sortDir: string
): IndexedDocument[] {
  let result = docs;

  if (extension) {
    result = result.filter((d) => d.file_path.toLowerCase().endsWith(extension));
  }

  if (search) {
    const lower = search.toLowerCase();
    result = result.filter((d) => d.file_path.toLowerCase().includes(lower));
  }

  result = [...result].sort((a, b) => {
    let av: string | number = a[sortKey as keyof IndexedDocument] as string | number;
    let bv: string | number = b[sortKey as keyof IndexedDocument] as string | number;
    if (typeof av === "string") av = av.toLowerCase();
    if (typeof bv === "string") bv = bv.toLowerCase();
    const cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return sortDir === "asc" ? cmp : -cmp;
  });

  return result;
}

export function DocumentBrowser() {
  const {
    documents,
    documentsLoading,
    documentsError,
    filter,
    sort,
    selectedFolderPath,
    setSelectedFolder,
    setFilter,
    setSort,
    resetFilter,
    loadDocuments,
  } = useWorkspace();

  const selectedDocumentIds = useWorkspaceStore((s) => s.selectedDocumentIds);
  const toggleDocumentSelection = useWorkspaceStore((s) => s.toggleDocumentSelection);
  const selectAllDocuments = useWorkspaceStore((s) => s.selectAllDocuments);
  const clearDocumentSelection = useWorkspaceStore((s) => s.clearDocumentSelection);
  const pendingDelete = useWorkspaceStore((s) => s.pendingDelete);
  const countdown = useWorkspaceStore((s) => s.deleteCountdown);
  const startDelete = useWorkspaceStore((s) => s.startDelete);
  const undoDelete = useWorkspaceStore((s) => s.undoDelete);

  const handleSingleDeleteRequested = useCallback(
    (documentId: string) => startDelete([documentId]),
    [startDelete]
  );

  const handleBulkDelete = useCallback(() => {
    if (selectedDocumentIds.size === 0) return;
    startDelete(Array.from(selectedDocumentIds));
  }, [selectedDocumentIds, startDelete]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  const filtered = useMemo(() => {
    const scoped = selectedFolderPath
      ? documents.filter((d) => d.file_path.startsWith(selectedFolderPath))
      : documents;
    return applyFiltersAndSort(scoped, filter.search, filter.extension, sort.key, sort.direction);
  }, [documents, selectedFolderPath, filter, sort]);

  const scopedTotal = useMemo(() => {
    return selectedFolderPath
      ? documents.filter((d) => d.file_path.startsWith(selectedFolderPath)).length
      : documents.length;
  }, [documents, selectedFolderPath]);

  const filteredIds = useMemo(() => filtered.map((d) => d.id), [filtered]);
  const selectedCount = selectedDocumentIds.size;
  const allSelected =
    filteredIds.length > 0 && filteredIds.every((id) => selectedDocumentIds.has(id));
  const someSelected = selectedCount > 0 && !allSelected;

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      clearDocumentSelection();
    } else {
      selectAllDocuments(filteredIds);
    }
  }, [allSelected, filteredIds, clearDocumentSelection, selectAllDocuments]);

  if (documentsLoading) {
    return (
      <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
        <Loader2 size={16} className="animate-spin" />
        <span className="text-sm">Loading documents…</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Indexed Documents</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          All files that have been indexed and are available for search.
        </p>
      </div>

      {selectedFolderPath && (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <span>Scoped to</span>
          <span className="font-medium text-foreground">{folderName(selectedFolderPath)}</span>
          <button
            onClick={() => setSelectedFolder(null)}
            className="inline-flex items-center gap-0.5 rounded px-1 py-0.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <X size={11} strokeWidth={1.5} />
            Clear
          </button>
        </div>
      )}

      {documentsError && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {documentsError}
        </p>
      )}

      {/* Undo banner */}
      {pendingDelete && (
        <div
          className="flex items-center justify-between rounded-lg px-3 py-2.5"
          style={{
            border: "1px solid hsl(var(--warning) / 0.5)",
            background: "hsl(var(--warning) / 0.12)",
          }}
        >
          <span className="text-xs font-medium" style={{ color: "hsl(var(--warning))" }}>
            Deleting {pendingDelete.docs.length} document
            {pendingDelete.docs.length !== 1 ? "s" : ""}… {countdown}s
          </span>
          <button
            onClick={undoDelete}
            className="rounded-md px-3 py-1 text-xs font-semibold hover:opacity-90"
            style={{
              background: "hsl(var(--warning))",
              color: "hsl(var(--warning-foreground))",
            }}
          >
            Undo
          </button>
        </div>
      )}

      <DocumentFilters
        filter={filter}
        sort={sort}
        onFilterChange={setFilter}
        onSortChange={setSort}
        onReset={resetFilter}
        totalCount={scopedTotal}
        filteredCount={filtered.length}
      />

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-10 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted">
            <FileSearch size={20} className="text-muted-foreground" strokeWidth={1.5} />
          </div>
          <p className="text-sm text-muted-foreground">
            {documents.length === 0
              ? "No documents indexed yet."
              : "No documents match your filters."}
          </p>
          {documents.length === 0 && (
            <p className="text-xs text-muted-foreground">Add a watched folder to start indexing.</p>
          )}
        </div>
      ) : (
        <div className="space-y-1.5">
          {/* Selection header + bulk toolbar */}
          <div className="flex items-center justify-between px-1 pb-1">
            {/* Select-all checkbox */}
            <button
              onClick={handleSelectAll}
              aria-label={allSelected ? "Deselect all" : "Select all"}
              className="flex items-center gap-2 rounded-md px-1 py-0.5 text-xs text-muted-foreground hover:text-foreground"
            >
              <span
                className={`flex h-4 w-4 items-center justify-center rounded border transition-colors ${
                  allSelected
                    ? "border-primary bg-primary text-primary-foreground"
                    : someSelected
                      ? "border-primary bg-primary/20 text-primary"
                      : "border-border bg-background"
                }`}
              >
                {allSelected && <Check size={10} strokeWidth={3} />}
                {someSelected && <Minus size={10} strokeWidth={3} />}
              </span>
              {selectedCount > 0 ? `${selectedCount} selected` : "Select all"}
            </button>

            {/* Bulk delete toolbar — visible when anything is selected */}
            {selectedCount > 0 && (
              <div className="flex items-center gap-2">
                <button
                  onClick={clearDocumentSelection}
                  className="rounded-md px-2 py-0.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  Deselect
                </button>
                <button
                  onClick={handleBulkDelete}
                  className="flex items-center gap-1.5 rounded-md bg-destructive px-2.5 py-1 text-xs font-medium text-destructive-foreground hover:bg-destructive/90"
                >
                  <Trash2 size={11} strokeWidth={2} />
                  Delete {selectedCount}
                </button>
              </div>
            )}
          </div>

          {filtered.map((doc) => (
            <DocumentRow
              key={doc.id}
              document={doc}
              onDeleteRequested={handleSingleDeleteRequested}
              isSelected={selectedDocumentIds.has(doc.id)}
              onToggleSelect={toggleDocumentSelection}
            />
          ))}
        </div>
      )}
    </div>
  );
}
