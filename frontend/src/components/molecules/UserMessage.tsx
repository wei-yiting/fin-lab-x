export function UserMessage({ content }: { content: string }) {
  return (
    <div data-testid="user-bubble" className="ml-auto max-w-[85%] rounded-2xl border border-[var(--chat-brand-accent)]/[0.12] bg-secondary px-4 py-3 text-sm text-secondary-foreground">
      {content}
    </div>
  )
}
