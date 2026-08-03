import { Input } from "@/components/ui/input";
import type { IndexingSettings as IndexingSettingsType } from "@/store/settingsStore";

interface IndexingSettingsProps {
  settings: IndexingSettingsType;
  onChange: (patch: Partial<IndexingSettingsType>) => void;
}

function FieldRow({
  id,
  label,
  hint,
  children,
}: {
  id: string;
  label: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-6">
      <div className="min-w-0 flex-1">
        <label htmlFor={id} className="text-xs font-medium text-foreground">
          {label}
        </label>
        <p className="text-xs text-muted-foreground">{hint}</p>
      </div>
      <div className="w-28 flex-shrink-0">{children}</div>
    </div>
  );
}

export function IndexingSettings({ settings, onChange }: IndexingSettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Indexing</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Controls how documents are split and indexed. Changes take effect on the next indexing
          run.
        </p>
      </div>

      <div className="space-y-4">
        <FieldRow
          id="chunk-size"
          label="Chunk size (chars)"
          hint="Target character count per document chunk. Larger chunks preserve more context; smaller chunks improve precision."
        >
          <Input
            id="chunk-size"
            type="number"
            min={200}
            max={8000}
            step={100}
            value={settings.chunkSize}
            onChange={(e) => onChange({ chunkSize: Number(e.target.value) })}
          />
        </FieldRow>

        <FieldRow
          id="chunk-overlap"
          label="Chunk overlap (chars)"
          hint="Character overlap between adjacent chunks. Prevents context loss at boundaries."
        >
          <Input
            id="chunk-overlap"
            type="number"
            min={0}
            max={1000}
            step={50}
            value={settings.chunkOverlap}
            onChange={(e) => onChange({ chunkOverlap: Number(e.target.value) })}
          />
        </FieldRow>

        <FieldRow
          id="max-file-size"
          label="Max file size (KB)"
          hint="Files larger than this will be skipped during indexing."
        >
          <Input
            id="max-file-size"
            type="number"
            min={100}
            max={102_400}
            step={1024}
            value={settings.maxFileSizeKb}
            onChange={(e) => onChange({ maxFileSizeKb: Number(e.target.value) })}
          />
        </FieldRow>

        <div className="flex items-center justify-between gap-6">
          <div className="min-w-0 flex-1">
            <label htmlFor="auto-index" className="text-xs font-medium text-foreground">
              Auto-index on startup
            </label>
            <p className="text-xs text-muted-foreground">
              Re-index all watched folders when the application starts.
            </p>
          </div>
          <input
            id="auto-index"
            type="checkbox"
            checked={settings.autoIndexOnStartup}
            onChange={(e) => onChange({ autoIndexOnStartup: e.target.checked })}
            className="h-4 w-4 rounded border-border accent-primary"
          />
        </div>
      </div>
    </div>
  );
}
