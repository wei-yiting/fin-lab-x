import { defineConfig, devices } from "@playwright/test";

const isCI = !!process.env.CI;

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? 2 : undefined,
  reporter: isCI ? [["html", { open: "never" }], ["list"]] : [["list"]],
  expect: {
    timeout: 5_000,
  },
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
    video: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  // Firefox is intentionally excluded: MSW + Firefox has a compat issue where
  // worker.start() hangs after page.reload(), blocking the app from re-mounting.
  // Enable with `pnpm exec playwright test --project=firefox` for targeted firefox runs
  // once the MSW Firefox interaction is resolved.
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
      testIgnore: /critical\/refresh-invariant\.spec\.ts/,
    },
  ],
  webServer: {
    command: "pnpm run preview:e2e",
    url: "http://localhost:5173",
    reuseExistingServer: !isCI,
    timeout: 120_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
