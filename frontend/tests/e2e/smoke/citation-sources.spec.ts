import { test, expect } from "../fixtures";

test(
  "citations render as RefSup with Sources block",
  { tag: ["@smoke", "@regression"] },
  async ({ chat, page }) => {
    await chat.gotoFixture("happy-citation");
    await chat.sendMessage("Show me analysis");
    await chat.waitReady();

    const refSups = page.getByTestId("ref-sup");
    await expect(refSups).toHaveCount(2);

    await expect(page.getByTestId("sources-block")).toBeVisible();

    const sourceLinks = page.getByTestId("source-link");
    await expect(sourceLinks).toHaveCount(2);

    await expect(page.getByText("Reuters Tech Report")).toBeVisible();
    await expect(page.getByText("Bloomberg Analysis")).toBeVisible();
  },
);
