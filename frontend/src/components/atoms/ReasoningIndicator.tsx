export function ReasoningIndicator() {
  return (
    <div data-testid="reasoning-indicator" className="flex items-center gap-1 py-4 px-2">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  );
}
