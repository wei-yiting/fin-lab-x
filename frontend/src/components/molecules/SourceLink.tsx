import { ExternalLink } from "lucide-react"
import { Badge } from "@/components/primitives/badge"

export function SourceLink({ label, url, title, hostname }: {
  label: string
  url: string
  title?: string
  hostname: string
}) {
  return (
    <li data-testid="source-link" data-source-label={label} id={`src-${label}`} className="flex items-center gap-2 rounded-md p-2 hover:bg-muted/50">
      <Badge variant="outline" className="shrink-0 font-mono text-xs">{label}</Badge>
      <a href={url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sm text-[var(--chat-brand-accent)] hover:underline truncate">
        {title ?? hostname}
        <ExternalLink className="h-3 w-3 shrink-0" />
      </a>
    </li>
  )
}
