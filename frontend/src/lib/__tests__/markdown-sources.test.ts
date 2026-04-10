import { describe, test, expect } from 'vitest'
import { extractSources } from '../markdown-sources'

describe('extractSources — happy paths', () => {
  test('TC-unit-md-01: extracts single reference with title attribute', () => {
    const md = `
NVDA 宣布擴大 Blackwell 產能 [1]。

[1]: https://reuters.com/nvda-blackwell-expansion "Reuters: NVIDIA expands Blackwell production"
    `.trim()

    const result = extractSources(md)

    expect(result).toEqual([
      {
        label: '1',
        url: 'https://reuters.com/nvda-blackwell-expansion',
        title: 'Reuters: NVIDIA expands Blackwell production',
        hostname: 'reuters.com',
      },
    ])
  })

  test('TC-unit-md-02: falls back to hostname when title is missing', () => {
    const md = `
NVDA Q2 [2] reported.

[2]: https://bloomberg.com/nvda-q2
    `.trim()

    const result = extractSources(md)

    expect(result).toEqual([
      {
        label: '2',
        url: 'https://bloomberg.com/nvda-q2',
        title: undefined,
        hostname: 'bloomberg.com',
      },
    ])
  })

  test('TC-unit-md-03: first-wins dedup when [1] is defined twice', () => {
    const md = `
NVDA [1] 漲。

[1]: https://reuters.com/a "Reuters A"
[1]: https://bloomberg.com/b "Bloomberg B"
    `.trim()

    const result = extractSources(md)

    expect(result).toHaveLength(1)
    expect(result[0]).toEqual({
      label: '1',
      url: 'https://reuters.com/a',
      title: 'Reuters A',
      hostname: 'reuters.com',
    })
  })
})

describe('extractSources — security: scheme allowlist', () => {
  test.each([
    ['javascript:alert(1)', 'javascript:'],
    ['data:image/png;base64,iVBOR', 'data:'],
    ['mailto:ir@nvidia.com', 'mailto:'],
    ['file:///etc/hosts', 'file:'],
    ['vbscript:msgbox(1)', 'vbscript:'],
  ])('TC-unit-md-04: drops or sanitizes %s scheme', (url) => {
    const md = `
See [1] for the report.

[1]: ${url} "Click me"
    `.trim()

    const result = extractSources(md)

    if (result.length > 0) {
      expect(result[0].url).not.toMatch(/^(javascript|data|mailto|file|vbscript):/i)
    } else {
      expect(result).toHaveLength(0)
    }
  })

  test('allows http and https schemes', () => {
    const md = `
[1]: http://example.com/a "HTTP"
[2]: https://example.com/b "HTTPS"
    `.trim()

    const result = extractSources(md)

    expect(result).toHaveLength(2)
    expect(result.map((r) => r.url)).toEqual([
      'http://example.com/a',
      'https://example.com/b',
    ])
  })
})

describe('extractSources — incremental parse robustness', () => {
  test('TC-unit-md-05: does not throw on partial URL (chunk boundary mid-URL)', () => {
    const md = `
NVDA [1]。

[1]: https://reut
    `.trim()

    expect(() => extractSources(md)).not.toThrow()
    const result = extractSources(md)
    if (result.length > 0) {
      expect(result[0].hostname).not.toBe('reut')
    }
  })

  test('does not throw on malformed URL (no scheme)', () => {
    const md = `
[1]: bloomberg.com/nvda-q2 "Bloomberg"
    `.trim()

    expect(() => extractSources(md)).not.toThrow()
  })

  test('does not throw on partial title (open quote not closed)', () => {
    const md = `
[1]: https://reuters.com/x "Partial tit
    `.trim()

    expect(() => extractSources(md)).not.toThrow()
  })
})

describe('extractSources — orphan handling', () => {
  test('TC-unit-md-06: def orphan: definition exists but body never references it → still in result', () => {
    const md = `
NVDA 很棒。

[1]: https://reuters.com "Reuters"
    `.trim()

    const result = extractSources(md)

    expect(result).toHaveLength(1)
    expect(result[0].label).toBe('1')
  })

  test('body orphan: [3] in body but no [3]: def → not in result', () => {
    const md = `
NVDA 很棒 [3]。

[1]: https://reuters.com "Reuters"
    `.trim()

    const result = extractSources(md)

    expect(result).toHaveLength(1)
    expect(result[0].label).toBe('1')
    expect(result.find((r) => r.label === '3')).toBeUndefined()
  })
})

describe('extractSources — real backend format fallback', () => {
  test('TC-unit-md-08: extracts [N] URL format (no colon)', () => {
    const md = `
text [1] and [2].

[1] https://reuters.com/report
[2] https://bloomberg.com/analysis
    `.trim()

    const result = extractSources(md)

    expect(result).toHaveLength(2)
    expect(result[0]).toEqual({
      label: '1',
      url: 'https://reuters.com/report',
      title: undefined,
      hostname: 'reuters.com',
    })
    expect(result[1]).toEqual({
      label: '2',
      url: 'https://bloomberg.com/analysis',
      title: undefined,
      hostname: 'bloomberg.com',
    })
  })

  test('TC-unit-md-09: handles trailing spaces (markdown line break)', () => {
    const md = `
text [1].

[1] https://reuters.com/report
    `.trim()

    const result = extractSources(md)

    expect(result).toHaveLength(1)
    expect(result[0].url).toBe('https://reuters.com/report')
  })

  test('TC-unit-md-10: handles mixed formats in same response', () => {
    const md = `
text [1] and [2].

[1]: https://reuters.com/a "Reuters A"
[2] https://bloomberg.com/b
    `.trim()

    const result = extractSources(md)

    expect(result).toHaveLength(2)
    expect(result[0].title).toBe('Reuters A')
    expect(result[1].title).toBeUndefined()
  })
})

test('TC-unit-md-07: orders Sources by numeric label, not by appearance order in markdown', () => {
  const md = `
Body text [3] then [1] then [2].

[3]: https://c.com "C"
[1]: https://a.com "A"
[2]: https://b.com "B"
  `.trim()

  const result = extractSources(md)

  expect(result.map((r) => r.label)).toEqual(['1', '2', '3'])
})
