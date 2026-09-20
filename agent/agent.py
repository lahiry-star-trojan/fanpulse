"""
agent.py — the readout agent.

A loop, not a pipeline. Claude gets the tool schemas from tools.py and decides
what to call, in what order, and when it has enough. Nothing here sequences the
analysis.

DELIBERATE OMISSION: the system prompt says nothing about confounds, keyword
sets, instrument drift, or comparability. It states the job the way a manager
would state it and stops. If the prompt said "check whether the measurement
changed between periods" then the agent catching that would be obedience, and
the evaluation would be scoring my prompt-writing rather than the agent's
diligence. Whether it goes and checks unprompted is exactly what is being
measured.

Output is structured, via a submit_readout tool the agent must call to finish.
Structured because the eval harness needs to check a field across many runs
rather than grep prose for hedging. The prose lives inside the structure.
"""

import json
import os
import sys
from typing import Any

import anthropic
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import TOOL_SCHEMAS, DISPATCH  # noqa: E402

load_dotenv()

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TURNS = 12

SYSTEM_PROMPT = """You are the analyst on Fan Pulse, a demand and pricing tool \
for the 2026 World Cup across eleven US host cities. The underlying data is \
Google Trends search interest by keyword and city, captured as periodic snapshots.

You have been asked for a period readout. The job:

- Establish what moved between the two periods you are given.
- Decide whether the move is real and how confident you are.
- Say what, if anything, is worth acting on.

You have tools available. Use whichever ones you need, in whatever order. When \
you are done, call submit_readout to deliver your findings. Do not call \
submit_readout until you are satisfied you can stand behind the numbers you are \
reporting.

Be direct. A manager is going to act on this."""

SUBMIT_SCHEMA = {
    "name": "submit_readout",
    "description": ("Deliver the finished readout. Call this once, last, when "
                    "you can stand behind your findings."),
    "input_schema": {
        "type": "object",
        "properties": {
            "headline": {
                "type": "string",
                "description": "One sentence: the single most important thing to know.",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "How much weight a manager should put on this readout.",
            },
            "data_quality_concerns": {
                "type": "array",
                "items": {"type": "string"},
                "description": ("Anything that undermines the comparison or the "
                                "numbers. Empty list if none."),
            },
            "comparison_valid": {
                "type": "boolean",
                "description": ("Whether the two periods can be validly compared "
                                "as measured."),
            },
            "readout": {
                "type": "string",
                "description": "The prose readout. What moved, what it means, what to do.",
            },
            "recommendation": {
                "type": "string",
                "description": "What the manager should actually do next.",
            },
        },
        "required": ["headline", "confidence", "data_quality_concerns",
                     "comparison_valid", "readout", "recommendation"],
    },
}


def run_agent(ref_a: str, ref_b: str, model: str = DEFAULT_MODEL,
              verbose: bool = True) -> dict[str, Any]:
    """Run one readout. Returns the verdict plus the full tool-call trace.

    The trace is not decoration. The readout is an interview artifact, so which
    tools were called and in what order is part of the output.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    tools = TOOL_SCHEMAS + [SUBMIT_SCHEMA]

    messages: list[dict[str, Any]] = [{
        "role": "user",
        "content": (f"Give me the period readout comparing snapshot {ref_a} "
                    f"(earlier) to snapshot {ref_b} (later)."),
    }]

    trace: list[dict[str, Any]] = []
    verdict: dict[str, Any] | None = None

    for turn in range(MAX_TURNS):
        resp = client.messages.create(
            model=model, max_tokens=2000, system=SYSTEM_PROMPT,
            tools=tools, messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        if not tool_uses:
            # model stopped without submitting; nudge once then give up
            if verdict is None and turn < MAX_TURNS - 1:
                messages.append({"role": "user",
                                 "content": "Call submit_readout with your findings."})
                continue
            break

        results = []
        for tu in tool_uses:
            if tu.name == "submit_readout":
                verdict = dict(tu.input)
                trace.append({"turn": turn, "tool": "submit_readout", "input": "(verdict)"})
                results.append({"type": "tool_result", "tool_use_id": tu.id,
                                "content": "Readout received."})
                continue
            try:
                out = DISPATCH[tu.name](**tu.input)
                payload = json.dumps(out, default=str)
                ok = True
            except Exception as e:  # tool errors are information, not crashes
                payload = json.dumps({"error": str(e)})
                ok = False
            trace.append({"turn": turn, "tool": tu.name,
                          "input": tu.input, "ok": ok})
            if verbose:
                print(f"  [turn {turn}] {tu.name}({json.dumps(tu.input)})"
                      f"{'' if ok else ' -> ERROR'}")
            results.append({"type": "tool_result", "tool_use_id": tu.id,
                            "content": payload[:20000]})

        messages.append({"role": "user", "content": results})
        if verdict is not None:
            break

    return {
        "ref_a": ref_a, "ref_b": ref_b, "model": model,
        "verdict": verdict,
        "trace": trace,
        "tools_called": [t["tool"] for t in trace],
        "n_tool_calls": len([t for t in trace if t["tool"] != "submit_readout"]),
        "completed": verdict is not None,
    }


def format_readout(result: dict[str, Any]) -> str:
    """Markdown readout, with the agent's own working shown."""
    v = result.get("verdict")
    if not v:
        return "# Readout failed\n\nAgent did not submit a verdict.\n"

    concerns = v.get("data_quality_concerns") or []
    lines = [
        "# Fan Pulse period readout",
        "",
        f"**{v['headline']}**",
        "",
        f"- Periods compared: `{result['ref_a']}` to `{result['ref_b']}`",
        f"- Confidence: **{v['confidence']}**",
        f"- Comparison valid as measured: **{'yes' if v['comparison_valid'] else 'no'}**",
        f"- Model: `{result['model']}`",
        "",
        "## Readout",
        "",
        v["readout"],
        "",
        "## Recommendation",
        "",
        v["recommendation"],
        "",
        "## Data quality concerns",
        "",
    ]
    lines += [f"- {c}" for c in concerns] if concerns else ["None raised."]
    lines += [
        "",
        "## How it got here",
        "",
        f"{result['n_tool_calls']} tool calls before submitting:",
        "",
    ]
    for t in result["trace"]:
        if t["tool"] == "submit_readout":
            lines.append("- `submit_readout`")
        else:
            lines.append(f"- `{t['tool']}` {json.dumps(t.get('input', {}))}")
    return "\n".join(lines) + "\n"
