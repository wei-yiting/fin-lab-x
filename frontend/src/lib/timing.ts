/**
 * Timing constants for the reasoning chips + placeholder system.
 * Centralized so integration tests can mock this module with small values
 * (F6 ruling: the 10s default is locked by fake-timer unit tests; exactly
 * one ChatPanel integration case verifies the wiring with a mocked
 * threshold against MSW real time).
 */

/** Global stall stopwatch threshold — any stream part arrival resets it. */
export const STALL_THRESHOLD_MS = 10_000;

/**
 * Grace delay before the dead-air placeholder appears in the
 * "chip collapsed → reply text" window. At collapse time the client cannot
 * know whether the next part is a tool card (decision 5: no placeholder in
 * that micro-gap) or reply text (placeholder wanted): the wire carries no
 * lookahead. The grace delay resolves the ambiguity empirically — tool
 * parts follow a collapse within milliseconds, so only a genuine dead-air
 * window outlives it.
 */
export const PLACEHOLDER_GRACE_MS = 300;
