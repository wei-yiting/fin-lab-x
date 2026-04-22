export function UserMessage({ content }: { content: string }) {
  return (
    <div
      data-testid="user-bubble"
      className="ml-auto max-w-[72%] rounded-[16px_16px_4px_16px] border border-[var(--chat-brand-accent)]/[0.12] bg-[linear-gradient(135deg,oklch(0.2914_0.0357_250.70)_0%,oklch(0.2654_0.0345_255.83)_100%)] px-4 py-[11px] text-sm leading-[1.6] text-foreground"
    >
      {content}
    </div>
  );
}
