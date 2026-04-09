import { describe, test, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatHeader } from '../ChatHeader'

describe('ChatHeader', () => {
  test('clear button disabled when messagesEmpty=true', () => {
    render(<ChatHeader onClear={vi.fn()} messagesEmpty={true} />)
    expect(screen.getByTestId('composer-clear-btn')).toBeDisabled()
  })

  test('clear button enabled when messagesEmpty=false', () => {
    render(<ChatHeader onClear={vi.fn()} messagesEmpty={false} />)
    expect(screen.getByTestId('composer-clear-btn')).toBeEnabled()
  })

  test('click invokes onClear callback', async () => {
    const user = userEvent.setup()
    const onClear = vi.fn()
    render(<ChatHeader onClear={onClear} messagesEmpty={false} />)
    await user.click(screen.getByTestId('composer-clear-btn'))
    expect(onClear).toHaveBeenCalledTimes(1)
  })
})
