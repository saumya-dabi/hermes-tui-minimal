// hermes-minimal-ui #24: Mac clipboard bridge. macOS Terminal.app ignores OSC 52, so over SSH the
// copied text ALSO goes through an SSH RemoteForward: VM 127.0.0.1:47052 -> Mac launchd agent ->
// pbcopy. The Mac side replies "OK" only after pbcopy finished, so `true` = Mac clipboard really set.
// null = bridge not in play (local session or HERMES_CLIP_BRIDGE=0). Setup: clipbridge/README.md.
export function clipBridgeEnabled(env: NodeJS.ProcessEnv = process.env): boolean {
  if (/^(?:0|false|no|off)$/i.test((env.HERMES_CLIP_BRIDGE ?? '').trim())) {
    return false
  }

  return Boolean(env.SSH_CONNECTION || env.SSH_TTY || env.SSH_CLIENT)
}

export async function sendClipBridge(text: string, timeoutMs = 2500): Promise<boolean | null> {
  if (!text || !clipBridgeEnabled()) {
    return null
  }

  const port = Number(process.env.HERMES_CLIP_BRIDGE_PORT || 47052)
  const { connect } = await import('node:net')

  const ok = await new Promise<boolean>(resolve => {
    let reply = ''
    let done = false
    const sock = connect({ host: '127.0.0.1', port })

    const finish = (value: boolean) => {
      if (!done) {
        done = true
        clearTimeout(timer)
        sock.destroy()
        resolve(value)
      }
    }

    const timer = setTimeout(() => finish(false), timeoutMs)

    sock.setEncoding('utf8')
    sock.on('connect', () => sock.end(Buffer.from(text, 'utf8')))
    sock.on('data', (chunk: string) => {
      reply += chunk

      if (reply.includes('OK')) {
        finish(true)
      }
    })
    sock.on('end', () => finish(reply.includes('OK')))
    sock.on('error', () => finish(false))
  })

  ;(globalThis as { __hermesClipBridge?: { at: number; ok: boolean } }).__hermesClipBridge = { at: Date.now(), ok }

  return ok
}

