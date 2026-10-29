"""Command-line interface for journal-limits-checker."""
import argparse
import json

from .core import PRESETS, check_limits, measure


def main(argv=None):
    ap = argparse.ArgumentParser(prog="journal-limits-checker", description="Check a manuscript against journal limits.")
    ap.add_argument("manuscript", help=".tex or .md file")
    ap.add_argument("-p", "--preset", choices=sorted(PRESETS), default="research-article")
    ap.add_argument("-l", "--limits", help="JSON file with your journal's limits (overrides the preset)")
    ap.add_argument("--set", action="append", default=[], help="override one limit, e.g. --set body_words=4500")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    limits = dict(PRESETS[args.preset])
    if args.limits:
        with open(args.limits, encoding="utf-8") as fh:
            limits.update(json.load(fh))
    for s in args.set:
        k, _, v = s.partition("=")
        limits[k.strip()] = int(v)
    with open(args.manuscript, encoding="utf-8", errors="replace") as fh:
        m = measure(fh.read())
    rows = check_limits(m, limits)
    if args.json:
        print(json.dumps({"measured": m, "checks": rows}, indent=2))
    else:
        for item, v, lim, st in rows:
            flag = {"ok": "  ok ", "over": "OVER ", "under": "UNDER"}[st]
            pct = " (%d%%)" % (100 * v / lim) if isinstance(lim, int) and lim else ""
            print("%s %-16s %7s / %-6s%s" % (flag, item, v, lim, pct))
    return 1 if any(r[3] != "ok" for r in rows) else 0
