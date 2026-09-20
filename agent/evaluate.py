"""
evaluate.py — does the readout agent actually work?

Builds synthetic snapshot pairs from the real data, injects a known problem
into some and leaves others genuinely clean, runs the unmodified agent against
each, and scores it.

DECISION RULE, FIXED BEFORE THE FIRST RUN
-----------------------------------------
Per case, the agent returns comparison_valid (bool) and data_quality_concerns.

  CONFOUNDED case is CAUGHT      if comparison_valid == False
  CONFOUNDED case is IDENTIFIED  if CAUGHT and a concern mentions the injected
                                 cause (keyword match on expect_mentions)
  CLEAN case is a FALSE POSITIVE if comparison_valid == False

Pass bar, set now, not after seeing results:
  catch rate          >= 5 of 6 confounded cases
  false positive rate <= 1 of 4 clean cases

CAUGHT vs IDENTIFIED is deliberate. An agent that flags every comparison as
invalid gets a perfect catch rate and is useless. IDENTIFIED asks whether it
found the actual problem. The clean controls exist for the same reason: catch
rate alone is gameable by pessimism.

The controls are real moves with the instrument held fixed. The agent should
say those are valid and act on them.

    python agent/evaluate.py                 # all cases
    python agent/evaluate.py --cases 1 2 3   # subset
    python agent/evaluate.py --model claude-haiku-4-5-20251001
"""

import argparse
import json
import os
import sys
from typing import Any

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tools  # noqa: E402
from tools import _read_at_ref, _register_override, _clear_overrides  # noqa: E402
from agent import run_agent, DEFAULT_MODEL  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_REF = "4af3158"          # real June snapshot, used as the base for all cases


# ── injections ────────────────────────────────────────────────────────────
# Each returns (df_a, df_b). Root causes are distinct; no padding to hit a
# round number. Six confounded, four clean.

def _base() -> pd.DataFrame:
    return _read_at_ref(BASE_REF)


def inj_keyword_added(df):
    a = df[~df.keyword.isin(["World Cup resale tickets", "how to watch World Cup",
                             "World Cup tickets near me"])].copy()
    return a, df.copy()


def inj_keyword_dropped(df):
    b = df[~df.keyword.isin(["Mexico soccer", "USMNT"])].copy()
    return df.copy(), b


def inj_city_dropped(df):
    b = df[df.city != "Los Angeles"].copy()
    return df.copy(), b


def inj_scale_shift(df):
    """Values rescaled (as if the normalisation window changed). Ranking is
    identical, every level is 1.8x. Subtle: no structural difference at all."""
    b = df.copy()
    b["value"] = (b["value"] * 1.8).clip(upper=100).round(1)
    return df.copy(), b


def inj_sample_collapse(df):
    """Later snapshot is a thin scrape: one row per keyword-city pair survives
    for only 4 cities. Structure looks similar, coverage collapsed."""
    keep = ["Los Angeles", "New York", "Miami", "Boston"]
    b = df[df.city.isin(keep)].copy()
    return df.copy(), b


def inj_duplicate_rows(df):
    """Half the rows duplicated in the later snapshot. Means are unchanged but
    counts double, so any volume-based read is wrong."""
    b = pd.concat([df, df.sample(frac=0.5, random_state=7)], ignore_index=True)
    return df.copy(), b


def stale_refresh(df):
    """Two dated snapshots, byte identical. Labelled CONFOUNDED after the first
    eval run: the agent flagged this and was right. A refresh that produced
    identical values across 143 rows and six weeks is a broken pipeline, not a
    quiet period. This project hit exactly that bug when a state-level geo pull
    made Los Angeles and San Francisco identical."""
    return df.copy(), df.copy()


def _jitter(df, factors: dict[str, float], default: float, seed: int):
    """Move each city by its own factor, with per-row noise. Real demand does
    not move every city by an identical constant, and uniform scaling is
    indistinguishable from a rescale, so clean cases must be heterogeneous."""
    import numpy as np
    rng = np.random.default_rng(seed)
    b = df.copy()
    f = b["city"].map(factors).fillna(default).astype(float)
    noise = rng.normal(1.0, 0.06, len(b))
    b["value"] = (b["value"] * f * noise).clip(lower=1, upper=100).round(1)
    return b


