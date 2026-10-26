#!/usr/bin/env python3
"""Keep the hermes-tui-minimal look applied to a Hermes Agent checkout (idempotent).

What it does to the Hermes TUI source (ui-tui/src):
  1. Hides the startup intro: the "hermes" banner/tagline and the big
     session box (version / tools / skills / MCP).
  2. Frames the prompt with a thin full-width line above and below it.
  3. Turns the status strip into plain dim text (no leading/inline dashes);
     display.tui_statusbar=bottom puts it under the bottom line.
  4. Drops the kaomoji face in front of the thinking verb.
  5. /model picker lists only set-up providers: no "(no key)" rows, and
     model_catalog.excluded_providers also hides `providers:` config rows
     (hermes_cli/inventory.py).
  6-16. Copy-on-select over SSH (OSC 52), Terminal.app redraw fixes, status
     strip extras (cost / turn time / git branch / hints), tool rows with
     green ✓ / red ✗, context as numbers only.
  17. "Editorial" reply markdown: distinct heading levels, shaded code blocks,
     accent bullets, quote bar, │ tables, inline-code chips (skin key code_bg).

Each patch is an exact-string anchor against upstream; if upstream changes a
file, apply.py prints which anchor no longer matches instead of guessing.

The TUI rebuilds itself from source on the next launch when these files change.

Usage:
  apply.py            apply (no-op if already applied)
  apply.py --check    exit 1 if not fully applied
  apply.py --revert   restore the original upstream files (git restore)
  -q                  quiet unless something fails
"""
import subprocess
import sys
from pathlib import Path

