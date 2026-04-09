import { describe, test, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Sources } from '../Sources'

describe('Sources molecule', () => {
  test('TC-comp-sources-01: renders entries with title when present, hostname when missing', () => {
    const extractedSources = [
      { label: '1', url: 'https://reuters.com/x', title: 'Reuters X', hostname: 'reuters.com' },
      { label: '2', url: 'https://bloomberg.com/y', title: undefined, hostname: 'bloomberg.com' },
    ]
    render(<Sources sources={extractedSources} />)

    expect(screen.getByText('Reuters X')).toBeInTheDocument()
    expect(screen.getByText('bloomberg.com')).toBeInTheDocument()
  })

  test('TC-comp-sources-01: SourceLink has anchor id="src-{label}" for in-page jump', () => {
    const extractedSources = [
      { label: '3', url: 'https://x.com', title: 'X', hostname: 'x.com' },
    ]
    const { container } = render(<Sources sources={extractedSources} />)
    expect(container.querySelector('#src-3')).toBeInTheDocument()
  })

  test('TC-comp-sources-02: source with javascript: URL is filtered out before rendering anchor', () => {
    const evilSources = [
      { label: '1', url: 'javascript:alert(1)', title: 'Evil', hostname: '' },
    ]
    const { container } = render(<Sources sources={evilSources} />)

    expect(container.querySelector('a[href^="javascript:"]')).toBeNull()
  })
})
