import { test, expect } from '@playwright/test'

test('J-err-01 @critical: pre-stream error shows ErrorBlock with Retry', async ({ page }) => {
  await page.goto('/?msw_fixture=pre-stream-500')

  await page.getByTestId('composer-textarea').fill('test')
  await page.getByTestId('composer-send-btn').click()

  await expect(page.getByTestId('stream-error-block')).toBeVisible({ timeout: 10000 })

  await expect(page.getByTestId('error-retry-btn')).toBeVisible()

  await expect(page.getByTestId('error-title')).toContainText('Server error')
})
