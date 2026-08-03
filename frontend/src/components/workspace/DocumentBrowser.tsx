import { useEffect, useMemo } from "react";
import { Loader2, FileSearch } from "lucide-react";
import { DocumentFilters } from "./DocumentFilters";
import { DocumentRow } from "./DocumentRow";
import { useWorkspace } from "@/hooks/useWorkspace";
import type { IndexedDocument } from "@/types/workspace";

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
    setFilter,
    setSort,
    resetFilter,
    loadDocuments,
  } = useWorkspace();

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  const filtered = useMemo(
    () => applyFiltersAndSort(documents, filter.search, filter.extension, sort.key, sort.direction),
    [documents, filter, sort]
  );

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

      {documentsError && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {documentsError}
        </p>
      )}

      <DocumentFilters
        filter={filter}
        sort={sort}
        onFilterChange={setFilter}
        onSortChange={setSort}
        onReset={resetFilter}
        totalCount={documents.length}
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
          {filtered.map((doc) => (
            <DocumentRow key={doc.id} document={doc} />
          ))}
        </div>
      )}
    </div>
  );
}
