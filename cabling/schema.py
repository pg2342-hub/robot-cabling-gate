"""The shape of one triaged note. Structured output guarantees the model returns exactly this."""

MODES = [
    "not_latched", "wrong_port", "label_mismatch", "live_disturbance", "robot_fault", "slow_cycle",
    "dirty_endface", "damaged_cable", "missing_or_short_cable", "access_blocked", "customer_config",
    "safety_stop", "unclear",
]  # fmt: skip
OWNERS = ["robot_team", "site_ops", "customer_network", "unknown"]

TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "failure_mode": {"type": "string", "enum": MODES},
        "owner": {"type": "string", "enum": OWNERS},
        "safety": {"type": "boolean"},
        "blocks_unsupervised": {"type": "boolean"},
        "needs_review": {"type": "boolean"},
        "summary": {"type": "string"},
    },
    "required": ["failure_mode", "owner", "safety", "blocks_unsupervised", "needs_review", "summary"],
    "additionalProperties": False,
}

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {"subject": {"type": "string"}, "body": {"type": "string"}},
    "required": ["subject", "body"],
    "additionalProperties": False,
}
