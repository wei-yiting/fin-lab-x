export function RefSup({ label, href }: { label: string; href: string }) {
  return (
    <sup data-testid="ref-sup" data-ref-label={label}>
      <a href={href} target="_blank" rel="noopener noreferrer" className="text-[var(--chat-brand-accent)] hover:underline text-xs">
        [{label}]
      </a>
    </sup>
  )
}
