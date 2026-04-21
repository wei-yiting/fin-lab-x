export function RefSup({ label, href }: { label: string; href: string }) {
  return (
    <sup data-testid="ref-sup" data-ref-label={label}>
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-[oklch(0.55_0.10_255)] hover:text-[oklch(0.65_0.14_255)] hover:underline text-[10px] font-medium"
      >
        [{label}]
      </a>
    </sup>
  );
}
