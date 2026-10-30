// hermes-minimal-ui: a link copied natively from a full-screen terminal app arrives with its
// wrap points turned into newlines + indent. Rejoin it only when the whole paste is one URL.
import { describe, expect, it } from 'vitest'

import { rejoinWrappedUrl } from '../lib/text.js'

const A = 'https://github.com/NousResearch/hermes-agent/blob/main/ui-tui/'
const B = 'packages/hermes-ink/src/ink/selection.ts?plain=1#L970'

describe('rejoinWrappedUrl', () => {
  it('rejoins a URL split by a wrap newline and indent', () => {
    expect(rejoinWrappedUrl(`${A}\n   ${B}`)).toBe(A + B)
  })

  it('rejoins CRLF and three fragments', () => {
    expect(rejoinWrappedUrl(`${A}\r\n${A.slice(8)}\n  ${B}`)).toBe(A + A.slice(8) + B)
  })

  it('leaves single-line text alone', () => {
    expect(rejoinWrappedUrl(A + B)).toBe(A + B)
  })

  it('leaves a list of several URLs alone', () => {
    expect(rejoinWrappedUrl(`${A}\nhttps://example.com/x`)).toBe(`${A}\nhttps://example.com/x`)
  })

  it('leaves prose with spaces alone', () => {
    const t = `check this link\nhttps://example.com/a/b?c=d`
    expect(rejoinWrappedUrl(t)).toBe(t)
    const u = `${A}\nthanks for sharing`
    expect(rejoinWrappedUrl(u)).toBe(u)
  })

  it('does not join a short URL followed by a word on its own line', () => {
    expect(rejoinWrappedUrl('https://a.com\nthanks')).toBe('https://a.com\nthanks')
  })

  it('leaves non-URL multi-line pastes alone', () => {
    expect(rejoinWrappedUrl('line one\nline two')).toBe('line one\nline two')
  })
})
