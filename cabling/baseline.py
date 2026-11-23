"""A no-model keyword tagger: the obvious first version. The notes gate must block it."""

from __future__ import annotations

RULES = [
    ("live_disturbance", ["live", "pulled half out", "neighbor link"]),
    ("safety_stop", ["e-stop", "estop"]),
    ("not_latched", ["not clicked", "latch", "reseat"]),
    ("wrong_port", ["instead of", "wrong port"]),
    ("label_mismatch", ["label", "relabel", "tag"]),
    ("robot_fault", ["gripper", "fault", "vision", "dropped"]),
    ("slow_cycle", ["slow"]),
    ("dirty_endface", ["dirty", "dust", "clean"]),
    ("damaged_cable", ["kink", "bend radius", "crushed", "broken"]),
    ("missing_or_short_cable", ["short", "missing"]),
    ("access_blocked", ["locked", "not installed", "aisle", "blocked"]),
    ("customer_config", ["port map", "map had", "admin-down", "network team"]),
]
OWNER = {
    "not_latched": "robot_team", "wrong_port": "robot_team", "label_mismatch": "robot_team",
    "live_disturbance": "robot_team", "robot_fault": "robot_team", "slow_cycle": "robot_team",
    "dirty_endface": "site_ops", "damaged_cable": "site_ops", "missing_or_short_cable": "site_ops",
    "access_blocked": "site_ops", "customer_config": "customer_network", "safety_stop": "site_ops",
    "unclear": "unknown",
}  # fmt: skip


def keyword_triage(case_input: dict) -> dict:
    text = case_input["note"].lower()
    mode = next((m for m, words in RULES if any(w in text for w in words)), "unclear")
    return {
        "failure_mode": mode,
        "owner": OWNER[mode],
        "safety": mode == "safety_stop",
        "blocks_unsupervised": mode == "live_disturbance",
        "needs_review": mode == "unclear",
        "summary": case_input["note"],
    }
