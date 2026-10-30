// hermes-minimal-ui: no colour emoji anywhere in the TUI (⚡, ✅, ⏳, 🔑 …).
import { describe, expect, it } from 'vitest'

import { ensureEmojiPresentation, stripEmoji, stripEmojiDeep } from '../lib/emoji.js'

describe('stripEmoji', () => {
  it('drops a leading emoji and its space', () => {
    expect(stripEmoji('⚡ Loading bundle: x (3 skills)')).toBe('Loading bundle: x (3 skills)')
    expect(stripEmoji('💾 Self-improvement saved')).toBe('Self-improvement saved')
  })

  it('collapses an emoji between words to one space', () => {
    expect(stripEmoji('done ✅ next')).toBe('done next')
  })

  it('drops a trailing emoji and the space before it', () => {
    expect(stripEmoji('all good ✨')).toBe('all good')
  })

  it('handles VS16, ZWJ, skin tones and keycaps', () => {
    expect(stripEmoji('warn ⚠️ now')).toBe('warn now')
    expect(stripEmoji('team 👨‍👩‍👧 here')).toBe('team here')
    expect(stripEmoji('ok 👍🏽')).toBe('ok')
    expect(stripEmoji('step 1️⃣ go')).toBe('step 1 go')
  })

  it('works per line', () => {
    expect(stripEmoji('🔴 failed\n🟡 pending')).toBe('failed\npending')
  })

  it('keeps text symbols and plain text', () => {
    const s = '✓ done · ✗ fail ● ▸ ▾ │ › ⌘V ⚠ warn ☑ task → ← — ½ © 2026 #1'
    expect(stripEmoji(s)).toBe(s)
    expect(stripEmoji('')).toBe('')
  })

  it('markdown no longer forces emoji presentation and strips emoji', () => {
    expect(ensureEmojiPresentation('⚠ careful ⚡ fast')).toBe('⚠ careful fast')
  })

  it('deep-strips strings in event payloads', () => {
    const ev = { type: 'x', payload: { text: '⚡ hi', n: 3, list: ['✅ ok', null], ok: true } }
    expect(stripEmojiDeep(ev)).toEqual({ type: 'x', payload: { text: 'hi', n: 3, list: ['ok', null], ok: true } })
  })
})
