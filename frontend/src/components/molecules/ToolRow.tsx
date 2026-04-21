import { StatusDot } from "@/components/atoms/StatusDot";
import { ChevronRight } from "lucide-react";

type ToolRowState =
  | "input-streaming"
  | "input-available"
  | "output-available"
  | "output-error"
  | "aborted";

function stateToStatusDot(state: ToolRowState): "running" | "success" | "error" | "aborted" {
  switch (state) {
    case "input-streaming":
    case "input-available":
      return "running";
    case "output-available":
      return "success";
    case "output-error":
      return "error";
    case "aborted":
      return "aborted";
  }
}

function stateLabel(
  state: ToolRowState,
  toolName: string,
  progressText?: string,
  friendlyTitle?: string,
): string {
  switch (state) {
    case "input-streaming":
    case "input-available":
      return progressText ?? `Running ${toolName}...`;
    case "output-available":
      return `Completed ${toolName}`;
    case "output-error":
      return friendlyTitle ?? `Error in ${toolName}`;
    case "aborted":
      return "Aborted";
  }
}

export function ToolRow({
  visualState,
  toolName,
  progressText,
  friendlyTitle,
}: {
  visualState: ToolRowState;
  toolName: string;
  progressText?: string;
  friendlyTitle?: string;
}) {
  return (
    <div className="flex items-center gap-2 py-1.5 px-2 text-sm">
      <StatusDot state={stateToStatusDot(visualState)} />
      <span className="truncate text-muted-foreground">
        {stateLabel(visualState, toolName, progressText, friendlyTitle)}
      </span>
      <ChevronRight className="ml-auto h-4 w-4 shrink-0 text-muted-foreground transition-transform [[data-state=open]_&]:rotate-90" />
    </div>
  );
}
