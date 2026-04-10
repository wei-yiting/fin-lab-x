import { test, expect } from '@playwright/test'

test('J-regen-01 @smoke: regenerate replaces assistant response', async ({ page }) => {
  await page.goto('/?msw_fixture=regenerate-happy')

  await page.getByTestId('composer-textarea').fill('Tell me about MSFT')
  await page.getByTestId('composer-send-btn').click()

  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready', { timeout: 10000 })
  await expect(page.getByTestId('assistant-message')).toContainText('Original response.')

  await page.getByTestId('regenerate-btn').click()

  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready', { timeout: 10000 })
  await expect(page.getByTestId('assistant-message')).toContainText('Regenerated response.')

  await expect(page.getByTestId('user-bubble')).toHaveCount(1)
})
