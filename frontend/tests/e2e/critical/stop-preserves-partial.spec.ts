import { test, expect } from '@playwright/test'

test('S-stop-01 @critical: stop preserves partial text and resets Composer', async ({ page }) => {
  await page.goto('/?msw_fixture=long-text-stream')

  await page.getByTestId('composer-textarea').fill('write a long essay')
  await page.getByTestId('composer-send-btn').click()

  await expect(page.getByTestId('assistant-message')).toBeVisible({ timeout: 10000 })

  await page.waitForTimeout(500)

  await page.getByTestId('composer-stop-btn').click()

  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready', { timeout: 5000 })

  await expect(page.getByTestId('composer-send-btn')).toBeVisible()

  await expect(page.getByTestId('assistant-message')).toBeVisible()
  const text = await page.getByTestId('assistant-message').textContent()
  expect(text!.length).toBeGreaterThan(0)
})
