import { useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { useConversationStore } from "@/store/conversationStore";
import { useNavigationStore } from "@/store/navigationStore";
import type { CitationMeta } from "@/types/conversation";

interface OrbSource {
  path: string;
  name: string;
}

interface OrbHandoffPayload {
  query: string;
  response: string;
  sources?: OrbSource[];
}

/**
 * Invisible component mounted in the main window.
 * Listens for the "orb-handoff" event emitted when the user clicks
 * "Open in Chat" in the orb overlay, then injects the Q&A pair into
 * the conversation store and navigates to the Chat page.
 *
 * Sources from the orb are mapped to CitationMeta so the existing
 * CitationChip renderer displays them as clickable file chips.
 */
export function OrbHandoffListener() {
  const addMessage = useConversationStore((s) => s.addMessage);
  const updateMessageCitations = useConversationStore((s) => s.updateMessageCitations);
  const setActiveItem = useNavigationStore((s) => s.setActiveItem);

  useEffect(() => {
    // Use a cancelled flag so that if React StrictMode unmounts before the
    // async listen() resolves, we immediately unlisten the dangling handler
    // rather than leaving two listeners active (which causes duplicate messages).
    let cancelled = false;
    let unlisten: (() => void) | null = null;

    listen<OrbHandoffPayload>("orb-handoff", (event) => {
      const { query, response, sources } = event.payload;
      if (!query || !response) return;

      addMessage("user", query, "complete");
      const assistantId = addMessage("assistant", response, "complete");

      if (sources && sources.length > 0) {
        const citations: CitationMeta[] = sources.map((src) => ({
          chunkId: src.path,
          documentPath: src.path,
          chunkIndex: 0,
          rrfScore: 1.0,
        }));
        updateMessageCitations(assistantId, citations);
      }

      setTimeout(() => setActiveItem("chat"), 0);
    }).then((fn) => {
      if (cancelled) {
        fn(); // StrictMode already unmounted — drop this listener immediately
      } else {
        unlisten = fn;
      }
    });

    return () => {
      cancelled = true;
      unlisten?.();
    };
  }, [addMessage, updateMessageCitations, setActiveItem]);

  return null;
}
