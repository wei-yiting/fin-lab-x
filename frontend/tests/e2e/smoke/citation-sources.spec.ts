import { test, expect } from "@playwright/test";

test("TC-e2e-citation-01 @smoke: citations render as RefSup with Sources block", async ({
  page,
}) => {
  await page.goto("/?msw_fixture=happy-citation");

  await page.getByTestId("composer-textarea").fill("Show me analysis");
  await page.getByTestId("composer-send-btn").click();

  await expect(page.getByTestId("message-list")).toHaveAttribute("data-status", "ready", {
    timeout: 10000,
  });

  const refSups = page.getByTestId("ref-sup");
  await expect(refSups).toHaveCount(2);

  await expect(page.getByTestId("sources-block")).toBeVisible();

  const sourceLinks = page.getByTestId("source-link");
  await expect(sourceLinks).toHaveCount(2);

  await expect(page.getByText("Reuters Tech Report")).toBeVisible();
  await expect(page.getByText("Bloomberg Analysis")).toBeVisible();
});
