import { ThemeProvider } from "@/providers/ThemeProvider";
import { LayoutProvider } from "@/providers/LayoutProvider";
import { ConversationServiceProvider } from "@/providers/ConversationServiceProvider";
import { DesktopPresenceProvider } from "@/providers/DesktopPresenceProvider";
import { AppShell } from "@/layouts/AppShell";
import { GlassPromptContainer } from "@/layouts/GlassPromptContainer";
import { OrbHandoffListener } from "@/components/OrbHandoffListener";
import { AuthGuard } from "@/components/auth/AuthGuard";

function App() {
  return (
    <ThemeProvider>
      <AuthGuard>
        <LayoutProvider>
          <ConversationServiceProvider>
            <DesktopPresenceProvider>
              <OrbHandoffListener />
              <AppShell />
              <GlassPromptContainer />
            </DesktopPresenceProvider>
          </ConversationServiceProvider>
        </LayoutProvider>
      </AuthGuard>
    </ThemeProvider>
  );
}

export default App;
