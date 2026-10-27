import { test, expect } from "../fixtures";

const EN_CHIP_TITLES = [
  "Risk disclosures vs. recent news",
  "Management narrative vs. the numbers",
  "Cross-company regulatory risk",
  "Evidence-checked bear case",
];

const ZH_CHIP_TITLES = [
  "風險揭露 vs. 近期新聞",
  "經營團隊說法 vs. 實際數字",
  "跨公司法規風險比較",
  "經證據檢驗的看空論點",
];

test(
  "language toggle renders starter chips in both locales and survives a reload",
  { tag: ["@critical", "@regression"] },
  async ({ page }) => {
    await page.goto("/");

    const chips = page.getByTestId("prompt-chip");
    await expect(chips).toHaveCount(4);
    for (const [i, title] of EN_CHIP_TITLES.entries()) {
      await expect(chips.nth(i)).toContainText(title);
    }
    await expect(page.locator("html")).toHaveAttribute("lang", "en");

    await page.getByRole("button", { name: "繁體中文" }).click();

    await expect(page.getByRole("heading", { level: 2 })).toHaveText("研究任何一檔美股");
    await expect(chips).toHaveCount(4);
    for (const [i, title] of ZH_CHIP_TITLES.entries()) {
      await expect(chips.nth(i)).toContainText(title);
    }
    await expect(page.locator("html")).toHaveAttribute("lang", "zh-TW");

    await page.reload();

    await expect(page.getByRole("heading", { level: 2 })).toHaveText("研究任何一檔美股");
    await expect(page.getByRole("button", { name: "繁體中文" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    await chips.first().click();
    await expect(page.getByTestId("composer-textarea")).toHaveValue(/^NVIDIA 在最新 10-K/);

    await page.getByRole("button", { name: "English" }).click();
    await expect(page.getByRole("heading", { level: 2 })).toHaveText(
      "Research any US-listed stock",
    );
    await expect(chips.first()).toContainText(EN_CHIP_TITLES[0]);
  },
);
