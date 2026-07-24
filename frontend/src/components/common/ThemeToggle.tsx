import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";
import { cn } from "@/lib/utils";
import type { ThemeMode } from "@/types/theme";

const MODES: { value: ThemeMode; icon: typeof Sun; label: string }[] = [
  { value: "light", icon: Sun, label: "Light" },
  { value: "dark", icon: Moon, label: "Dark" },
  { value: "system", icon: Monitor, label: "System" },
];

interface ThemeToggleProps {
  className?: string;
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();

  return (
    <div
      className={cn("flex items-center rounded-lg border border-border bg-muted p-0.5", className)}
      role="group"
      aria-label="Select theme"
    >
      {MODES.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          aria-label={label}
          aria-pressed={theme === value}
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded-md transition-colors duration-fast",
            theme === value
              ? "bg-background text-foreground shadow-elevation-1"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Icon size={13} strokeWidth={2} />
        </button>
      ))}
    </div>
  );
}