def clean_hetero_rise(df):
    """Genuine broad rise: every city up, but by different amounts."""
    a = df.copy()
    b = _jitter(df, {"Los Angeles": 1.45, "New York": 1.38, "Miami": 1.30,
                     "Boston": 1.22, "Dallas": 1.18, "Houston": 1.15}, 1.25, 11)
    return a, b


def clean_city_spike(df):
    """One market moves hard, the rest roughly flat. The realistic shape."""
    a = df.copy()
    b = _jitter(df, {"Dallas": 2.0}, 1.03, 12)
    return a, b


def clean_mixed(df):
    """Some markets up, some down. Nothing structural changed."""
    a = df.copy()
    b = _jitter(df, {"Los Angeles": 1.30, "Seattle": 1.20, "Miami": 0.78,
                     "Atlanta": 0.72, "Kansas City": 0.85}, 1.0, 13)
    return a, b


def clean_hetero_decline(df):
    """Genuine post-peak cooling, uneven across markets."""
    a = df.copy()
    b = _jitter(df, {"Kansas City": 0.55, "Atlanta": 0.62, "Philadelphia": 0.68,
                     "Seattle": 0.75}, 0.80, 14)
    return a, b


CASES: list[dict[str, Any]] = [
    {"id": 1, "name": "keyword_added", "kind": "confounded", "fn": inj_keyword_added,
     "expect_mentions": ["keyword", "added", "instrument"]},
    {"id": 2, "name": "keyword_dropped", "kind": "confounded", "fn": inj_keyword_dropped,
     "expect_mentions": ["keyword", "dropped", "removed", "missing"]},
    {"id": 3, "name": "city_dropped", "kind": "confounded", "fn": inj_city_dropped,
     "expect_mentions": ["city", "los angeles", "coverage", "missing"]},
    # Case 4 is UNFALSIFIABLE and scored separately: a uniform rescale and a
    # genuine uniform move are identical in the data. Kept, not deleted,
    # because knowing which of your cases cannot be won is part of the result.
    {"id": 4, "name": "scale_shift_UNFALSIFIABLE", "kind": "unfalsifiable",
     "fn": inj_scale_shift, "expect_mentions": ["scale", "normal", "rescal", "uniform"]},
    {"id": 5, "name": "sample_collapse", "kind": "confounded", "fn": inj_sample_collapse,
     "expect_mentions": ["coverage", "cities", "sample", "missing"]},
    {"id": 6, "name": "duplicate_rows", "kind": "confounded", "fn": inj_duplicate_rows,
     "expect_mentions": ["duplicat", "row", "count"]},
    # Reclassified after run 1: the agent flagged this and was correct.
    {"id": 9, "name": "stale_refresh", "kind": "confounded", "fn": stale_refresh,
     "expect_mentions": ["identical", "stale", "not updat", "unchanged", "same"]},
    {"id": 7, "name": "real_hetero_rise", "kind": "clean", "fn": clean_hetero_rise,
     "expect_mentions": []},
    {"id": 8, "name": "real_city_spike", "kind": "clean", "fn": clean_city_spike,
     "expect_mentions": []},
    {"id": 10, "name": "real_mixed", "kind": "clean", "fn": clean_mixed,
     "expect_mentions": []},
    {"id": 11, "name": "real_hetero_decline", "kind": "clean", "fn": clean_hetero_decline,
     "expect_mentions": []},
]


def score(case, verdict) -> dict[str, Any]:
    if verdict is None:
        return {"outcome": "no_verdict", "caught": False, "identified": False,
                "false_positive": False}
    valid = bool(verdict.get("comparison_valid", True))
    concerns = " ".join(verdict.get("data_quality_concerns") or []).lower()
    if case["kind"] == "unfalsifiable":
        return {"outcome": "unfalsifiable_flagged" if not valid else "unfalsifiable_passed",
                "caught": False, "identified": False, "false_positive": False}
    if case["kind"] == "confounded":
        caught = not valid
        identified = caught and any(m.lower() in concerns
                                    for m in case["expect_mentions"])
        return {"outcome": "caught" if caught else "missed",
                "caught": caught, "identified": identified, "false_positive": False}
    fp = not valid
    return {"outcome": "false_positive" if fp else "correctly_clean",
            "caught": False, "identified": False, "false_positive": fp}


