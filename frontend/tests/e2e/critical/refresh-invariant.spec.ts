import { test, expect } from '@playwright/test'

test('S-cross-01 @critical: page refresh produces new chatId and clean state', async ({ page }) => {
  await page.goto('/?msw_fixture=happy-text')

  await page.getByTestId('composer-textarea').fill('test')
  await page.getByTestId('composer-send-btn').click()
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready', { timeout: 10000 })

  const chatIdBefore = await page.getByTestId('chat-panel').getAttribute('data-chat-id')

  await page.reload()

  await expect(page.getByTestId('empty-state')).toBeVisible({ timeout: 10000 })
  await expect(page.getByTestId('user-bubble')).toHaveCount(0)

  const chatIdAfter = await page.getByTestId('chat-panel').getAttribute('data-chat-id')
  expect(chatIdAfter).not.toBe(chatIdBefore)
})
