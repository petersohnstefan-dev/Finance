#!/usr/bin/env python
"""Run any script against a throwaway copy of data/ instead of the live files.

Merely constructing a PortfolioManager opens portfolio.db and applies pending
migrations, so even a read-only-looking test dirties the working tree and can
end up committed over the bot's own writes. This wrapper copies data/ to a
temporary directory, points FINANCE_DATA_DIR at it (see src/paths.py), runs the
target in a fresh interpreter, and then verifies that the real data/ is byte for
byte unchanged.

    python tools/sandbox_run.py my_test.py [args...]
    python tools/sandbox_run.py --keep my_test.py   # leave the sandbox for inspection
    python tools/sandbox_run.py -m src.market_scanner

Exit code is the target's, unless the real data directory was modified - that is
always a failure, because it means something bypassed src.paths.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def fingerprint(directory: str) -> dict:
    """SHA-256 per file, so a changed byte anywhere is detected."""
    out = {}
    for root, _dirs, files in os.walk(directory):
        for fn in sorted(files):
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, directory)
            try:
                with open(full, "rb") as fh:
                    digest = hashlib.sha256()
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        digest.update(chunk)
                    out[rel] = digest.hexdigest()
            except OSError:
                out[rel] = "<unlesbar>"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--keep", action="store_true",
                        help="Sandbox nach dem Lauf nicht loeschen")
    parser.add_argument("-m", dest="module", metavar="MODUL",
                        help="Modul statt Skript ausfuehren (wie python -m)")
    parser.add_argument("target", nargs="?", help="Auszufuehrendes Skript")
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if not args.module and not args.target:
        print(__doc__)
        return 2

    if not os.path.isdir(REAL_DATA_DIR):
        print(f"Kein data/-Verzeichnis unter {REAL_DATA_DIR}", file=sys.stderr)
        return 2

    before = fingerprint(REAL_DATA_DIR)

    sandbox = tempfile.mkdtemp(prefix="finance-sandbox-")
    sandbox_data = os.path.join(sandbox, "data")
    shutil.copytree(REAL_DATA_DIR, sandbox_data)

    env = dict(os.environ)
    env["FINANCE_DATA_DIR"] = sandbox_data
    env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    cmd = [sys.executable]
    cmd += ["-m", args.module] if args.module else [args.target]
    cmd += [a for a in args.rest if a != "--"]

    print(f"[sandbox] data/  -> {sandbox_data}")
    print(f"[sandbox] starte  {' '.join(cmd[1:])}\n", flush=True)

    result = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env)

    after = fingerprint(REAL_DATA_DIR)
    touched = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))

    print()
    if touched:
        print("[sandbox] FEHLER: echte Dateien wurden veraendert:", file=sys.stderr)
        for name in touched:
            print(f"            data/{name}", file=sys.stderr)
        print("          Ein Modul umgeht src.paths - dort den Pfad korrigieren.",
              file=sys.stderr)
    else:
        print("[sandbox] data/ unveraendert.")

    changed_in_sandbox = sorted(
        k for k, v in fingerprint(sandbox_data).items() if before.get(k) != v)
    if changed_in_sandbox:
        print(f"[sandbox] in der Kopie geschrieben: {', '.join(changed_in_sandbox)}")

    if args.keep:
        print(f"[sandbox] behalten: {sandbox}")
    else:
        shutil.rmtree(sandbox, ignore_errors=True)

    return 1 if touched else result.returncode


if __name__ == "__main__":
    sys.exit(main())
