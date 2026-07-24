import { ThemeProvider } from "@/providers/ThemeProvider";

function App() {
  return (
    <ThemeProvider>
      <div className="flex-col-fill bg-background text-foreground">
        <main className="flex-col-fill items-center justify-center">
          <p className="text-muted-foreground text-sm">Enterprise AI Companion</p>
        </main>
      </div>
    </ThemeProvider>
  );
}

export default App;
