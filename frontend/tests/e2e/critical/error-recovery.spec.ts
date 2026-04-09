import { test, expect } from '@playwright/test'

test('J-err-01 @critical: pre-stream error recovery via Retry', async ({ page }) => {
  await page.goto('/?msw_fixture=pre-stream-500-then-success')

  await page.getByTestId('composer-textarea').fill('test')
  await page.getByTestId('composer-send-btn').click()

  await expect(page.getByTestId('stream-error-block')).toBeVisible({ timeout: 10000 })
  await expect(page.getByTestId('error-title')).toContainText('Server error')
  await expect(page.getByTestId('error-retry-btn')).toBeVisible()

  await expect(page.getByTestId('user-bubble')).toBeVisible()
  await expect(page.getByTestId('user-bubble')).toHaveCount(1)

  await page.getByTestId('error-retry-btn').click()

  await expect(page.getByTestId('stream-error-block')).not.toBeVisible({ timeout: 10000 })

  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready', { timeout: 10000 })

  await expect(page.getByTestId('user-bubble')).toHaveCount(1)

  await expect(page.getByTestId('assistant-message')).toBeVisible()
})
