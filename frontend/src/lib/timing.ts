/**
 * Coalescing window for `useChat`'s message-state updates
 * (`experimental_throttle`). The wire delivers text deltas far faster than a
 * display can show them — a verbose provider emits several hundred per turn
 * — and each one otherwise re-renders the transcript and re-parses the
 * streaming message's markdown. One frame's worth of coalescing keeps the
 * text visibly flowing while cutting the number of parses by roughly an
 * order of magnitude.
 */
export const STREAM_THROTTLE_MS = 50;
