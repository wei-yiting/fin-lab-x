import { describe, test, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Markdown } from '../Markdown'

describe('Markdown — citation vs inline link disambiguation', () => {
  test('inline link [3](url) renders as normal <a> even when a source with label "3" exists', () => {
    const sources = [
      { label: '1', url: 'https://reuters.com/a', hostname: 'reuters.com' },
      { label: '3', url: 'https://official-source.com/article', hostname: 'official-source.com' },
    ]
    const text =
      'See [3](https://blog.example.com/top-10) for ranking.\n\n' +
      '[1]: #src-1\n' +
      '[3]: #src-3'

    const { container } = render(<Markdown text={text} isStreaming={false} sources={sources} />)

    // The inline link should NOT be rewritten to a RefSup — it must render as <a>
    const anchors = container.querySelectorAll('a')
    const inlineAnchor = Array.from(anchors).find(
      (a) => a.getAttribute('href') === 'https://blog.example.com/top-10',
    )
    expect(inlineAnchor).toBeDefined()
    expect(inlineAnchor?.textContent).toBe('3')
    expect(inlineAnchor?.getAttribute('target')).toBe('_blank')
    expect(inlineAnchor?.getAttribute('rel')).toContain('noopener')
  })

  test('reference-style [1] with matching source renders as RefSup with source URL', () => {
    const sources = [
      { label: '1', url: 'https://reuters.com/real-article', hostname: 'reuters.com' },
    ]
    const text = 'Growth [1].\n\n[1]: #src-1'

    render(<Markdown text={text} isStreaming={false} sources={sources} />)

    const refSup = screen.getByTestId('ref-sup')
    expect(refSup).toHaveAttribute('data-ref-label', '1')
    // RefSup renders an anchor with the source URL
    expect(refSup.querySelector('a')?.getAttribute('href')).toBe('https://reuters.com/real-article')
  })
})
