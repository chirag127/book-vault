from __future__ import annotations

import argparse
import subprocess
import sys


def run(command: list[str]) -> int:
    print("$", " ".join(command), flush=True)
    return subprocess.run(command, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run guarded book-generation phases.")
    parser.add_argument("--phase", choices=("smoke", "one", "batch"), default="smoke")
    parser.add_argument("--slug", default="Make-It-Stick")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--loop", action="store_true", help="Keep processing pending books until the manifest is complete.")

    parser.add_argument("--sleep", type=int, default=300, help="Seconds between loop passes.")
    parser.add_argument("--workers", type=int, default=None, help="Books generated concurrently.")
    args = parser.parse_args()

    base = [sys.executable, "-m", "automation.generate"]
    if args.loop:
        base += ["--loop", "--sleep", str(args.sleep)]
    if args.workers:
        base += ["--workers", str(args.workers)]
    if args.phase == "smoke":
        return run(base + ["--limit", "1", "--dry-run"])
    if args.phase == "one":
        code = run(base + ["--slug", args.slug, "--limit", "1"])
    else:
        code = run(base + ["--limit", str(args.limit)])
    if code != 0:
        return code
    return run([sys.executable, "-m", "automation.validate_vault"])


if __name__ == "__main__":
    raise SystemExit(main())
