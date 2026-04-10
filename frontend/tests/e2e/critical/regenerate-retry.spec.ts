import { test, expect } from '@playwright/test'

test('J-regen-retry-01 @critical: regenerate failure → retry succeeds without duplicate history', async ({ page }) => {
  await page.goto('/?msw_fixture=regenerate-fail-then-success')

  // Step 1: send initial message → success
  await page.getByTestId('composer-textarea').fill('Tell me about AAPL')
  await page.getByTestId('composer-send-btn').click()
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready', { timeout: 10000 })
  await expect(page.getByTestId('assistant-message')).toContainText('Original response.')

  // Step 2: click Regenerate → fails with 500
  await page.getByTestId('regenerate-btn').click()
  await expect(page.getByTestId('stream-error-block')).toBeVisible({ timeout: 10000 })
  await expect(page.getByTestId('error-title')).toContainText('Server error')

  // Step 3: click Retry → succeeds
  await page.getByTestId('error-retry-btn').click()
  await expect(page.getByTestId('stream-error-block')).not.toBeVisible({ timeout: 10000 })
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready', { timeout: 10000 })
  await expect(page.getByTestId('assistant-message')).toContainText('Retried response.')

  // Step 4: verify no duplicate history
  await expect(page.getByTestId('user-bubble')).toHaveCount(1)
})
