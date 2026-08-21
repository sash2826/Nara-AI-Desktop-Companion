import type { WatchedFolder, IndexedDocument } from "@/types/workspace";

export interface FolderTreeNode {
  path: string;
  name: string;
  /** Total indexed files under this folder, including subfolders. */
  documentCount: number;
  children: FolderTreeNode[];
  /** Present only for watched root folders; absent for derived subfolders. */
  watchedFolder?: WatchedFolder;
}

function separatorFor(path: string): string {
  return path.includes("\\") ? "\\" : "/";
}

/** Directory segments between the root and the document itself (excludes the filename). */
function relativeDirSegments(root: string, filePath: string): string[] {
  const rel = filePath.slice(root.length).replace(/^[\\/]+/, "");
  const parts = rel.split(/[\\/]/).filter(Boolean);
  return parts.slice(0, -1);
}

function findOrCreateChild(parent: FolderTreeNode, name: string, path: string): FolderTreeNode {
  let child = parent.children.find((c) => c.name === name);
  if (!child) {
    child = { path, name, documentCount: 0, children: [] };
    parent.children.push(child);
  }
  return child;
}

/** Builds a folder tree from watched roots plus subfolders derived from document paths. */
export function buildFolderTree(
  folders: WatchedFolder[],
  documents: IndexedDocument[]
): FolderTreeNode[] {
  const roots: FolderTreeNode[] = folders.map((f) => ({
    path: f.path,
    name: f.path.split(/[\\/]/).filter(Boolean).pop() ?? f.path,
    documentCount: 0,
    children: [],
    watchedFolder: f,
  }));

  for (const doc of documents) {
    const root = roots.find((r) => doc.file_path.startsWith(r.path));
    if (!root) continue;

    root.documentCount += 1;

    const sep = separatorFor(root.path);
    let current = root;
    let currentPath = root.path.replace(/[\\/]+$/, "");
    for (const segment of relativeDirSegments(root.path, doc.file_path)) {
      currentPath = `${currentPath}${sep}${segment}`;
      current = findOrCreateChild(current, segment, currentPath);
      current.documentCount += 1;
    }
  }

  const sortRecursively = (node: FolderTreeNode) => {
    node.children.sort((a, b) => a.name.localeCompare(b.name));
    node.children.forEach(sortRecursively);
  };
  roots.forEach(sortRecursively);

  // Protected folders (Downloads) are pinned to the top among roots.
  roots.sort(
    (a, b) => Number(!!b.watchedFolder?.is_protected) - Number(!!a.watchedFolder?.is_protected)
  );

  return roots;
}

/** Flattens a tree into a single list (pre-order), useful for path-based lookups. */
export function flattenFolderTree(nodes: FolderTreeNode[]): FolderTreeNode[] {
  const result: FolderTreeNode[] = [];
  const walk = (list: FolderTreeNode[]) => {
    for (const node of list) {
      result.push(node);
      walk(node.children);
    }
  };
  walk(nodes);
  return result;
}

/** Finds the most specific (deepest/longest-path) node that targetPath falls under. */
export function findDeepestMatch(
  flatNodes: FolderTreeNode[],
  targetPath: string
): FolderTreeNode | null {
  let best: FolderTreeNode | null = null;
  for (const node of flatNodes) {
    if (targetPath === node.path || targetPath.startsWith(node.path)) {
      if (!best || node.path.length > best.path.length) best = node;
    }
  }
  return best;
}
