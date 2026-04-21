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

type ToolPart = {
  type: string;
  toolCallId: string;
  toolName?: string;
  title?: string;
  state: string;
  input: unknown;
  output?: unknown;
  errorText?: string;
};

function resolveToolName(part: ToolPart): string {
  if (part.toolName) return part.toolName;
  if (part.title) return part.title;
  if (part.type.startsWith("tool-")) return part.type.slice(5);
  return part.type;
}

export function ToolCard({
  part,
  isAborted,
  progressText,
}: {
  part: ToolPart;
  isAborted: boolean;
  progressText?: string;
}) {
  const visualState: ToolUIState =
    isAborted && isRunningToolState(part.state) ? "aborted" : (part.state as ToolUIState);

  const friendly =
    part.state === "output-error" && part.errorText
      ? toFriendlyError({ source: "tool-output-error", rawMessage: part.errorText })
      : null;

  return (
    <Collapsible>
      <div
        data-testid="tool-card"
        data-tool-call-id={part.toolCallId}
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
            toolName={resolveToolName(part)}
            progressText={progressText}
            friendlyTitle={friendly?.title}
          />
        </CollapsibleTrigger>
        <CollapsibleContent>
          <ToolDetail
            input={part.input}
            output={part.output}
            errorDetail={part.state === "output-error" ? part.errorText : undefined}
          />
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
