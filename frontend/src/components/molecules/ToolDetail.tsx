import { Badge } from "@/components/primitives/badge"

export function ToolDetail({ input, output, errorDetail }: {
  input: unknown
  output?: unknown
  errorDetail?: string
}) {
  return (
    <div data-testid="tool-detail" className="space-y-2 p-3 text-xs">
      <div>
        <Badge variant="outline" className="mb-1 text-[10px] uppercase text-[var(--chat-fg-subtle)]">Input</Badge>
        <pre data-testid="tool-input-json" className="whitespace-pre-wrap break-all rounded bg-muted/50 p-2 font-mono text-[var(--chat-fg-secondary)]">
          {JSON.stringify(input, null, 2)}
        </pre>
      </div>
      {output !== undefined && (
        <div>
          <Badge variant="outline" className="mb-1 text-[10px] uppercase text-[var(--chat-fg-subtle)]">Output</Badge>
          <pre data-testid="tool-output-json" className="whitespace-pre-wrap break-all rounded bg-muted/50 p-2 font-mono text-[var(--chat-fg-secondary)]">
            {JSON.stringify(output, null, 2)}
          </pre>
        </div>
      )}
      {errorDetail && (
        <div>
          <Badge variant="outline" className="mb-1 text-[10px] uppercase text-[var(--chat-fg-subtle)]">Error</Badge>
          <pre data-testid="tool-error-detail" className="overflow-auto rounded bg-destructive/10 p-2 font-mono text-destructive">
            {errorDetail}
          </pre>
        </div>
      )}
    </div>
  )
}
