import { test, expect } from "../fixtures";

const EN_CHIP_TITLES = [
  "Today's price move",
  "How a company makes money",
  "Is it expensive?",
  "Risk disclosures vs. recent news",
  "Management narrative vs. the numbers",
  "Cross-company regulatory risk",
];

const ZH_CHIP_TITLES = [
  "今日股價表現",
  "這家公司靠什麼賺錢",
  "現在買算貴嗎？",
  "風險揭露 vs. 近期新聞",
  "經營團隊說法 vs. 實際數字",
  "跨公司法規風險比較",
];

test(
  "language toggle renders starter chips in both locales and survives a reload",
  { tag: ["@critical", "@regression"] },
  async ({ page }) => {
    await page.goto("/");

    const chips = page.getByTestId("prompt-chip");
    await expect(chips).toHaveCount(6);
    for (const [i, title] of EN_CHIP_TITLES.entries()) {
      await expect(chips.nth(i)).toContainText(title);
    }
    await expect(page.locator("html")).toHaveAttribute("lang", "en");

    await page.getByRole("button", { name: "繁體中文" }).click();

    await expect(page.getByRole("heading", { level: 2 })).toHaveText("研究任何一檔美股");
    await expect(chips).toHaveCount(6);
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
    await expect(page.getByTestId("composer-textarea")).toHaveValue(
      "Apple 今天的股價表現如何？背後有什麼相關新聞嗎？",
    );

    await page.getByRole("button", { name: "English" }).click();
    await expect(page.getByRole("heading", { level: 2 })).toHaveText(
      "Research any US-listed stock",
    );
    await expect(chips.first()).toContainText(EN_CHIP_TITLES[0]);
  },
);