import os
ROOT = Path(os.environ.get("HERMES_AGENT_ROOT") or Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes") / "hermes-agent")
SRC = ROOT / "ui-tui" / "src" / "components"
MARK = "hermes-minimal-ui"
RULE = "<Text color={ui.theme.color.border}>{'─'.repeat(Math.max(1, composer.cols - 2)) /* hermes-minimal-ui */}</Text>"
# TS helper block (cost / turn-time / hint labels) inserted into appChrome.tsx — patch 12.
MINIMAL_HELPERS = (Path(__file__).resolve().parent / "appChrome.helpers.ts").read_text(encoding="utf-8")

PATCHES = {
    SRC / "appLayout.tsx": [
        # 11. thinking verb on the row just above the prompt (replaces the blank
        #     spacer row, so the layout height doesn't change while busy)
        (
            "import { GoodVibesHeart, StatusRule, StickyPromptTracker, TranscriptScrollbar } from './appChrome.js'",
            "import { FaceTicker, GoodVibesHeart, StatusRule, StickyPromptTracker, TranscriptScrollbar } from './appChrome.js' // hermes-minimal-ui",
        ),
        (
            "      {status.showStickyPrompt ? (\n        <Text color={ui.theme.color.muted} wrap=\"truncate-end\">\n",
            "      {ui.busy /* hermes-minimal-ui */ ? (\n"
            "        <Box height={1}>\n"
            "          <FaceTicker color={status.statusColor} style={ui.indicatorStyle} verbOverride={ui.compacting ? 'compacting' : undefined} />\n"
            "        </Box>\n"
            "      ) : status.showStickyPrompt ? (\n        <Text color={ui.theme.color.muted} wrap=\"truncate-end\">\n",
        ),
        # 1. hide intro (banner + session box)
        (
            "          {row.msg.kind === 'intro' ? (\n            nativeMode ? null : (",
            "          {row.msg.kind === 'intro' ? (\n            /* hermes-minimal-ui */ Boolean(1) ? null : nativeMode ? null : (",
        ),
        # 2a. no extra blank row above the framed prompt
        (
            "marginTop={nativeMode || ui.statusBar === 'top' ? 0 : 1}",
            "marginTop={0 /* hermes-minimal-ui */}",
        ),
        # 12. git branch prop into the status strip
        (
            "        cwdLabel={status.cwdLabel}\n        focusView={ui.focusView}\n",
            "        cwdLabel={status.cwdLabel}\n        focusView={ui.focusView}\n        gitBranch={status.gitBranch /* hermes-minimal-ui */}\n",
        ),
        # 2b. line above prompt
        (
            "        {!isBlocked && (\n          <>\n            {composer.inputBuf.map(",
            "        {!isBlocked && (\n          <>\n            " + RULE + "\n"
            "            {composer.inputBuf.map(",
        ),
        # 2c. line below prompt
        (
            "                <GoodVibesHeart t={ui.theme} tick={status.goodVibesTick} />\n"
            "              </Box>\n            </Box>\n          </>",
            "                <GoodVibesHeart t={ui.theme} tick={status.goodVibesTick} />\n"
            "              </Box>\n            </Box>\n            " + RULE + "\n          </>",
        ),
    ],
    SRC / "appChrome.tsx": [
        # 4. no kaomoji/emoji face in front of the thinking verb
        (
            "return { frame: frames[tick % frames.length] ?? '', intervalMs: FACE_TICK_MS, showVerb: true }",
            "return { frame: frames.length < 0 ? '' : '' /* hermes-minimal-ui */, intervalMs: FACE_TICK_MS, showVerb: true }",
        ),
        (
            "  if (style === 'kaomoji') {\n    return kaomojiFrameWidth()\n  }",
            "  if (style === 'kaomoji') {\n    return 0 /* hermes-minimal-ui */\n  }",
        ),
        # 3. status strip: plain text, same widths
        (
            "<Text color={t.color.border}>{'─ '}</Text>",
            "<Text color={t.color.border}>{'  ' /* hermes-minimal-ui */}</Text>",
        ),
        (
            "<Text color={t.color.border}>{separatorWidth >= 3 ? ' ─ ' : ' '}</Text>",
            "<Text color={t.color.border}>{separatorWidth >= 3 ? '   ' /* hermes-minimal-ui */ : ' '}</Text>",
        ),
        # 8. status strip: no cwd at bottom-right (shows as "~" in $HOME), no idle
        #    clock, no live-session count; context bar + % always shown (pinned,
        #    0% before the first turn). Session timer is off via status_bar.fields.
        (
            "  const rightLabel = sessionTitle && ok('title') ? ` ${sessionTitle} ` : cwdLabel\n",
            "  const rightLabel = sessionTitle && ok('title') ? ` ${sessionTitle} ` : minimalRightHints(busy, ok, cols) /* hermes-minimal-ui */\n",
        ),
        # 16. idle strip starts with the model: no "ready" word (other idle statuses still show)
        (
            "              {displayStatus(status)}\n",
            "              {status === 'ready' ? '' : displayStatus(status) /* hermes-minimal-ui */}\n",
        ),
        # 12. status strip: cost / last-turn time / git branch segments (opt-in via
        #     display.status_bar.fields: cost, turn_time, git_branch) and dim keyboard
        #     hints in the (otherwise empty) right slot while idle (field: hints).
        (
            "interface StatusRuleProps {\n  battery?: BatteryInfo | null\n",
            "interface StatusRuleProps {\n  battery?: BatteryInfo | null\n  gitBranch?: string /* hermes-minimal-ui */\n",
        ),
        (
            "export function StatusRule({\n  battery,\n  focusView,\n",
            "export function StatusRule({\n  battery,\n  gitBranch = '' /* hermes-minimal-ui */,\n  focusView,\n",
        ),
        (
            "  const showDuration = segs.duration && ok('duration') && !!sessionStartedAt && fits(SEP + MAX_DURATION_WIDTH)\n",
            "  // hermes-minimal-ui: session spend, last turn's wall time, git branch — all opt-in via\n"
            "  // display.status_bar.fields (cost / turn_time / git_branch), budgeted like every tail segment.\n"
            "  const costText = ok('cost') ? minimalCostLabel(usage.cost_usd, usage.cost_status) : ''\n"
            "  const showCost = !!costText && fits(SEP + stringWidth(costText))\n"
            "  const turnText = ok('turn_time') ? minimalTurnLabel(busy, turnStartedAt, lastTurnEndedAt) : ''\n"
            "  const showTurnTime = !!turnText && fits(SEP + stringWidth(turnText))\n"
            "  const branchText = ok('git_branch') && gitBranch ? `⎇ ${gitBranch}` : ''\n"
            "  const showBranch = !!branchText && fits(SEP + stringWidth(branchText))\n"
            "  const showDuration = segs.duration && ok('duration') && !!sessionStartedAt && fits(SEP + MAX_DURATION_WIDTH)\n",
        ),
        (
            "            <SessionDuration startedAt={sessionStartedAt!} />\n          </Text>\n        ) : null}\n",
            "            <SessionDuration startedAt={sessionStartedAt!} />\n          </Text>\n        ) : null}\n"
            "        {showCost ? (\n"
            "          <Text color={t.color.muted} wrap=\"truncate-end\">\n"
            "            {' │ '}\n"
            "            <Text color={t.color.label}>{costText /* hermes-minimal-ui */}</Text>\n"
            "          </Text>\n"
            "        ) : null}\n"
            "        {showTurnTime ? (\n"
            "          <Text color={t.color.muted} wrap=\"truncate-end\">\n"
            "            {' │ '}\n"
            "            {turnText /* hermes-minimal-ui */}\n"
            "          </Text>\n"
            "        ) : null}\n"
            "        {showBranch ? (\n"
            "          <Text color={t.color.muted} wrap=\"truncate-end\">\n"
            "            {' │ '}\n"
            "            <Text color={t.color.accent}>{branchText /* hermes-minimal-ui */}</Text>\n"
            "          </Text>\n"
            "        ) : null}\n",
        ),
        (
            "export function GoodVibesHeart({ tick, t }: { tick: number; t: Theme }) {\n",
            MINIMAL_HELPERS + "export function GoodVibesHeart({ tick, t }: { tick: number; t: Theme }) {\n",
        ),
        (
            "    segs.duration && !busy && lastTurnEndedAt != null && fits(",
            "    Boolean(0) /* hermes-minimal-ui */ && segs.duration && !busy && lastTurnEndedAt != null && fits(",
        ),
        (
            "  const showSessionCount = !!sessionCountText && fits(",
            "  const showSessionCount = Boolean(0) /* hermes-minimal-ui */ && !!sessionCountText && fits(",
        ),
        (
            "  const bar = !segs.compactCtx && usage.context_max && ok('context_pct') ? ctxBar(pct) : ''\n",
            "  const bar = ok('context_pct') ? ctxBar(pct) : '' /* hermes-minimal-ui */\n",
        ),
        (
            "  const showBar = !!bar && fits(SEP + stringWidth(`[${bar}] ${pct != null ? `${contextMark}${pct}%` : ''}`))\n",
            "  const showBar = !!bar /* hermes-minimal-ui */\n",
        ),
        (
            "<Text color={barColor}>{pct != null ? `${contextMark}${pct}%` : ''}</Text>",
            "<Text color={barColor}>{`${contextMark}${pct ?? 0}%` /* hermes-minimal-ui */}</Text>",
        ),
        # 10. context shown as numbers only (no [████░░] bar)
        (
            "            <Text color={barColor}>[{bar}]</Text>{' '}\n",
            "            <Text color={barColor}>{bar ? '' : '' /* hermes-minimal-ui */}</Text>\n",
        ),
        # 11. thinking verb moves to the row above the prompt (appLayout); the
        #     status strip shows nothing in its slot while busy.
        (
            "function FaceTicker({\n  color,",
            "export /* hermes-minimal-ui */ function FaceTicker({\n  color,",
        ),
        (
            "          {busy ? (\n            <FaceTicker\n",
            "          {busy ? (\n            Boolean(1) /* hermes-minimal-ui */ ? null : <FaceTicker\n",
        ),
        (
            "            {' │ '}\n            {modelText}\n",
            "            {busy || status === 'ready' ? '' : ' │ ' /* hermes-minimal-ui */}\n            {modelText}\n",
        ),
    ],
    # 6. Copy-on-select also for macOS Terminal.app over SSH (node runs on Linux,
    #    so upstream's isMac gate skips it; Terminal.app swallows Cmd+C while the
    #    TUI owns the mouse). Copy travels back via OSC 52 (works on Tahoe Terminal).
    SRC.parent / "app" / "useMainApp.ts": [
        # 9. Terminal.app over SSH sometimes keeps stale cells (stray dots from the
        #    busy "thinking… · 12s" strip) that Ink's diff never repaints. Force one
        #    full repaint each time a turn ends (same as Ctrl+L / /redraw).
        (
            "  useEffect(() => {\n    if (dashboardFreshSessionId) {\n      forceRedraw(stdout ?? process.stdout)\n    }\n  }, [dashboardFreshSessionId, stdout])\n",
            "  useEffect(() => {\n    if (dashboardFreshSessionId) {\n      forceRedraw(stdout ?? process.stdout)\n    }\n  }, [dashboardFreshSessionId, stdout])\n\n"
            "  const wasBusyRef = useRef(false) /* hermes-minimal-ui */\n\n"
            "  useEffect(() => {\n"
            "    if (wasBusyRef.current && !ui.busy && (process.env.TERM_PROGRAM ?? '').trim() === 'Apple_Terminal') {\n"
            "      setTimeout(() => forceRedraw(stdout ?? process.stdout), 150).unref?.()\n"
            "    }\n\n"
            "    wasBusyRef.current = ui.busy\n"
            "  }, [ui.busy, stdout])\n",
        ),
        (
            "  useEffect(() => {\n    if (!isMac) {\n      return\n    }\n\n    return selection.subscribe(",
            "  useEffect(() => {\n    if (!isMac && (process.env.TERM_PROGRAM ?? '').trim() !== 'Apple_Terminal' /* hermes-minimal-ui */) {\n      return\n    }\n\n    return selection.subscribe(",
        ),
        # 13. "✓ copied N chars" notice after a drag-select (⌘C can't reach the app while
        #     the TUI owns the mouse, so make the auto-copy visible).
        (
            "      lastCopiedVersionRef.current = version\n      void selection.copySelectionNoClear()\n    })\n  }, [selection])\n",
            "      lastCopiedVersionRef.current = version\n"
            "      void selection.copySelectionNoClear().then(copied => {\n"
            "        // hermes-minimal-ui: ⌘C never reaches the app while the TUI owns the mouse, so\n"
            "        // say that the drag itself already copied (OSC 52) — otherwise it looks broken.\n"
            "        if (copied) {\n"
            "          turnController.showNotice({\n"
            "            key: 'copy.selection',\n"
            "            kind: 'ttl',\n"
            "            level: 'success',\n"
            "            text: `✓ copied ${copied.length.toLocaleString()} chars · ⌘V to paste`,\n"
            "            ttl_ms: 2500\n"
            "          })\n"
            "        }\n"
            "      })\n"
            "    })\n  }, [selection])\n",
        ),
        # 12. git branch reaches the status strip as its own prop
        (
            "      cwdLabel: fmtProjectCwdBranch(cwd, gitBranch, ui.info?.project?.name, 28),\n      goodVibesTick,\n",
            "      cwdLabel: fmtProjectCwdBranch(cwd, gitBranch, ui.info?.project?.name, 28),\n      gitBranch: gitBranch ?? '' /* hermes-minimal-ui */,\n      goodVibesTick,\n",
        ),
    ],
    SRC.parent / "app" / "interfaces.ts": [
        (
            "export interface AppLayoutStatusProps {\n  cwdLabel: string\n  goodVibesTick: number\n",
            "export interface AppLayoutStatusProps {\n  cwdLabel: string\n  gitBranch?: string /* hermes-minimal-ui */\n  goodVibesTick: number\n",
        ),
    ],
    # 14. Prompt-box copy over SSH: writeClipboardText only knew xclip/xsel/wl-copy (absent,
    #     and they'd hit the SERVER clipboard anyway). Over SSH go straight to OSC 52.
    SRC.parent / "lib" / "clipboard.ts": [
        (
            "import { execFile, spawn } from 'node:child_process'\nimport { promisify } from 'node:util'\n",
            "import { execFile, spawn } from 'node:child_process'\nimport { promisify } from 'node:util'\n\nimport { writeOsc52Clipboard } from './osc52.js' // hermes-minimal-ui\n",
        ),
        (
            "  const candidates = writeClipboardCommands(platform, env)\n\n  for (const cmdEntry of candidates) {\n",
            "  const candidates = writeClipboardCommands(platform, env)\n\n"
            "  // hermes-minimal-ui: over SSH the native tools (xclip/xsel/wl-copy) would write the\n"
            "  // REMOTE box's clipboard, if they exist at all. Go straight to OSC 52, which rides the\n"
            "  // pty back to the user's terminal (Terminal.app, iTerm2, Ghostty, kitty, WezTerm…).\n"
            "  if (env === process.env && (env.SSH_CONNECTION || env.SSH_TTY || env.SSH_CLIENT) && !env.TMUX && !env.STY) {\n"
            "    writeOsc52Clipboard(text)\n\n"
            "    return true\n"
            "  }\n\n"
            "  for (const cmdEntry of candidates) {\n",
        ),
    ],
    # 14b. Prompt-box drag-select auto-copies on Terminal.app over SSH too (upstream: macOS only).
    SRC / "textInput.tsx": [
        (
            "    if (isMac && normalized) {\n      void writeClipboardText(vRef.current.slice(normalized.start, normalized.end))\n",
            "    if (normalized && (isMac || (process.env.TERM_PROGRAM ?? '').trim() === 'Apple_Terminal') /* hermes-minimal-ui */) {\n      void writeClipboardText(vRef.current.slice(normalized.start, normalized.end))\n",
        ),
    ],
    # 15. Finished tool rows: green ✓ / red ✗ instead of the same ● for every state.
    SRC / "thinking.tsx": [
        (
            "  details: DetailRow[]\n  key: string\n  label: string\n}\n",
            "  details: DetailRow[]\n  key: string\n  label: string\n  mark?: string /* hermes-minimal-ui: finished-call outcome ✓ or ✗ */\n}\n",
        ),
        (
            "        details: [],\n        key: `tr-${i}`,\n        label: parsed.call\n      })\n",
            "        details: [],\n        key: `tr-${i}`,\n        label: parsed.call,\n        mark: parsed.mark /* hermes-minimal-ui */\n      })\n",
        ),
        (
            "                    <>\n                      <Text color={t.color.tool}>● </Text>\n                      {toolLabel(group)}\n",
            "                    <>\n"
            "                      {group.mark === '✓' ? (\n"
            "                        <Text color={t.color.ok}>{'✓ ' /* hermes-minimal-ui */}</Text>\n"
            "                      ) : group.mark === '✗' ? (\n"
            "                        <Text color={t.color.error}>{'✗ ' /* hermes-minimal-ui */}</Text>\n"
            "                      ) : (\n"
            "                        <Text color={t.color.tool}>● </Text>\n"
            "                      )}\n"
            "                      {toolLabel(group)}\n",
        ),
    ],
    # 17. Reply markdown, "Editorial" style: heading levels look different (H1 bold
    #     primary + full rule, H2 bold accent, H3+ bold primary), code blocks get a
    #     shaded fill with a left gutter and a right-aligned language tag, accent
    #     bullets/numbers (nested bullets use ◦), accent quote bar with italic text,
    #     inline code on the selection fill, table header in primary with │ columns,
    #     half-width horizontal rules. Skin key `code_bg` (theme.ts) feeds the fill.
    SRC / "markdown.tsx": [
        (
            "function MdImpl({ cols, compact, t, text }: MdProps) {\n",
            "// hermes-minimal-ui: heading levels get distinct looks (H1 primary + rule, H2 accent, H3+ primary)\n"
            "function renderHeading(level: number, text: string, key: number, t: Theme, cols: number | undefined): ReactNode {\n"
            "  const title = (\n"
            "    <Text bold color={level === 2 ? t.color.accent : t.color.primary} wrap=\"wrap-trim\">\n"
            "      <MdInline t={t} text={text} />\n"
            "    </Text>\n"
            "  )\n"
            "\n"
            "  if (level !== 1) {\n"
            "    return <Fragment key={key}>{title}</Fragment>\n"
            "  }\n"
            "\n"
            "  return (\n"
            "    <Box flexDirection=\"column\" key={key}>\n"
            "      {title}\n"
            "      <Text color={t.color.border}>{'─'.repeat(Math.max(8, Math.min(cols ?? 80, 120) - 1))}</Text>\n"
            "    </Box>\n"
            "  )\n"
            "}\n"
            "\n"
            "function MdImpl({ cols, compact, t, text }: MdProps) {\n",
        ),
        (
            "      const heading = line.match(HEADING_RE)?.[2]\n"
            "\n"
            "      if (heading) {\n"
            "        start('heading')\n"
            "        nodes.push(\n"
            "          <Text bold color={t.color.accent} key={key} wrap=\"wrap-trim\">\n"
            "            <MdInline t={t} text={heading} />\n"
            "          </Text>\n"
            "        )\n",
            "      const headingMatch = line.match(HEADING_RE) /* hermes-minimal-ui */\n"
            "      const heading = headingMatch?.[2]\n"
            "\n"
            "      if (heading) {\n"
            "        start('heading')\n"
            "        nodes.push(renderHeading(headingMatch![1]!.length, heading, key, t, cols))\n",
        ),
        (
            "      if (i + 1 < lines.length && SETEXT_RE.test(lines[i + 1]!)) {\n"
            "        start('heading')\n"
            "        nodes.push(\n"
            "          <Text bold color={t.color.accent} key={key} wrap=\"wrap-trim\">\n"
            "            <MdInline t={t} text={line.trim()} />\n"
            "          </Text>\n"
            "        )\n",
            "      if (i + 1 < lines.length && SETEXT_RE.test(lines[i + 1]!)) {\n"
            "        start('heading')\n"
            "        nodes.push(renderHeading(lines[i + 1]!.trim().startsWith('=') ? 1 : 2, line.trim(), key, t, cols)) /* hermes-minimal-ui */\n",
        ),
        # code block: shaded fill + gutter + right-aligned language tag
        (
            "        nodes.push(\n"
            "          <Box flexDirection=\"column\" key={key} paddingLeft={2}>\n"
            "            {lang && !isDiff && <Text color={t.color.muted}>{'─ ' + lang}</Text>}\n"
            "\n"
            "            {block.map((l, j) => {\n"
            "              if (highlighted) {\n"
            "                return (\n"
            "                  <Text key={j}>\n"
            "                    {highlightLine(l, lang, t).map(([color, text], kk) =>\n"
            "                      color ? (\n"
            "                        <Text color={color} key={kk}>\n"
            "                          {text}\n"
            "                        </Text>\n"
            "                      ) : (\n"
            "                        <Text key={kk}>{text}</Text>\n"
            "                      )\n"
            "                    )}\n"
            "                  </Text>\n"
            "                )\n"
            "              }\n",
            "        const codeBg = isDiff ? undefined : t.color.codeBg || undefined /* hermes-minimal-ui */\n"
            "        const codeW = Math.min(\n"
            "          Math.max(lang.length + 4, ...block.map(l => stringWidth(l) + 4)),\n"
            "          Math.max(24, (cols ?? 80) - 4)\n"
            "        )\n"
            "        const codePad = (l: string) => ' '.repeat(Math.max(0, codeW - 2 - stringWidth(l)))\n"
            "\n"
            "        nodes.push(\n"
            "          <Box flexDirection=\"column\" key={key} paddingLeft={2}>\n"
            "            {lang && isDiff && <Text color={t.color.muted}>{'─ ' + lang}</Text>}\n"
            "            {!isDiff && (\n"
            "              <Text backgroundColor={codeBg}>\n"
            "                <Text color={t.color.border}>{'▏'}</Text>\n"
            "                {' '.repeat(Math.max(0, codeW - 2 - lang.length))}\n"
            "                <Text color={t.color.muted} italic>\n"
            "                  {lang}\n"
            "                </Text>\n"
            "                {' '}\n"
            "              </Text>\n"
            "            )}\n"
            "\n"
            "            {block.map((l, j) => {\n"
            "              if (highlighted) {\n"
            "                return (\n"
            "                  <Text backgroundColor={codeBg} key={j}>\n"
            "                    <Text color={t.color.border}>{'▏ '}</Text>\n"
            "                    {highlightLine(l, lang, t).map(([color, text], kk) =>\n"
            "                      color ? (\n"
            "                        <Text color={color} key={kk}>\n"
            "                          {text}\n"
            "                        </Text>\n"
            "                      ) : (\n"
            "                        <Text key={kk}>{text}</Text>\n"
            "                      )\n"
            "                    )}\n"
            "                    {codePad(l)}\n"
            "                  </Text>\n"
            "                )\n"
            "              }\n"
            "\n"
            "              if (!isDiff) {\n"
            "                return (\n"
            "                  <Text backgroundColor={codeBg} key={j}>\n"
            "                    <Text color={t.color.border}>{'▏ '}</Text>\n"
            "                    {l}\n"
            "                    {codePad(l)}\n"
            "                  </Text>\n"
            "                )\n"
            "              }\n",
        ),
        (
            "                  {l}\n"
            "                </Text>\n"
            "              )\n"
            "            })}\n"
            "          </Box>\n"
            "        )\n"
            "\n"
            "        continue\n"
            "      }\n"
            "\n"
            "      const mathOpen = line.match(MATH_BLOCK_OPEN_RE)\n",
            "                  {l}\n"
            "                </Text>\n"
            "              )\n"
            "            })}\n"
            "            {!isDiff && <Text backgroundColor={codeBg}>{' '.repeat(codeW)}</Text> /* hermes-minimal-ui */}\n"
            "          </Box>\n"
            "        )\n"
            "\n"
            "        continue\n"
            "      }\n"
            "\n"
            "      const mathOpen = line.match(MATH_BLOCK_OPEN_RE)\n",
        ),
        # horizontal rule: half the width instead of a fixed 36
        (
            "            {'─'.repeat(36)}\n",
            "            {'─'.repeat(Math.max(16, Math.floor(Math.min(cols ?? 80, 120) / 2))) /* hermes-minimal-ui */}\n",
        ),
        # bullets: accent •, nested ◦
        (
            "        const marker = task ? (task[1]!.toLowerCase() === 'x' ? '☑' : '☐') : '•'\n",
            "        const nested = indentDepth(bullet[1]!) > 0 /* hermes-minimal-ui */\n"
            "        const marker = task ? (task[1]!.toLowerCase() === 'x' ? '☑' : '☐') : nested ? '◦' : '•'\n",
        ),
        (
            "              <Text color={t.color.muted}>{marker} </Text>\n",
            "              <Text color={nested ? t.color.muted : t.color.accent}>{marker} </Text>\n",
        ),
        # numbered lists: bold accent number
        (
            "              <Text color={t.color.muted}>{numbered[2]}. </Text>\n",
            "              <Text bold color={t.color.accent}>{numbered[2]}. </Text>\n",
        ),
        # block quote: accent bar, italic label-tone text
        (
            "                <Text color={t.color.muted} wrap=\"wrap-trim\">\n"
            "                  │ <MdInline t={t} text={ql.text} />\n"
            "                </Text>\n",
            "                <Text wrap=\"wrap-trim\">\n"
            "                  <Text color={t.color.accent}>{'▌ '}</Text>\n"
            "                  <Text color={t.color.label} italic>\n"
            "                    <MdInline t={t} text={ql.text} />\n"
            "                  </Text>\n"
            "                </Text>\n",
        ),
        # inline code: selection fill + primary text instead of dim accent
        (
            "        <Text color={t.color.accent} dimColor key={parts.length}>\n"
            "          {m[7]}\n",
            "        <Text backgroundColor={t.color.selectionBg} color={t.color.primary} key={parts.length}>\n"
            "          {m[7]}\n",
        ),
        # tables: │ column separators, ┼ in the header rule, primary header text
        (
            "const COL_GAP = 2 // the '  ' between columns\n",
            "const COL_GAP = 3 // the ' │ ' between columns (hermes-minimal-ui)\n",
        ),
        (
            "  const sep = columnWidths.map(w => '─'.repeat(Math.max(1, w))).join('  ')\n",
            "  const sep = columnWidths.map(w => '─'.repeat(Math.max(1, w))).join('─┼─')\n",
        ),
        (
            "          const gap = ci < numCols - 1 ? '  ' : ''\n",
            "          const gap = ci < numCols - 1 ? ' │ ' : ''\n",
        ),
        (
            "        if (ci < numCols - 1) {\n          line += '  '\n        }\n",
            "        if (ci < numCols - 1) {\n          line += ' │ '\n        }\n",
        ),
        (
            "            <Text bold={ri === 0} color={ri === 0 ? t.color.accent : undefined} wrap=\"truncate-end\">\n",
            "            <Text bold={ri === 0} color={ri === 0 ? t.color.primary : undefined} wrap=\"truncate-end\">\n",
        ),
        (
            "          color={entry.kind === 'header' ? t.color.accent : entry.kind === 'separator' ? t.color.muted : undefined}\n",
            "          color={entry.kind === 'header' ? t.color.primary : entry.kind === 'separator' ? t.color.muted : undefined}\n",
        ),
    ],
    # 17. `code_bg` skin key → theme.color.codeBg (code-block fill in markdown.tsx)
    ROOT / "ui-tui" / "src" / "theme.ts": [
        (
            "  selectionBg: string\n\n  diffAdded: string\n",
            "  selectionBg: string\n  /** Code-block fill (skin `code_bg`); '' = no fill. hermes-minimal-ui */\n  codeBg: string\n\n  diffAdded: string\n",
        ),
        (
            "    selectionBg: seeds.selection ?? tones.selection,\n",
            "    selectionBg: seeds.selection ?? tones.selection,\n    codeBg: '' /* hermes-minimal-ui */,\n",
        ),
        (
            "    selectionBg: c('selection_bg') ?? c('completion_menu_current_bg') ?? derived.selectionBg,\n",
            "    selectionBg: c('selection_bg') ?? c('completion_menu_current_bg') ?? derived.selectionBg,\n"
            "    codeBg: c('code_bg') ?? '' /* hermes-minimal-ui */,\n",
        ),
    ],
    # 12. session spend rides the session.usage frame (cost_usd / cost_status) so the
    #     TUI status strip can show it. Needs a gateway restart.
    ROOT / "gateway" / "session_usage.py": [
        (
            "    if (gauge := plan_gauge(agent)) is not None:  # absent off a window plan, as on the embedded path\n"
            "        stats[\"plan_gauge\"] = gauge\n    return stats\n",
            "    if (gauge := plan_gauge(agent)) is not None:  # absent off a window plan, as on the embedded path\n"
            "        stats[\"plan_gauge\"] = gauge\n"
            "    with contextlib.suppress(Exception):  # hermes-minimal-ui: session spend for the TUI status bar\n"
            "        _cost = getattr(agent, \"session_estimated_cost_usd\", None)\n"
            "        if isinstance(_cost, (int, float)) and _cost == _cost:\n"
            "            stats[\"estimated_cost_usd\"] = float(_cost)\n"
            "            stats[\"cost_status\"] = str(getattr(agent, \"session_cost_status\", \"\") or \"unknown\")\n"
            "    return stats\n",
        ),
        (
            "    if isinstance(stats.get(\"plan_gauge\"), dict):\n        usage[\"plan_gauge\"] = stats[\"plan_gauge\"]\n    return usage\n",
            "    if isinstance(stats.get(\"plan_gauge\"), dict):\n        usage[\"plan_gauge\"] = stats[\"plan_gauge\"]\n"
            "    if isinstance(stats.get(\"estimated_cost_usd\"), (int, float)):  # hermes-minimal-ui\n"
            "        usage[\"cost_usd\"] = round(float(stats[\"estimated_cost_usd\"]), 4)\n"
            "        usage[\"cost_status\"] = stats.get(\"cost_status\") or \"unknown\"\n"
            "    return usage\n",
        ),
    ],
    # 7. No stray "p" bottom-left in Terminal.app: the mouse watchdog sends a
    #    DECRQM probe (ESC[?1000$p) with the cursor parked at the last row, col 1.
    #    Terminal.app doesn't parse DECRQM and prints the final "p" there. Skip the
    #    probe on Apple_Terminal (it never answers DECRQM anyway).
    ROOT / "ui-tui" / "packages" / "hermes-ink" / "src" / "ink" / "components" / "App.tsx": [
        (
            "  mouseWatchdogUnsupported = false\n",
            "  mouseWatchdogUnsupported = (process.env.TERM_PROGRAM ?? '').trim() === 'Apple_Terminal' /* hermes-minimal-ui */\n",
        ),
    ],
    # 5. /model picker: only providers that are actually set up.
    SRC / "modelPicker.tsx": [
        # no "(no key)" setup rows for unconfigured providers
        (
            "      include_unconfigured: true\n",
            "      include_unconfigured: false /* hermes-minimal-ui */\n",
        ),
    ],
    ROOT / "hermes_cli" / "inventory.py": [
        # model_catalog.excluded_providers also hides `providers:` config rows
        # (upstream only filters built-in rows), so the picker shows just the
        # providers you keep.
        (
            "    if explicit_only:\n        rows = _filter_explicit_provider_rows(rows, ctx)\n",
            "    _excl = {str(p).strip().lower() for p in (ctx.excluded_providers or []) if p}  # hermes-minimal-ui\n"
            "    rows = [r for r in rows if _slug(r) not in _excl and _slug(r).removeprefix(\"custom:\") not in _excl]\n"
            "    if explicit_only:\n        rows = _filter_explicit_provider_rows(rows, ctx)\n",
        ),
    ],
}


def say(msg, quiet):
    if not quiet:
        print(msg)


def main():
    args = set(sys.argv[1:])
    quiet = "-q" in args

    if not (ROOT / "ui-tui" / "src").is_dir():
        print(f"[minimal-ui] no Hermes source checkout at {ROOT} (set HERMES_AGENT_ROOT)", file=sys.stderr)
        return 1

    if "--revert" in args:
        files = [str(p.relative_to(ROOT)) for p in PATCHES]
        subprocess.run(["git", "restore", "--", *files], cwd=ROOT, check=True)
        print("minimal UI reverted (restart the TUI)")
        return 0

    missing, changed = [], []
    for path, patches in PATCHES.items():
        text = path.read_text(encoding="utf-8")
        new = text
        for old, rep in patches:
            if rep in new:
                continue  # already applied
            if old not in new:
                missing.append(f"{path.name}: {old.splitlines()[0].strip()[:70]}")
                continue
            new = new.replace(old, rep, 1)
        if new != text:
            if "--check" in args:
                changed.append(path.name)
                continue
            path.write_text(new, encoding="utf-8")
            changed.append(path.name)

    if "--check" in args:
        ok = not changed and not missing
        say("minimal UI: applied" if ok else f"minimal UI: NOT applied ({', '.join(changed + missing)})", quiet and ok)
        return 0 if ok else 1

    if missing:
        print(
            "[minimal-ui] Hermes TUI code changed upstream; could not re-apply:\n  "
            + "\n  ".join(missing)
            + "\n  Fix the anchor in apply.py (or open an issue at github.com/saumya-dabi/hermes-tui-minimal).",
            file=sys.stderr,
        )
    if changed:
        say(f"[minimal-ui] applied to {', '.join(changed)} (TUI rebuilds on next launch)", quiet)
    elif not missing:
        say("[minimal-ui] already applied", quiet)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
