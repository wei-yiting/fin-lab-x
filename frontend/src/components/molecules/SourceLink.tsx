import { ExternalLink } from "lucide-react"

export function SourceLink({ label, url, title, hostname }: {
  label: string
  url: string
  title?: string
  hostname: string
}) {
  return (
    <li data-testid="source-link" data-source-label={label} id={`src-${label}`} className="flex items-baseline gap-1.5">
      <span className="shrink-0 w-4 text-[10px] font-medium text-[oklch(0.55_0.10_255)]">[{label}]</span>
      <a href={url} target="_blank" rel="noopener noreferrer" className="flex items-baseline gap-1 text-xs text-[oklch(0.55_0.04_252)] hover:text-[oklch(0.70_0.08_252)] hover:underline truncate">
        {title ?? hostname}
        <ExternalLink className="h-2.5 w-2.5 shrink-0 translate-y-px" />
      </a>
    </li>
  )
}
