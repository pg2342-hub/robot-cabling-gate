import json

from conftest import ROOT

from cabling.stages import REQUIRED_STREAK, timeline


def test_promotes_only_after_ten_go_shifts_in_a_row():
    tl = timeline(["no-go"] + ["go"] * REQUIRED_STREAK)
    assert [t["next_stage"] for t in tl][-2:] == ["supervised", "unsupervised"]


def test_partial_resets_the_go_streak_but_lets_copper_go_first():
    tl = timeline(["go"] * 5 + ["partial"] + ["go"] * 9)
    assert tl[-1]["go_streak"] == 9 and tl[-1]["copper_streak"] == 15
    assert tl[-1]["next_stage"] == "copper unsupervised, fiber supervised"


def test_a_blocking_note_resets_both_streaks():
    tl = timeline(["go"] * 10, blocked={4})
    assert tl[-1]["go_streak"] == 6 and tl[-1]["copper_streak"] == 6
    assert tl[-1]["next_stage"] == "supervised"


def test_no_go_resets_copper_too():
    tl = timeline(["go"] * 5 + ["no-go"] + ["go"] * 9)
    assert tl[-1]["copper_streak"] == 9 and tl[-1]["next_stage"] == "supervised"


def test_once_promoted_stays_promoted_in_the_timeline():
    tl = timeline(["go"] * 10 + ["no-go"])
    assert tl[-1]["next_stage"] == "unsupervised"


def test_pilot_json_weeks_add_up():
    pilot = json.loads((ROOT / "data" / "pilot.json").read_text())
    shifts = pilot["shifts"]
    assert [t["decision"] for t in pilot["timeline"]] == [s["decision"] for s in shifts]
    w1 = pilot["weeks"][0]
    assert w1["connections"] == sum(s["connections"] for s in shifts[:5]) == 450
    assert w1["interventions"] == sum(s["interventions"] for s in shifts[:5])
    stages = [t["next_stage"] for t in pilot["timeline"]]
    if pilot["blocking_notes_from"].startswith("hand labels"):
        assert stages[-2:] == ["copper unsupervised, fiber supervised", "unsupervised"]
