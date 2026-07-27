import { ThemeProvider } from "@/providers/ThemeProvider";
import { LayoutProvider } from "@/providers/LayoutProvider";
import { ConversationServiceProvider } from "@/providers/ConversationServiceProvider";
import { DesktopPresenceProvider } from "@/providers/DesktopPresenceProvider";
import { AppShell } from "@/layouts/AppShell";
import { OrbLayer } from "@/layouts/OrbLayer";

function App() {
  return (
    <ThemeProvider>
      <LayoutProvider>
        <ConversationServiceProvider>
          <DesktopPresenceProvider>
            <AppShell />
            <OrbLayer />
          </DesktopPresenceProvider>
        </ConversationServiceProvider>
      </LayoutProvider>
    </ThemeProvider>
  );
}

export default App;
