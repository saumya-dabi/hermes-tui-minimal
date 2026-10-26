#!/usr/bin/env bash
# Would the next `hermes update` break a patch anchor? Fetches origin/main (no checkout
# change) and tests every apply.py anchor against it. Exit 0 = all fine (silent),
# exit 1 = prints the broken anchors. Cron it and alert on non-zero.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${HERMES_AGENT_ROOT:-${HERMES_HOME:-$HOME/.hermes}/hermes-agent}"
cd "$ROOT" || exit 2
git fetch -q origin main || exit 2
REPORT=$(python3 - "$HERE/apply.py" <<'PY'
import importlib.util, subprocess, sys
spec = importlib.util.spec_from_file_location("ap", sys.argv[1]); ap = importlib.util.module_from_spec(spec); spec.loader.exec_module(ap)
root = ap.ROOT; bad = []
for path, patches in ap.PATCHES.items():
    rel = path.relative_to(root)
    r = subprocess.run(["git", "show", f"origin/main:{rel}"], cwd=root, capture_output=True, text=True)
    if r.returncode:
        bad.append(f"{rel}: file missing upstream"); continue
    for old, _ in patches:
        olds = old if isinstance(old, tuple) else (old,)
        if not any(o in r.stdout for o in olds):
            bad.append(f"{rel}: {olds[0].splitlines()[0].strip()[:70]}")
print("\n".join(bad))
PY
) || { echo "check failed"; exit 2; }
[ -z "$REPORT" ] && exit 0
echo "hermes-tui-minimal: a hermes update would break these anchors (origin/main $(git rev-parse --short origin/main)):"
echo "$REPORT"
exit 1
