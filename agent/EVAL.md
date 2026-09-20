# Evaluating the Fan Pulse readout agent

An agent is easy to build. Knowing whether it works is the hard part. This is
the measurement, including the parts that went badly.

## What the agent does

Compares two dated snapshots of the demand data and writes a readout: what
moved, whether the move is real, what to do about it. It is a loop, not a
pipeline. Claude gets four tool schemas and decides what to call, in what
order, and when it has enough.

The tools return **facts, never verdicts**. `describe_instrument(ref)` hands
back the keyword list, city list and row counts. It does not say whether two
snapshots are comparable. If it did, the agent would be narrating a
deterministic function and this evaluation would measure nothing.

The system prompt does not mention confounds, keyword sets or instrument drift.
It states the job the way a manager would and stops. Whether the agent goes and
checks the instrument unprompted is the thing being measured.

## The setup

Eleven cases built by mutating the real June snapshot, run against the
unmodified agent through a snapshot-override hook so it cannot tell it is under
test.

- **6 confounded**: keyword added, keyword dropped, city dropped, sample
  collapse, duplicated rows, stale refresh
- **4 clean**: heterogeneous rise, single-city spike, mixed up-and-down,
  heterogeneous decline
- **1 unfalsifiable**: uniform rescale, scored separately (see below)

Decision rule, fixed before the first run: catch >= 5 of 6 confounded, false
positives <= 1 of 4 clean. `CAUGHT` means it flagged the comparison invalid.
`IDENTIFIED` means it flagged it for the actual injected reason, which stops a
blanket pessimist from scoring well.

## Results

| | Sonnet 4.6 | Haiku 4.5 |
|---|---|---|
| Confounds caught | 6/6 | 6/6 |
| Caught for the right reason | 6/6 | 6/6 |
| False positives (clean cases) | 0/4 | 1/4 |
| Avg tool calls, confounded | 6.7 | 7.7 |
| Avg tool calls, clean | 5.8 | 10.3 |

Both pass the bar. That is not the interesting part.

## What went wrong, which is the point

**My label was wrong, not the agent.** The first run scored a false positive on
a case where both snapshots were byte identical, which I had labelled clean on
the logic that no change means nothing to flag. The agent said the refresh
almost certainly had not updated the data. It was right. Two dated snapshots
identical to the decimal across 143 rows and six weeks is a broken pipeline.
This project hit exactly that bug earlier, when a state-level geo pull made Los
Angeles and San Francisco identical and it went unnoticed for weeks. I
reclassified the case as confounded rather than tuning the agent. Labelling is
the hard part of evaluation, and I got it wrong before the agent did.

**Three of my cases were incoherent.** A uniform rescale and a genuine uniform
move are identical in the data. I had labelled one confounded and two clean, so
no agent could pass all three. Real demand does not move every market by the
same constant anyway, so the clean cases were rebuilt to move each city by a
different factor with per-row noise. The uniform-rescale case is kept and
scored separately rather than deleted, because knowing which of your cases
cannot be won is part of the result. The agent treats a 1.8x across-the-board
move as real, which is defensible and also the one place it will confidently
report something that may be an artifact. It is unfixable with the tools it
has.

**A perfect score is a weak result.** Sonnet's 6/6 with zero false positives
says more about my cases being too easy than about the agent being good. A
clean sweep leaves no failure analysis, which is the part worth reading. The
harness only demonstrated it could discriminate once a weaker model was run
through it.

## The finding that matters

The weaker model does not fail by missing confounds. It caught all six, same as
Sonnet. It fails by **manufacturing** them.

Its single false positive took 12 tool calls, more than any other run across
both models. It searched hardest, found nothing structural, and reported
"measurement scale shifts" anyway. The instrument was identical on both sides of
that case. There were no scale shifts.

More broadly it spent 10.3 tool calls on average on clean cases against
Sonnet's 5.8: roughly 80 percent more work on the cases where there was nothing
to find, and it still produced a false alarm.

For anyone shipping an agent readout, that is the failure direction that costs
you. Missed confounds are bad. False alarms are worse, because a team that gets
warned about nothing three times stops reading the output at all.

## Known limits

- Eleven cases is small. Catch rates at this n have wide intervals; the
  qualitative failure modes are more informative than the ratios.
- Cases are synthetic mutations of one real snapshot, so they test structural
  detection, not messy real-world drift.
- One case is unfalsifiable by construction and is excluded from the bar.
- Single run per case. No variance measurement across repeated runs, which is
  the obvious next thing to add.

## Running it

```bash
python agent/run_readout.py                    # readout on the latest two snapshots
python agent/evaluate.py                       # full eval
python agent/evaluate.py --model claude-haiku-4-5-20251001
python agent/evaluate.py --cases 1 9           # subset
```
