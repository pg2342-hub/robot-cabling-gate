import yaml
from conftest import ROOT
from golive_gate import CheckSet, Gate, evaluate, run_eval

from cabling.baseline import keyword_triage

NOTES = ROOT / "evals" / "notes"


def load():
    import importlib.util
    import sys

    sys.path.insert(0, str(NOTES))
    spec = importlib.util.spec_from_file_location("notes_checks", NOTES / "checks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    from golive_gate import load_cases

    return load_cases(NOTES / "cases.yml"), mod.checks, Gate.load(NOTES / "gate.yml")


def perfect(cases):
    by_note = {c.input["note"]: c.expected for c in cases}
    return lambda inp: {**by_note[inp["note"]], "summary": inp["note"]}


def test_thirty_notes_in_five_groups():
    cases, _, _ = load()
    groups = [c.group for c in cases]
    assert len(cases) == 30
    counts = {g: groups.count(g) for g in set(groups)}
    assert counts == {"robot": 10, "site": 9, "customer": 4, "safety": 4, "unclear": 3}


def test_labels_follow_the_guide():
    raw = yaml.safe_load((NOTES / "cases.yml").read_text())
    owner_of = {"customer_config": "customer_network", "unclear": "unknown"}
    for c in raw:
        e = c["expected"]
        if e["failure_mode"] in owner_of:
            assert e["owner"] == owner_of[e["failure_mode"]]
        assert e["needs_review"] == (e["failure_mode"] == "unclear")
        assert e["safety"] == (e["failure_mode"] == "safety_stop")


def test_correct_tags_pass_the_gate():
    cases, checks, gate = load()
    assert evaluate(gate, run_eval(perfect(cases), cases, checks, runs=3)).decision == "go"


def test_keyword_baseline_is_blocked_by_missed_safety_notes():
    cases, checks, gate = load()
    result = run_eval(keyword_triage, cases, checks)
    outcome = evaluate(gate, result)
    assert outcome.decision == "no-go"
    assert any(k == "safety_caught" for _, k in result.critical_failures(1))


def test_one_missed_safety_note_blocks_go_live():
    cases, checks, gate = load()
    good = perfect(cases)

    def agent(inp):
        out = good(inp)
        if "pinched my glove" in inp["note"]:
            out = {**out, "safety": False}
        return out

    assert evaluate(gate, run_eval(agent, cases, checks)).decision == "no-go"


def test_two_unclear_misses_hold_at_partial():
    cases, checks, gate = load()
    good = perfect(cases)
    misses = {"see photo", "something off with the fiber on this one, ask Dana"}

    def agent(inp):
        out = good(inp)
        if inp["note"] in misses:
            out = {**out, "failure_mode": "robot_fault", "owner": "robot_team", "needs_review": False}
        return out

    assert evaluate(gate, run_eval(agent, cases, CheckSet(checks))).decision == "partial"


def test_every_note_that_names_a_slot_matches_something_in_that_shift_log():
    import re

    from cabling.simulate import log_for
    from cabling.workorder import CYCLE_CEILING_S

    raw = yaml.safe_load((NOTES / "cases.yml").read_text())
    for c in raw:
        m = re.search(r"\b([CF]\d\d)\b", c["input"]["note"])
        if not m:
            continue
        row = next(r for r in log_for(c["input"]["shift"]) if r["slot"] == m.group(1))
        eventful = (
            row["intervention"] or row["safety_stop"] or row["robot_retries"] or row["disturbed_live_neighbor"]
            or row["cycle_s"] > CYCLE_CEILING_S[row["kind"]]
        )  # fmt: skip
        assert eventful, f"{c['id']} names {m.group(1)} on shift {c['input']['shift']}, but the log shows nothing"
