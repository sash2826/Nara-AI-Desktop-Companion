import { useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { useConversationStore } from "@/store/conversationStore";
import { useNavigationStore } from "@/store/navigationStore";

interface OrbHandoffPayload {
  query: string;
  response: string;
}

/**
 * Invisible component mounted in the main window.
 * Listens for the "orb-handoff" event emitted when the user clicks
 * "Open in EAC" in the orb overlay, then injects the Q&A pair into
 * the conversation store and navigates to the Chat page.
 */
export function OrbHandoffListener() {
  const addMessage = useConversationStore((s) => s.addMessage);
  const setActiveItem = useNavigationStore((s) => s.setActiveItem);

  useEffect(() => {
    // Use a cancelled flag so that if React StrictMode unmounts before the
    // async listen() resolves, we immediately unlisten the dangling handler
    // rather than leaving two listeners active (which causes duplicate messages).
    let cancelled = false;
    let unlisten: (() => void) | null = null;

    listen<OrbHandoffPayload>("orb-handoff", (event) => {
      const { query, response } = event.payload;
      if (!query || !response) return;

      addMessage("user", query, "complete");
      addMessage("assistant", response, "complete");
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
  }, [addMessage, setActiveItem]);

  return null;
}
