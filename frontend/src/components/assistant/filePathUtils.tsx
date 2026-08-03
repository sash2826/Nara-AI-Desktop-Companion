import type { ReactNode } from "react";
import { FilePathChip } from "./FilePathChip";

// Matches Windows absolute paths (C:\... or C:/...) and Unix absolute paths
// (/home/...). Stops at whitespace and common markdown/punctuation delimiters.
const FILE_PATH_REGEX = /([A-Za-z]:[/\\][^\s"'`*[\](){}|<>]+|\/[^\s"'`*[\](){}|<>]{2,})/g;

/**
 * Splits a text string on absolute file paths and returns a React node array
 * with plain text segments and FilePathChip elements interleaved.
 *
 * Used by the ReactMarkdown `p` renderer so paths in assistant messages
 * become clickable "Open" buttons rather than plain text.
 */
export function renderWithFilePaths(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  FILE_PATH_REGEX.lastIndex = 0;
  while ((match = FILE_PATH_REGEX.exec(text)) !== null) {
    const [rawPath] = match;
    const start = match.index;

    if (start > lastIndex) {
      parts.push(text.slice(lastIndex, start));
    }

    parts.push(<FilePathChip key={start} path={rawPath} />);
    lastIndex = start + rawPath.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}
