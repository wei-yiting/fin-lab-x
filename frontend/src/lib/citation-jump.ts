import { createContext, useContext } from "react";

/**
 * Lets an inline `[N]` marker (rendered deep inside the memoized Markdown
 * tree) open and reveal its entry in the same message's citation list.
 * Outside a provider the marker has nowhere to jump, so it is a no-op.
 */
export const CitationJumpContext = createContext<(label: string) => void>(() => {});

export function useCitationJump(): (label: string) => void {
  return useContext(CitationJumpContext);
}
