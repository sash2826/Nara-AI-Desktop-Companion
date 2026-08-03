import { Monitor, Sun, Moon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ThemeMode } from "@/types/theme";

interface GeneralSettingsProps {
  theme: ThemeMode;
  onThemeChange: (theme: ThemeMode) => void;
}

const THEME_OPTIONS: { value: ThemeMode; label: string; icon: typeof Monitor }[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

export function GeneralSettings({ theme, onThemeChange }: GeneralSettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Appearance</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Choose how the application looks. System follows your OS preference.
        </p>

        <div className="mt-3 flex gap-2">
          {THEME_OPTIONS.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              type="button"
              onClick={() => onThemeChange(value)}
              aria-pressed={theme === value}
              className={cn(
                "flex flex-1 flex-col items-center gap-2 rounded-lg border p-3 text-xs font-medium transition-colors",
                theme === value
                  ? "border-ring bg-accent text-foreground ring-1 ring-ring"
                  : "border-border bg-background text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              )}
            >
              <Icon size={16} strokeWidth={1.5} />
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-border bg-muted/30 p-4">
        <p className="text-xs text-muted-foreground">
          Additional general settings (language, notifications, startup behaviour) will be added in
          a future update.
        </p>
      </div>
    </div>
  );
}
