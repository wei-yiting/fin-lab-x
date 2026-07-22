import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

import { test, expect } from "../fixtures";
import { E2E_TIMEOUTS } from "../constants";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// J-stream-01 ship gate: provider × reasoning matrix.
//
// Only the Gemini reasoning-ON row runs automatically (it uses the backend's
// default credentials against the happy-text MSW fixture). The other 5 rows
// need provider-specific API keys AND a runtime agent-capability override the
// backend does not expose yet, AND the row → trace_id correlation depends on
// an `x-langfuse-trace-id` response header that is not shipped. Rather than
// ship 5 permanently-skipped @critical tests, we keep the full matrix as a
// validated MANIFEST (one always-running test) plus ONE real smoke row.
//
// When the keys + header ship, promote the manifest rows back into executable
// tests that feed `backend/scripts/validation/verify_langfuse_trace.py`.
test.use({ video: "on" });

type Expectation = "reasoning-on" | "reasoning-off" | "unsupported";

type MatrixRow = {
  id: string;
  name: string;
  fixture: string;
  expectation: Expectation;
  // Why the row is not auto-executable today (null = runs automatically).
  blockedBy: string | null;
};

const FIXTURE_DIR = path.join(__dirname, "fixtures", "agent-capability");

const ROWS: MatrixRow[] = [
  { id: "gemini-on", name: "Gemini reasoning ON", fixture: "gemini-on.yaml", expectation: "reasoning-on", blockedBy: null },
  { id: "gemini-off", name: "Gemini reasoning OFF", fixture: "gemini-off.yaml", expectation: "reasoning-off", blockedBy: "runtime agent-capability override not exposed by backend" },
  { id: "anthropic-on", name: "Anthropic reasoning ON", fixture: "anthropic-on.yaml", expectation: "reasoning-on", blockedBy: "ANTHROPIC_API_KEY" },
  { id: "anthropic-off", name: "Anthropic reasoning OFF", fixture: "anthropic-off.yaml", expectation: "reasoning-off", blockedBy: "ANTHROPIC_API_KEY" },
  { id: "openai-on", name: "OpenAI Responses reasoning ON", fixture: "openai-on.yaml", expectation: "reasoning-on", blockedBy: "OPENAI_API_KEY" },
  { id: "openai-off", name: "OpenAI Responses reasoning OFF", fixture: "openai-off.yaml", expectation: "reasoning-off", blockedBy: "OPENAI_API_KEY" },
];

test(
  "matrix manifest: all 6 provider × reasoning rows have a capability fixture",
  { tag: ["@matrix"] },
  // eslint-disable-next-line no-empty-pattern -- Playwright needs object destructuring to resolve fixtures; this test uses none.
  async ({}, testInfo) => {
    // Guards that every intended matrix row still has a parseable
    // agent-capability fixture on disk, so promoting a row to executable
    // later only needs keys — not new fixtures. Also publishes the manifest
    // (row → expectation → blocker) as an artifact for ship-gate review.
    for (const row of ROWS) {
      const fixturePath = path.join(FIXTURE_DIR, row.fixture);
      expect(fs.existsSync(fixturePath), `${row.fixture} must exist`).toBe(true);
      expect(fs.readFileSync(fixturePath, "utf8").trim().length).toBeGreaterThan(0);
    }

    await testInfo.attach("matrix-manifest.json", {
      body: JSON.stringify(ROWS, null, 2),
      contentType: "application/json",
    });

    const blocked = ROWS.filter((r) => r.blockedBy);
    console.log(
      `[matrix] 1 row auto-runs (gemini-on); ${blocked.length} rows blocked: ` +
        blocked.map((r) => `${r.id}(${r.blockedBy})`).join(", "),
    );
  },
);

test(
  "matrix smoke: Gemini reasoning ON streams a chat turn to completion",
  { tag: ["@critical", "@matrix"] },
  async ({ chat, page }, testInfo) => {
    const row = ROWS.find((r) => r.id === "gemini-on")!;
    await testInfo.attach(`agent-capability-${row.id}.yaml`, {
      body: fs.readFileSync(path.join(FIXTURE_DIR, row.fixture), "utf8"),
      contentType: "application/yaml",
    });

    await chat.gotoFixture("happy-text");
    await chat.sendMessage(`matrix probe: ${row.id}`);
    await chat.waitReady();

    await expect(page.getByTestId("assistant-message")).toBeVisible({
      timeout: E2E_TIMEOUTS.streamComplete,
    });
  },
);
