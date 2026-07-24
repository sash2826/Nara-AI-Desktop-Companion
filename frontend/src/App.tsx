import { ThemeProvider } from "@/providers/ThemeProvider";
import { LayoutProvider } from "@/providers/LayoutProvider";
import { AppShell } from "@/layouts/AppShell";

function App() {
  return (
    <ThemeProvider>
      <LayoutProvider>
        <AppShell />
      </LayoutProvider>
    </ThemeProvider>
  );
}

export default App;
