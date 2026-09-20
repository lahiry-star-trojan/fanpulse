"""
tools.py — the agent's tool layer for Fan Pulse.

DESIGN RULE, and it is the whole point of this file:
TOOLS RETURN FACTS, NEVER VERDICTS.

No tool here decides whether two snapshots are comparable, whether a move is
real, or whether something is a confound. They hand back raw structure:
which keywords were measured, which cities, how many rows, what the numbers
are. The agent has to notice that the instrument changed between periods and
reason about whether that invalidates the comparison.

If a tool returned {"comparable": false, "reason": "keyword sets differ"} then
the agent would just be narrating a deterministic function and the evaluation
would be measuring nothing. That distinction is the difference between an agent
that detects a confound and a script that prints one.

Every function is a pure function over (ref -> data). No side effects, no
network. That keeps them wrappable as an MCP server later without a rewrite.
"""

import subprocess
import io
import os
from typing import Any

import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMAND_PATH = "data/raw/trends_geo_raw.csv"

# Snapshots can be overridden by the eval harness so it can point the same
# agent at injected/synthetic data without touching agent code.
_SNAPSHOT_OVERRIDES: dict[str, pd.DataFrame] = {}
_OVERRIDE_META: dict[str, dict[str, str]] = {}


def _register_override(ref: str, df: pd.DataFrame,
                       date: str = "2026-06-01",
                       subject: str = "Refresh demand data") -> None:
    """Used by the eval harness to inject synthetic snapshots under a ref.

    Metadata defaults to an ordinary-looking commit. If this said "synthetic"
    or "injected by eval harness" the agent would know it was under test the
    moment it called list_snapshots, and every result would be worthless.
    """
    _SNAPSHOT_OVERRIDES[ref] = df.copy()
    _OVERRIDE_META[ref] = {"date": date, "subject": subject}


def _clear_overrides() -> None:
    _SNAPSHOT_OVERRIDES.clear()
    _OVERRIDE_META.clear()


def _read_at_ref(ref: str, path: str = DEMAND_PATH) -> pd.DataFrame:
    if ref in _SNAPSHOT_OVERRIDES:
        return _SNAPSHOT_OVERRIDES[ref].copy()
    out = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise ValueError(f"could not read {path} at {ref}: {out.stderr.strip()}")
    return pd.read_csv(io.StringIO(out.stdout))


