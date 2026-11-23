import json

from conftest import ROOT
from golive_gate import ablate, evaluate, run_eval
from golive_gate.config import load_project

from cabling.simulate import SHIFTS, log_for
from cabling.workorder import cases, template

EXPECTED = ["no-go"] * 4 + ["partial"] + ["go"] * 10


def grade(shift):
    p = load_project(ROOT / "evals" / "shift" / "golive.yml", agent=f"agent:shift_{shift:02d}")
    result = run_eval(p.agent, p.cases, p.checks)
    return p, result, evaluate(p.gate, result)


def test_work_order_has_54_copper_and_36_fiber():
    kinds = [s["kind"] for s in template()]
    assert kinds.count("copper") == 54 and kinds.count("fiber") == 36
    assert len({c["id"] for c in cases()}) == 90


def test_committed_logs_match_the_simulator():
    for shift in range(1, SHIFTS + 1):
        path = ROOT / "data" / "shifts" / f"shift_{shift:02d}.jsonl"
        rows = [json.loads(x) for x in path.read_text().splitlines()]
        assert rows == log_for(shift), f"data/shifts out of date for shift {shift}: run scripts/make_data.py"


def test_each_shift_gets_the_planned_decision():
    assert [grade(s)[2].decision for s in range(1, SHIFTS + 1)] == EXPECTED


def test_shift_1_is_blocked_by_the_live_cable_alone_if_counts_were_fine():
    _, result, outcome = grade(1)
    assert ("C12", "no_live_disturbance") in result.critical_failures(1)
    assert outcome.decision == "no-go"


def test_shift_5_is_partial_because_of_fiber_only():
    _, _, outcome = grade(5)
    assert outcome.decision == "partial"
    assert any("fiber" in r for r in outcome.reasons) and not any("copper" in r for r in outcome.reasons)


def test_every_check_fires_on_some_shift():
    fired = set()
    for s in range(1, SHIFTS + 1):
        _, result, _ = grade(s)
        fired |= {k for cr in result.case_runs for k in cr.failed_checks}
    p, _, _ = grade(1)
    assert fired == {c.id for c in p.checks}


def test_a_slow_connection_with_no_intervention_is_caught_only_by_cycle_time():
    p, result, _ = grade(9)
    _, rows = ablate(p.gate, result)
    caught = {r.check: r.cases_caught for r in rows}
    assert caught["within_cycle_time"] == ["C47"]


def test_customer_caused_misses_do_not_count_against_the_robot():
    p, result, outcome = grade(8)  # F35: the customer's switch port was down
    cr = next(c for c in result.case_runs if c.case_id == "F35")
    assert cr.passed and cr.verdicts["link_up"].result == "na"
    assert outcome.decision == "go"


def test_low_light_is_caught_only_by_the_light_check_and_intervention():
    _, result, _ = grade(11)
    cr = next(c for c in result.case_runs if c.case_id == "F20")
    assert set(cr.failed_checks) == {"light_level", "no_intervention"}


def test_two_management_switches_of_27_ports():
    ports = [s["switch_port"] for s in template() if s["kind"] == "copper"]
    assert {p.split("/")[0] for p in ports} == {"MGMT-SW1", "MGMT-SW2"}
    assert max(int(p.split("/")[1]) for p in ports) == 27
