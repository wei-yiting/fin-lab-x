/**
 * Timing constants for the reasoning chips + placeholder system.
 * Centralized so integration tests can mock this module with small values
 * (the 10s default is locked by fake-timer unit tests; exactly
 * one ChatPanel integration case verifies the wiring with a mocked
 * threshold against MSW real time).
 */

/** Global stall stopwatch threshold — any stream part arrival resets it. */
export const STALL_THRESHOLD_MS = 10_000;

/**
 * Grace delay before the dead-air placeholder appears in the
 * "chip collapsed → reply text" window. At collapse time the client cannot
 * know whether the next part is a tool card (no placeholder wanted in
 * that micro-gap) or reply text (placeholder wanted): the wire carries no
 * lookahead. The grace delay resolves the ambiguity empirically — tool
 * parts follow a collapse within milliseconds, so only a genuine dead-air
 * window outlives it.
 */
export const PLACEHOLDER_GRACE_MS = 300;

/**
 * Coalescing window for `useChat`'s message-state updates
 * (`experimental_throttle`). The wire delivers reasoning/text deltas far
 * faster than a display can show them — a verbose provider emits several
 * hundred per turn — and each one otherwise re-renders the transcript and
 * re-parses the streaming message's markdown. Coalescing into a ~20Hz update
 * rate (about 3 frames at a 60Hz display) keeps the text visibly flowing
 * while cutting the number of parses by roughly an order of magnitude.
 */
export const STREAM_THROTTLE_MS = 50;
