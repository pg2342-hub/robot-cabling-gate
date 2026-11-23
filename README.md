# robot-cabling-gate

[![CI](https://github.com/pg2342-hub/robot-cabling-gate/actions/workflows/ci.yml/badge.svg)](https://github.com/pg2342-hub/robot-cabling-gate/actions/workflows/ci.yml)

Demo page: https://pg2342-hub.github.io/robot-cabling-gate/ (stage timeline and every graded connection, plus Claude's note triage and weekly updates from the recorded live run; no install needed)

A go-live gate for a supervised robot cabling pilot in an AI data center. A robot cables one rack per shift while a tech watches. This repo answers the question the customer and the deployment team both ask every week: **can the robot work without a tech watching yet?**

Built on [golive-gate](https://github.com/pg2342-hub/golive-gate).

## The three parts

| Part | What it does | Where |
|---|---|---|
| Shift gate | Grades every connection the robot made on a shift: right port, latched, link up, label, clean fiber end face, fiber receive power, cycle time, nobody stepping in, and no live cable knocked loose (a live cable is any connection already linked up, on this rack or a neighbor). **GO** needs 53 of 54 copper and 35 of 36 fiber connections right the first time, with no live cable disturbed. A fiber miss alone is **PARTIAL**. A miss the customer's network team fixed (wrong port map or switch setting) is reported separately and not counted against the robot. | `evals/shift/` |
| Note triage (Claude) | Every time a tech steps in, they write a short note. Claude tags it with a failure mode from a fixed list, the team that owns the fix, whether it is a safety note, whether it must block unsupervised work, and whether a person should read it, plus a one-line summary. Rules grade the tags; a Claude judge grades whether the summary sticks to the note. Missing a safety note or a blocker is critical. | `evals/notes/`, `cabling/triage_guide.md` |
| Weekly update (Claude) | Claude writes the customer's weekly update from that week's fact sheet. A rule check blocks any number that is not in the sheet; a Claude judge blocks any unsupported claim. | `evals/summary/` |

**Stage rule.** The robot stays supervised until the shift gate says GO on **10 shifts in a row** (two working weeks) with no tech note that blocks unsupervised work on those shifts. A PARTIAL, a NO-GO or a blocking note resets the count. Copper can go first: a PARTIAL is a fiber-only miss, so it keeps a separate copper streak going, and copper goes unsupervised once that streak reaches 10 (`cabling/stages.py`).

## The data

Everything is simulated or constructed. The simulation covers the supervised weeks of a pilot: 15 shifts, one rack each. Each rack has 54 copper management connections over two management switches and 36 front-end fiber connections (two DPU ports per tray), following NVIDIA's GB300 NVL72 reference design ("54 x 1Gb/s for management" per rack). Port names, labels, light levels, cycle-time ceilings and every miss are made up and planted by hand in `cabling/simulate.py`, so the gate's decisions are easy to follow: shifts 1 to 4 are NO-GO, shift 5 is PARTIAL, and shifts 6 to 15 are GO, so at the readout copper could go unsupervised ahead of fiber, and after shift 15 the full GO streak reaches 10. The 30 tech notes in `evals/notes/cases.yml` are written to read like real field notes, each with its correct tags; every note that names a connection matches that connection in the shift log (a test checks this).

## Baselines the gates must block

- A keyword tagger for the notes (`cabling/baseline.py`): it misses safety notes that never say "e-stop" ("pinched my glove", "walked into the aisle"), so the notes gate says NO-GO.
- A weekly update writer that rounds and projects ("about 99%", "save roughly 40% of tech hours"): the update gate says NO-GO.

## Run it

```
pip install -e ".[dev]"
pytest -q                                          # no network
python scripts/run_shifts.py                       # grade all 15 shifts and print the stage timeline
golive run evals/shift/golive.yml --agent agent:shift_01    # one shift: NO-GO, a live cable knocked loose
golive run evals/notes/golive.baseline.yml         # keyword tagger: NO-GO
golive run evals/notes/golive.yml                  # replays the recorded Claude run: no key needed
GOLIVE_LIVE=1 ANTHROPIC_API_KEY=... golive run evals/notes/golive.live.yml   # a fresh live run
python scripts/build_demo.py                       # rebuild docs/
```

## How the live run is recorded

Triage, the weekly update and the judge call Claude (`claude-opus-5-5`, low effort, structured output for triage and the update). A live run writes every reply to `recordings/` with cost and latency per call. CI and the demo page replay that recording, so they need no API key and give the same result every time. The **Record a live run** workflow (Actions tab, needs the `ANTHROPIC_API_KEY` secret) refreshes the recording, rebuilds the demo page and publishes it.

## CI

Every push runs ruff, the tests, a check that the committed shift logs and fact sheets match the code, the shift gate through the golive-gate GitHub Action, the two baselines (which must come out NO-GO), and the recorded Claude runs.
