// hermes-minimal-ui: clicking a URL that word-wraps onto the next row must yield the WHOLE URL.
import { describe, expect, it } from 'vitest'

import { CellWidth, CharPool, createScreen, HyperlinkPool, setCellAt, StylePool } from './screen.js'
import { findPlainTextUrlAt } from './selection.js'

const put = (screen: ReturnType<typeof createScreen>, col: number, row: number, text: string) => {
  for (let i = 0; i < text.length; i++) {
    setCellAt(screen, col + i, row, { char: text[i]!, hyperlink: undefined, styleId: screen.emptyStyleId, width: CellWidth.Narrow })
  }
}

const wrapped = (continuation: boolean) => {
  const screen = createScreen(20, 3, new StylePool(), new CharPool(), new HyperlinkPool())
  put(screen, 0, 0, 'see https://a.co/abc') // 20 cols, full row
  put(screen, 2, 1, 'def?x=1 ok') // continuation row, 2-col unwritten indent
  put(screen, 0, 2, 'https://b.io/z.')
  screen.softWrap[1] = continuation ? 20 : 0

  return screen
}

describe('findPlainTextUrlAt across soft wraps', () => {
  it('joins the continuation row when clicking the first fragment', () => {
    expect(findPlainTextUrlAt(wrapped(true), 6, 0)).toBe('https://a.co/abcdef?x=1')
  })

  it('joins the previous row when clicking the continuation fragment', () => {
    expect(findPlainTextUrlAt(wrapped(true), 3, 1)).toBe('https://a.co/abcdef?x=1')
  })

  it('does not treat words after the URL as part of it', () => {
    expect(findPlainTextUrlAt(wrapped(true), 11, 1)).toBeUndefined()
  })

  it('keeps single-row behaviour on a hard line break', () => {
    expect(findPlainTextUrlAt(wrapped(false), 6, 0)).toBe('https://a.co/abc')
    expect(findPlainTextUrlAt(wrapped(false), 3, 1)).toBeUndefined()
  })

  it('still strips trailing sentence punctuation', () => {
    expect(findPlainTextUrlAt(wrapped(true), 3, 2)).toBe('https://b.io/z')
  })

  it('returns undefined on non-URL text', () => {
    expect(findPlainTextUrlAt(wrapped(true), 1, 0)).toBeUndefined()
  })
})
