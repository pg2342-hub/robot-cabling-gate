"""From shift gate decisions to the pilot's stage: when the robot may work without a tech watching.

Rule (the pilot plan's): the robot works supervised until the shift gate says GO on
REQUIRED_STREAK shifts in a row (two working weeks). A PARTIAL or NO-GO resets the streak, and so
does any tech note on that shift that the triage step marks as blocking unsupervised work
(a disturbed live cable, or the robot moving toward or touching a person).

Copper can go first: a PARTIAL shift (fiber missed its bar, copper did not) keeps the copper
streak going, so copper may reach REQUIRED_STREAK and go unsupervised while fiber stays supervised.
"""

from __future__ import annotations

from statistics import mean

from .workorder import CYCLE_CEILING_S, MIN_RX_DBM, template

_SLOTS = {s["slot"]: s for s in template()}

REQUIRED_STREAK = 10
WEEK = 5  # shifts per working week


def metrics(log: list[dict], decision: str) -> dict:
    """Plain numbers for one shift, straight from the robot log."""
    out = {"shift": log[0]["shift"], "rack": log[0]["rack"], "decision": decision, "connections": len(log)}
    for kind in ("copper", "fiber"):
        rows = [r for r in log if r["kind"] == kind]
        clean = [r for r in rows if _first_pass(r)]
        out[f"{kind}_total"] = len(rows)
        out[f"{kind}_first_pass"] = len(clean)
        out[f"{kind}_mean_cycle_s"] = round(mean(r["cycle_s"] for r in rows), 1)
    out["interventions"] = sum(r["intervention"] is not None and not _customer(r) for r in log)
    out["customer_caused"] = sum(_customer(r) for r in log)
    out["live_disturbances"] = sum(r["disturbed_live_neighbor"] for r in log)
    out["safety_stops"] = sum(r["safety_stop"] for r in log)
    return out


def _customer(r: dict) -> bool:
    return bool(r["intervention"]) and r["intervention"]["by"] == "customer_network"


def _first_pass(r: dict) -> bool:
    """Same bar as the shift gate's checks, computed from the log alone. Customer-caused misses don't count."""
    if _customer(r):
        return True
    return (
        r["intervention"] is None
        and r["latched"]
        and r["link_up"]
        and (r["rx_dbm"] is None or r["rx_dbm"] >= MIN_RX_DBM)
        and r["endface_inspection"] in (None, "pass")
        and not r["disturbed_live_neighbor"]
        and r["cycle_s"] <= CYCLE_CEILING_S[r["kind"]]
        and r["label_scanned"] == f"{r['rack']}-{_SLOTS[r['slot']]['label']}"
        and r["switch_port"] == _SLOTS[r["slot"]]["switch_port"]
    )


def timeline(
    decisions: list[str],
    blocked: set[int] = frozenset(),
    copper_ok: list[bool] | None = None,
    required: int = REQUIRED_STREAK,
) -> list[dict]:
    """For each shift in order: decision, blocking note, GO and copper streaks after it, and the next stage.

    copper_ok[i] says the copper rule held with no critical failure on that shift; by default it
    is true exactly when the shift was GO or PARTIAL (a PARTIAL is a fiber-only miss).
    """
    if copper_ok is None:
        copper_ok = [d in ("go", "partial") for d in decisions]
    rows, streak, cu_streak, full_after, cu_after = [], 0, 0, None, None
    for i, d in enumerate(decisions, start=1):
        ok = i not in blocked
        streak = streak + 1 if d == "go" and ok else 0
        cu_streak = cu_streak + 1 if copper_ok[i - 1] and ok else 0
        if full_after is None and streak >= required:
            full_after = i
        if cu_after is None and cu_streak >= required:
            cu_after = i
        if full_after is not None:
            nxt = "unsupervised"
        elif cu_after is not None:
            nxt = "copper unsupervised, fiber supervised"
        else:
            nxt = "supervised"
        rows.append(
            {
                "shift": i,
                "decision": d,
                "blocking_note": i in blocked,
                "go_streak": streak,
                "copper_streak": cu_streak,
                "next_stage": nxt,
            }
        )
    return rows


def weekly_facts(shift_metrics: list[dict], tl: list[dict]) -> list[dict]:
    """One fact sheet per working week: what the customer's exec summary may say, and nothing more."""
    weeks = []
    for w in range(0, len(shift_metrics), WEEK):
        ms, ts = shift_metrics[w : w + WEEK], tl[w : w + WEEK]
        n = w // WEEK + 1
        copper = sum(m["copper_first_pass"] for m in ms), sum(m["copper_total"] for m in ms)
        fiber = sum(m["fiber_first_pass"] for m in ms), sum(m["fiber_total"] for m in ms)
        conns = sum(m["connections"] for m in ms)
        weeks.append(
            {
                "week": n,
                "shifts": f"{ms[0]['shift']}-{ms[-1]['shift']}",
                "racks_cabled": len(ms),
                "connections": conns,
                "copper_first_pass": f"{copper[0]} of {copper[1]}",
                "fiber_first_pass": f"{fiber[0]} of {fiber[1]}",
                "first_pass_pct": round(100 * (copper[0] + fiber[0]) / conns, 1),
                "interventions": sum(m["interventions"] for m in ms),
                "customer_caused_misses": sum(m["customer_caused"] for m in ms),
                "interventions_per_100": round(100 * sum(m["interventions"] for m in ms) / conns, 1),
                "live_disturbances": sum(m["live_disturbances"] for m in ms),
                "safety_stops": sum(m["safety_stops"] for m in ms),
                "gate_go": sum(t["decision"] == "go" for t in ts),
                "gate_partial": sum(t["decision"] == "partial" for t in ts),
                "gate_no_go": sum(t["decision"] == "no-go" for t in ts),
                "shifts_with_blocking_note": sum(t["blocking_note"] for t in ts),
                "go_streak_at_end": ts[-1]["go_streak"],
                "go_streak_needed": REQUIRED_STREAK,
                "stage_next_week": ts[-1]["next_stage"],
            }
        )
    return weeks
