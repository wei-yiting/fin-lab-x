import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// J-stream-01 ship gate: 6-case provider × reasoning matrix.
//
// Each row exercises a streaming chat-turn end-to-end and emits its
// associated agent-capability fixture path to stdout so the verifier
// (`backend/scripts/validation/verify_langfuse_trace.py`) can correlate
// row → expected reasoning shape post-run.
//
// Video recording: forced ON for this spec only via `test.use({ video: "on" })`.
// The global config defaults to "retain-on-failure", which would not produce
// a video for a passing matrix row — but J-stream-01 needs every row's
// recording for ship-gate review, regardless of pass/fail.
test.use({ video: "on" });

type Expectation = "reasoning-on" | "reasoning-off" | "unsupported";

type MatrixRow = {
  id: string;
  name: string;
  fixture: string;
  expectation: Expectation;
  // Env var that must be set for the row to run. Gemini's row uses the
  // backend's default credentials; the other 5 need provider-specific keys
  // that are not available in CI today, so they self-skip.
  requiresEnv?: string;
};

const FIXTURE_DIR = path.join(__dirname, "fixtures", "agent-capability");

const ROWS: MatrixRow[] = [
  {
    id: "gemini-on",
    name: "Gemini reasoning ON",
    fixture: "gemini-on.yaml",
    expectation: "reasoning-on",
  },
  {
    id: "gemini-off",
    name: "Gemini reasoning OFF",
    fixture: "gemini-off.yaml",
    expectation: "reasoning-off",
    // Same provider as default agent, but switching reasoning at runtime
    // requires an admin-config override path the backend does not expose
    // today. Gate behind an explicit opt-in env var.
    requiresEnv: "MATRIX_ALLOW_RUNTIME_AGENT_OVERRIDE",
  },
  {
    id: "anthropic-on",
    name: "Anthropic reasoning ON",
    fixture: "anthropic-on.yaml",
    expectation: "reasoning-on",
    requiresEnv: "ANTHROPIC_API_KEY",
  },
  {
    id: "anthropic-off",
    name: "Anthropic reasoning OFF",
    fixture: "anthropic-off.yaml",
    expectation: "reasoning-off",
    requiresEnv: "ANTHROPIC_API_KEY",
  },
  {
    id: "openai-on",
    name: "OpenAI Responses reasoning ON",
    fixture: "openai-on.yaml",
    expectation: "reasoning-on",
    requiresEnv: "OPENAI_API_KEY",
  },
  {
    id: "openai-off",
    name: "OpenAI Responses reasoning OFF",
    fixture: "openai-off.yaml",
    expectation: "reasoning-off",
    requiresEnv: "OPENAI_API_KEY",
  },
];

for (const row of ROWS) {
  test(
    `matrix: ${row.name}`,
    { tag: ["@critical", "@matrix"] },
    async ({ chat, page }, testInfo) => {
      // Self-skip rows whose provider credentials / runtime-override hooks
      // are not present. Listing them keeps the 6-case shape visible in
      // `--list` output (J-stream-01 ship-gate manifest) so reviewers can
      // see which rows would run if the keys were exported.
      if (row.requiresEnv && !process.env[row.requiresEnv]) {
        test.skip(
          true,
          `requires env ${row.requiresEnv}; runtime agent-capability override not wired into backend yet`,
        );
      }

      const fixturePath = path.join(FIXTURE_DIR, row.fixture);
      const fixtureBody = fs.readFileSync(fixturePath, "utf8");

      // Surface fixture metadata in the test artifacts so the operator-side
      // verifier shell wrapper can pair (case → expected reasoning shape)
      // without re-reading the spec file.
      await testInfo.attach(`agent-capability-${row.id}.yaml`, {
        body: fixtureBody,
        contentType: "application/yaml",
      });
      await testInfo.attach("expectation.json", {
        body: JSON.stringify({ row: row.id, expectation: row.expectation }, null, 2),
        contentType: "application/json",
      });

      // Capture trace_id from the chat POST response if the backend exposes
      // one (header `x-langfuse-trace-id` is a planned but not-yet-shipped
      // hook — see report). When absent, downstream verifier invocation
      // becomes a manual step.
      let traceId: string | null = null;
      page.on("response", async (resp) => {
        if (resp.request().method() !== "POST" || !resp.url().includes("/api/v1/chat")) {
          return;
        }
        const headerValue = resp.headers()["x-langfuse-trace-id"];
        if (headerValue) traceId = headerValue;
      });

      await chat.gotoFixture("happy-text");
      await chat.sendMessage(`matrix probe: ${row.id}`);
      await chat.waitReady();

      await expect(page.getByTestId("assistant-message")).toBeVisible({
        timeout: E2E_TIMEOUTS.streamComplete,
      });

      // Emit row → trace_id mapping to stdout so a shell wrapper can run:
      //   uv run python -m backend.scripts.validation.verify_langfuse_trace \
      //     <trace_id> --expect-reasoning-{on,off,unsupported}
      // per matrix row.
      console.log(
        `[matrix] row=${row.id} fixture=${row.fixture} expectation=${row.expectation} trace_id=${traceId ?? "<unavailable>"}`,
      );
    },
  );
}
