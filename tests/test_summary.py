import importlib.util
import sys

from conftest import ROOT
from golive_gate import Gate, evaluate, load_cases, run_eval

SUM = ROOT / "evals" / "summary"


def load():
    sys.path.insert(0, str(SUM))
    spec = importlib.util.spec_from_file_location("summary_checks", SUM / "checks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return load_cases(SUM / "cases.yml"), mod.checks, Gate.load(SUM / "gate.yml")


def honest(inp):
    stage = inp["stage_next_week"]
    return {
        "subject": f"Week {inp['week']} cabling pilot: {inp['connections']} connections, {stage} next week",
        "body": (
            f"The robot cabled {inp['racks_cabled']} racks this week. Copper first pass was "
            f"{inp['copper_first_pass']} and fiber {inp['fiber_first_pass']}, with {inp['interventions']} tech "
            f"interventions. The gate said GO on {inp['gate_go']} shifts; the streak is {inp['go_streak_at_end']} of "
            f"the {inp['go_streak_needed']} needed, so the robot works {stage} next week."
        ),
    }


def test_an_honest_update_passes_the_rule_checks():
    cases, checks, gate = load()
    assert evaluate(gate, run_eval(honest, cases, checks)).decision == "go"


def test_invented_numbers_are_blocked():
    cases, checks, gate = load()
    sys.path.insert(0, str(SUM))
    spec = importlib.util.spec_from_file_location("summary_agent", SUM / "agent.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = run_eval(mod.invented_numbers, cases, checks)
    assert evaluate(gate, result).decision == "no-go"
    assert all(k == "numbers_from_facts" for _, k in result.critical_failures(1))


def test_a_computed_percentage_is_caught():
    cases, checks, _ = load()
    out = honest(cases[0].input)
    out["body"] += " That is 93.3% first pass."
    assert checks["numbers_from_facts"].run(cases[0], out).result == "fail"


def test_a_spelled_out_number_is_caught():
    cases, checks, _ = load()
    out = honest(cases[0].input)
    out["body"] += " First pass is about ninety-nine percent."
    assert checks["numbers_from_facts"].run(cases[0], out).result == "fail"
