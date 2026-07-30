import { ContextEngine, ContextSnapshot } from "./ContextEngine";

const MAX_RECENT_DOCUMENTS = 5;

/**
 * Observes real workspace signals: the most recently recorded active file path
 * and a rolling FIFO list of the last 5 document paths accessed this session.
 *
 * In Phase 01 there is no OS-level file-watcher; callers push paths via
 * `recordActiveFile()` (e.g. from a Tauri file-open event). Phase 03 will
 * wire this up to the full workspace event stream.
 */
export class WorkspaceContextEngine implements ContextEngine {
  private activeFilePath: string | null = null;
  private recentDocuments: string[] = [];

  recordActiveFile(filePath: string): void {
    this.activeFilePath = filePath;

    // Keep the list deduplicated: move the path to the front if already present
    this.recentDocuments = [filePath, ...this.recentDocuments.filter((p) => p !== filePath)].slice(
      0,
      MAX_RECENT_DOCUMENTS
    );
  }

  async getSnapshot(): Promise<ContextSnapshot> {
    const activeProjectFolder = this.activeFilePath
      ? this.deriveProjectFolder(this.activeFilePath)
      : null;

    return {
      activeProjectFolder,
      recentDocuments: [...this.recentDocuments],
      explicitContext: null,
      retrievedContext: null,
    };
  }

  private deriveProjectFolder(filePath: string): string {
    // Return the parent directory of the file path.
    // Works with both forward and back slashes.
    const normalised = filePath.replace(/\\/g, "/");
    const lastSlash = normalised.lastIndexOf("/");
    return lastSlash > 0 ? normalised.slice(0, lastSlash) : normalised;
  }
}
