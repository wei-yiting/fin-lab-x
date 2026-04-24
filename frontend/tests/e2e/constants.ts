// MSW stream fixtures simulate 2-5s latency with chunked delays; 10s leaves buffer for CI variance
export const E2E_TIMEOUTS = {
  streamComplete: 10_000,
  status: 5_000,
} as const;
