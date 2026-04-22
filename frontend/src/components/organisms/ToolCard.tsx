import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/primitives/collapsible";
import { ToolRow } from "@/components/molecules/ToolRow";
import { ToolDetail } from "@/components/molecules/ToolDetail";
import { toFriendlyError } from "@/lib/error-messages";
import { isRunningToolState } from "@/models";
import type { ToolUIState } from "@/models";

export interface ToolPart {
  type: string;
  toolCallId: string;
  toolName?: string;
  title?: string;
  state: string;
  input: unknown;
  output?: unknown;
  errorText?: string;
}

function resolveToolName(toolPart: ToolPart): string {
  if (toolPart.toolName) return toolPart.toolName;
  if (toolPart.title) return toolPart.title;
  if (toolPart.type.startsWith("tool-")) return toolPart.type.slice(5);
  return toolPart.type;
}

interface ToolCardProps {
  toolPart: ToolPart;
  isAborted: boolean;
  progressText?: string;
}

export function ToolCard({ toolPart, isAborted, progressText }: ToolCardProps) {
  const visualState: ToolUIState =
    isAborted && isRunningToolState(toolPart.state) ? "aborted" : (toolPart.state as ToolUIState);

  const friendly =
    toolPart.state === "output-error" && toolPart.errorText
      ? toFriendlyError({ source: "tool-output-error", rawMessage: toolPart.errorText })
      : null;

  return (
    <Collapsible>
      <div
        data-testid="tool-card"
        data-tool-call-id={toolPart.toolCallId}
        data-tool-state={visualState}
        className="mt-1 mb-4 rounded-lg border border-border bg-card"
      >
        <CollapsibleTrigger
          data-testid="tool-card-expand"
          aria-label="Toggle tool details"
          className="w-full"
        >
          <ToolRow
            visualState={visualState}
            toolName={resolveToolName(toolPart)}
            progressText={progressText}
            friendlyTitle={friendly?.title}
          />
        </CollapsibleTrigger>
        <CollapsibleContent>
          <ToolDetail
            input={toolPart.input}
            output={toolPart.output}
            errorDetail={toolPart.state === "output-error" ? toolPart.errorText : undefined}
          />
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
