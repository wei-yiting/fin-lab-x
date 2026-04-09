import { test, expect } from '@playwright/test'

test('S-md-03 @security: javascript: URL is sanitized', async ({ page }) => {
  let dialogTriggered = false
  page.on('dialog', async (dialog) => {
    dialogTriggered = true
    await dialog.dismiss()
  })

  await page.goto('/?msw_fixture=xss-javascript-url')

  await page.getByTestId('composer-textarea').fill('show me sources')
  await page.getByTestId('composer-send-btn').click()

  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready', { timeout: 10000 })

  const xssAnchors = page.locator('a[href^="javascript:"]')
  await expect(xssAnchors).toHaveCount(0)

  const mailtoAnchors = page.locator('a[href^="mailto:"]')
  await expect(mailtoAnchors).toHaveCount(0)

  expect(dialogTriggered).toBe(false)
})