# ── TOOL 1 ────────────────────────────────────────────────────────────────
def list_snapshots() -> list[dict[str, Any]]:
    """Available dated snapshots of the demand data, newest first.

    Returns commit ref, author date, and subject line. Says nothing about
    whether any two of them can be compared.
    """
    if _SNAPSHOT_OVERRIDES:
        return [{"ref": r,
                 "date": _OVERRIDE_META.get(r, {}).get("date", "2026-06-01"),
                 "subject": _OVERRIDE_META.get(r, {}).get("subject",
                                                          "Refresh demand data")}
                for r in _SNAPSHOT_OVERRIDES]
    out = subprocess.run(
        ["git", "log", "--format=%h|%ad|%s", "--date=short", "--", DEMAND_PATH],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    snaps = []
    for line in out.stdout.strip().splitlines():
        if not line.strip():
            continue
        ref, date, subject = line.split("|", 2)
        snaps.append({"ref": ref, "date": date, "subject": subject})
    return snaps


# ── TOOL 2 ────────────────────────────────────────────────────────────────
def describe_instrument(ref: str) -> dict[str, Any]:
    """Raw structure of what was measured in one snapshot.

    This is the tool that makes confound detection possible without doing it
    for the agent. It reports WHAT was measured: the keyword list, the bucket
    list, the city list, row counts. It does NOT compare anything or flag
    anything. If the agent wants to know whether the instrument changed, it
    has to call this twice and look at the two lists itself.
    """
    df = _read_at_ref(ref)
    per_bucket = (
        df.groupby("bucket")["keyword"].nunique().to_dict()
        if "bucket" in df.columns else {}
    )
    return {
        "ref": ref,
        "n_rows": int(len(df)),
        "columns": list(df.columns),
        "keywords": sorted(df["keyword"].dropna().unique().tolist()),
        "n_keywords": int(df["keyword"].nunique()),
        "buckets": sorted(df["bucket"].dropna().unique().tolist())
                   if "bucket" in df.columns else [],
        "keywords_per_bucket": {k: int(v) for k, v in per_bucket.items()},
        "cities": sorted(df["city"].dropna().unique().tolist()),
        "n_cities": int(df["city"].nunique()),
        "value_min": float(df["value"].min()),
        "value_max": float(df["value"].max()),
        "value_mean": round(float(df["value"].mean()), 2),
    }


# ── TOOL 3 ────────────────────────────────────────────────────────────────
def compute_deltas(ref_a: str, ref_b: str, group_by: str = "city") -> dict[str, Any]:
    """Numeric change from ref_a to ref_b, grouped by city, bucket or keyword.

    Computes the arithmetic faithfully and reports coverage alongside it: how
    many groups exist in both snapshots, how many are only in one. It does not
    warn, caveat, or judge whether the delta is meaningful. A delta computed
    over a changed keyword set will be returned with the same confidence as a
    clean one. Noticing that is the agent's job.
    """
    if group_by not in {"city", "bucket", "keyword"}:
        raise ValueError("group_by must be one of: city, bucket, keyword")
    a, b = _read_at_ref(ref_a), _read_at_ref(ref_b)
    if group_by not in a.columns or group_by not in b.columns:
        raise ValueError(f"{group_by} not present in both snapshots")

    ma = a.groupby(group_by)["value"].mean()
    mb = b.groupby(group_by)["value"].mean()
    both = sorted(set(ma.index) & set(mb.index))

    rows = []
    for g in both:
        va, vb = float(ma[g]), float(mb[g])
        rows.append({
            group_by: g,
            "mean_a": round(va, 1),
            "mean_b": round(vb, 1),
            "abs_change": round(vb - va, 1),
            "pct_change": round(100 * (vb - va) / va, 1) if va else None,
            "n_rows_a": int((a[group_by] == g).sum()),
            "n_rows_b": int((b[group_by] == g).sum()),
        })
    rows.sort(key=lambda r: abs(r["abs_change"]), reverse=True)

    return {
        "ref_a": ref_a, "ref_b": ref_b, "group_by": group_by,
        "overall_mean_a": round(float(a["value"].mean()), 2),
        "overall_mean_b": round(float(b["value"].mean()), 2),
        "overall_pct_change": round(
            100 * (b["value"].mean() - a["value"].mean()) / a["value"].mean(), 1),
        "groups_in_both": len(both),
        "groups_only_in_a": sorted(set(ma.index) - set(mb.index)),
        "groups_only_in_b": sorted(set(mb.index) - set(ma.index)),
        "deltas": rows,
    }


# ── TOOL 4 ────────────────────────────────────────────────────────────────
def get_values(ref: str, keyword: str | None = None,
               city: str | None = None) -> dict[str, Any]:
    """Raw rows from one snapshot, optionally filtered. An escape hatch so the
    agent can check a specific number rather than trusting an aggregate."""
    df = _read_at_ref(ref)
    if keyword:
        df = df[df["keyword"] == keyword]
    if city:
        df = df[df["city"] == city]
    return {
        "ref": ref, "keyword": keyword, "city": city,
        "n_rows": int(len(df)),
        "rows": df.head(60).to_dict(orient="records"),
    }


# ── SCHEMAS (Anthropic tool-use format; also the MCP shape later) ─────────
TOOL_SCHEMAS = [
    {
        "name": "list_snapshots",
        "description": ("List available dated snapshots of the demand dataset, "
                        "newest first, with commit ref and date. Does not say "
                        "whether any two are comparable."),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "describe_instrument",
        "description": ("Report what was measured in one snapshot: the exact "
                        "keyword list, bucket list, city list, row counts and "
                        "value range. Returns structure only, no comparison and "
                        "no judgement."),
        "input_schema": {
            "type": "object",
            "properties": {"ref": {"type": "string",
                                   "description": "snapshot ref from list_snapshots"}},
            "required": ["ref"],
        },
    },
    {
        "name": "compute_deltas",
        "description": ("Mean value change from ref_a to ref_b grouped by city, "
                        "bucket or keyword, with per-group row counts and which "
                        "groups appear in only one snapshot. Computes the "
                        "arithmetic as asked; does not validate the comparison."),
        "input_schema": {
            "type": "object",
            "properties": {
                "ref_a": {"type": "string", "description": "earlier snapshot ref"},
                "ref_b": {"type": "string", "description": "later snapshot ref"},
                "group_by": {"type": "string", "enum": ["city", "bucket", "keyword"],
                             "description": "grouping dimension, default city"},
            },
            "required": ["ref_a", "ref_b"],
        },
    },
    {
        "name": "get_values",
        "description": ("Raw rows from one snapshot, optionally filtered by "
                        "keyword and/or city. Use to check a specific number."),
        "input_schema": {
            "type": "object",
            "properties": {
                "ref": {"type": "string"},
                "keyword": {"type": "string"},
                "city": {"type": "string"},
            },
            "required": ["ref"],
        },
    },
]

DISPATCH = {
    "list_snapshots": list_snapshots,
    "describe_instrument": describe_instrument,
    "compute_deltas": compute_deltas,
    "get_values": get_values,
}


if __name__ == "__main__":
    import json
    snaps = list_snapshots()
    print("snapshots:", json.dumps(snaps, indent=2))
    if len(snaps) >= 2:
        b, a = snaps[0]["ref"], snaps[1]["ref"]
        print(f"\ndescribe_instrument({a}):")
        print(json.dumps(describe_instrument(a), indent=2)[:700])
        print(f"\ncompute_deltas({a}, {b}, bucket):")
        print(json.dumps(compute_deltas(a, b, "bucket"), indent=2)[:700])