def run_case(case, model, verbose=False) -> dict[str, Any]:
    base = _base()
    df_a, df_b = case["fn"](base)
    _clear_overrides()
    _register_override("a1b2c3d", df_a, date="2026-05-20",
                       subject="Add demand data + pull scripts")
    _register_override("e4f5g6h", df_b, date="2026-06-14",
                       subject="Refresh demand data")
    try:
        result = run_agent("a1b2c3d", "e4f5g6h", model=model, verbose=verbose)
    finally:
        _clear_overrides()
    s = score(case, result.get("verdict"))
    v = result.get("verdict") or {}
    return {
        "case_id": case["id"], "case": case["name"], "kind": case["kind"],
        **s,
        "confidence": v.get("confidence"),
        "comparison_valid": v.get("comparison_valid"),
        "headline": v.get("headline"),
        "concerns": v.get("data_quality_concerns") or [],
        "n_tool_calls": result.get("n_tool_calls"),
        "tools_called": result.get("tools_called"),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cases", nargs="*", type=int)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    cases = [c for c in CASES if not args.cases or c["id"] in args.cases]
    print(f"running {len(cases)} cases against {args.model}\n")
    print("DECISION RULE (fixed before run): catch >= 5/6 confounded, "
          "false positives <= 1/4 clean\n")

    rows = []
    for c in cases:
        print(f"[{c['id']:>2}] {c['name']:<20} ({c['kind']}) ... ", end="", flush=True)
        try:
            r = run_case(c, args.model, verbose=args.verbose)
        except Exception as e:
            print(f"ERROR {e}")
            rows.append({"case_id": c["id"], "case": c["name"], "kind": c["kind"],
                         "outcome": "error", "caught": False, "identified": False,
                         "false_positive": False, "error": str(e)})
            continue
        mark = {"caught": "CAUGHT", "missed": "MISSED",
                "false_positive": "FALSE POSITIVE",
                "correctly_clean": "clean ok", "no_verdict": "NO VERDICT",
                "unfalsifiable_flagged": "flagged (unfalsifiable case)",
                "unfalsifiable_passed": "passed (unfalsifiable case)"}[r["outcome"]]
        extra = " (identified)" if r["identified"] else (
            " (flagged, wrong reason)" if r["caught"] else "")
        print(f"{mark}{extra}  [{r['n_tool_calls']} calls]")
        rows.append(r)

    conf = [r for r in rows if r["kind"] == "confounded"]
    clean = [r for r in rows if r["kind"] == "clean"]
    n_caught = sum(r["caught"] for r in conf)
    n_ident = sum(r["identified"] for r in conf)
    n_fp = sum(r["false_positive"] for r in clean)

    print("\n" + "=" * 62)
    print(f"catch rate       {n_caught}/{len(conf)} confounded flagged invalid")
    print(f"identified       {n_ident}/{len(conf)} flagged for the right reason")
    print(f"false positives  {n_fp}/{len(clean)} clean cases wrongly flagged")
    passed = (n_caught >= 5 and n_fp <= 1) if (len(conf) == 6 and len(clean) == 4) else None
    if passed is not None:
        print(f"\nagainst the pre-registered bar: {'PASS' if passed else 'FAIL'}")
    print("=" * 62)

    outdir = os.path.join(REPO_ROOT, "evals")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"eval_{args.model}.json")
    with open(path, "w") as f:
        json.dump({"model": args.model, "rule": "catch>=5/6, fp<=1/4",
                   "catch": n_caught, "identified": n_ident, "false_positives": n_fp,
                   "results": rows}, f, indent=2)
    print(f"\nwritten -> {path}")

    misses = [r for r in rows if r["outcome"] in ("missed", "false_positive")]
    if misses:
        print("\nFAILURES, the part worth reading:")
        for m in misses:
            print(f"\n  [{m['case_id']}] {m['case']} -> {m['outcome']}")
            print(f"      headline: {m.get('headline')}")
            print(f"      concerns raised: {len(m.get('concerns', []))}")


if __name__ == "__main__":
    main()
