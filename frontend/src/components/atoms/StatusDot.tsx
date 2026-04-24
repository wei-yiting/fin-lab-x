import { cn } from "@/lib/utils";

export function StatusDot({ state }: { state: "running" | "success" | "error" | "aborted" }) {
  return (
    <span
      data-testid="status-dot"
      data-status-state={state}
      className={cn(
        "inline-block h-2 w-2 rounded-full",
        state === "running" && "bg-[var(--status-running)] animate-pulse",
        state === "success" && "bg-[var(--status-success)]",
        state === "error" && "bg-[var(--status-error)]",
        state === "aborted" && "bg-[var(--status-aborted)]",
      )}
    />
  );
}
