import { WorkspaceFolderRail } from "./WorkspaceFolderRail";
import { DocumentBrowser } from "./DocumentBrowser";

/** Merged Folders + Documents view: file-explorer rail on the left, searchable document list on the right. */
export function WorkspaceExplorer() {
  return (
    <div className="flex h-full min-h-0">
      <WorkspaceFolderRail />
      <div className="min-w-0 flex-1 overflow-y-auto px-4 py-4">
        <DocumentBrowser />
      </div>
    </div>
  );
}
