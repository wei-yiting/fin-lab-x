import { test, expect } from "../fixtures";

test(
  "app shell loads and displays heading",
  { tag: ["@smoke", "@regression"] },
  async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("FinLab-X");
  },
);
