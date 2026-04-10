import { test, expect } from '@playwright/test'

const VIEWPORT = 'message-list-viewport'

async function sendAndWait(page: import('@playwright/test').Page, text: string) {
  await page.getByTestId('composer-textarea').fill(text)
  await page.getByTestId('composer-send-btn').click()
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready', { timeout: 10000 })
}

test('S-scroll-e2e-01 @smoke: overflowed content is scrollable', async ({ page }) => {
  await page.goto('/?msw_fixture=scroll-overflow')
  await sendAndWait(page, 'Generate long content')

  const viewport = page.getByTestId(VIEWPORT)

  const isScrollable = await viewport.evaluate(
    (el) => el.scrollHeight > el.clientHeight,
  )
  expect(isScrollable).toBe(true)

  const canScrollUp = await viewport.evaluate((el) => {
    el.scrollTop = 0
    return el.scrollTop === 0 && el.scrollHeight > el.clientHeight
  })
  expect(canScrollUp).toBe(true)
})

test('S-scroll-e2e-02 @smoke: sending new message auto-scrolls to bottom', async ({ page }) => {
  await page.goto('/?msw_fixture=scroll-overflow')

  await sendAndWait(page, 'First message')

  const viewport = page.getByTestId(VIEWPORT)

  // Scroll up
  await viewport.evaluate((el) => { el.scrollTop = 0 })
  await page.waitForTimeout(100)

  const notAtBottom = await viewport.evaluate(
    (el) => el.scrollHeight - el.scrollTop - el.clientHeight > 100,
  )
  expect(notAtBottom).toBe(true)

  // Send new message — should auto-scroll to bottom
  await sendAndWait(page, 'Second message')

  const isAtBottom = await viewport.evaluate(
    (el) => el.scrollHeight - el.scrollTop - el.clientHeight < 100,
  )
  expect(isAtBottom).toBe(true)
})
