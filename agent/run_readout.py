"""
run_readout.py — CLI for the readout agent.

    python agent/run_readout.py                       # latest two snapshots
    python agent/run_readout.py 37a062e 4af3158       # explicit refs
    python agent/run_readout.py --model claude-haiku-4-5-20251001

Writes readouts/readout_<a>_<b>.md and prints the verdict summary.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import run_agent, format_readout, DEFAULT_MODEL  # noqa: E402
from tools import list_snapshots  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("refs", nargs="*", help="ref_a ref_b (earlier later)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    if len(args.refs) == 2:
        ref_a, ref_b = args.refs
    else:
        snaps = list_snapshots()
        if len(snaps) < 2:
            print("need at least two snapshots"); return
        ref_b, ref_a = snaps[0]["ref"], snaps[1]["ref"]
        print(f"using latest two snapshots: {ref_a} -> {ref_b}")

    print(f"\nrunning agent ({args.model})...")
    result = run_agent(ref_a, ref_b, model=args.model, verbose=not args.quiet)

    if not result["completed"]:
        print("\nAGENT DID NOT COMPLETE. Trace:")
        print(json.dumps(result["trace"], indent=2))
        return

    md = format_readout(result)
    outdir = os.path.join(REPO_ROOT, "readouts")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"readout_{ref_a}_{ref_b}.md")
    with open(path, "w") as f:
        f.write(md)

    v = result["verdict"]
    print("\n" + "=" * 62)
    print(v["headline"])
    print("=" * 62)
    print(f"confidence: {v['confidence']}   "
          f"comparison_valid: {v['comparison_valid']}")
    print(f"tool calls: {result['n_tool_calls']} -> {result['tools_called']}")
    concerns = v.get("data_quality_concerns") or []
    print(f"\ndata quality concerns ({len(concerns)}):")
    for c in concerns:
        print(f"  - {c}")
    print(f"\nwritten -> {path}")


if __name__ == "__main__":
    main()
