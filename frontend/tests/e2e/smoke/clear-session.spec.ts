import { test, expect } from '@playwright/test'

test('J-clear-01 @smoke: clear session resets messages and chatId', async ({ page }) => {
  await page.goto('/?msw_fixture=happy-text')

  await page.getByTestId('composer-textarea').fill('first question')
  await page.getByTestId('composer-send-btn').click()
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready', { timeout: 10000 })

  const oldChatId = await page.getByTestId('chat-panel').getAttribute('data-chat-id')
  expect(oldChatId).toBeTruthy()

  await page.getByTestId('composer-clear-btn').click()

  await expect(page.getByTestId('empty-state')).toBeVisible()
  await expect(page.getByTestId('user-bubble')).toHaveCount(0)

  const newChatId = await page.getByTestId('chat-panel').getAttribute('data-chat-id')
  expect(newChatId).toBeTruthy()
  expect(newChatId).not.toBe(oldChatId)
})
