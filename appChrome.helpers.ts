// hermes-minimal-ui ── status-strip helpers ───────────────────────────────────
// Session spend: `$1.23` (exact) / `~$1.23` (estimated); sub-cent reads `<$0.01`.
// Hidden while the gateway reports nothing or an unknown price (omniroute "custom").
export function minimalCostLabel(cost: unknown, status: unknown): string {
  if (typeof cost !== 'number' || !Number.isFinite(cost) || cost <= 0) {
    return ''
  }

  if (status !== 'exact' && status !== 'estimated') {
    return ''
  }

  const mark = status === 'exact' ? '' : '~'

  return cost < 0.005 ? `${mark}<$0.01` : `${mark}$${cost.toFixed(2)}`
}

// Last turn's wall time (`⏱ 42s`). StatusRule is hook-free, so the start of the
// most recent turn is remembered at module level across renders.
let minimalLastTurnStart = 0
let minimalLastTurnMs = 0

export function minimalTurnLabel(busy: boolean, turnStartedAt?: null | number, lastTurnEndedAt?: null | number): string {
  if (busy && turnStartedAt) {
    minimalLastTurnStart = turnStartedAt

    return ''
  }

  if (!busy && lastTurnEndedAt && minimalLastTurnStart && lastTurnEndedAt >= minimalLastTurnStart) {
    minimalLastTurnMs = lastTurnEndedAt - minimalLastTurnStart
  }

  return minimalLastTurnMs > 0 ? `⏱ ${fmtDuration(minimalLastTurnMs)}` : ''
}

// Right-hand slot while idle and no session title: dim keyboard hints. Opt-out by
// dropping `hints` from display.status_bar.fields. Shrinks with the terminal.
export function minimalRightHints(busy: boolean, ok: (name: string) => boolean, cols: number): string {
  if (busy || !ok('hints')) {
    return ''
  }

  if (cols >= 120) {
    return ' ⇧↑↓ scroll · ^O model · ^X sessions · ^L redraw · /help '
  }

  if (cols >= 90) {
    return ' ⇧↑↓ scroll · ^O model · /help '
  }

  return ''
}

