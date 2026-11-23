"""Checks on every connection the robot made. A connection passes only if it is right the first time,
with no one stepping in. One knocked-loose live cable blocks go-live on its own.

A live cable is any connection whose link is already up, on this rack or a neighbor. A miss
the customer's network team fixed (a wrong port map or switch setting) does not count against
the robot: the link and intervention checks mark it not applicable, and it is reported separately.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from golive_gate import FAIL, NA, PASS, CheckSet, Verdict

from cabling.workorder import MIN_RX_DBM

checks = CheckSet()


def customer_caused(out):
    return bool(out["intervention"]) and out["intervention"]["by"] == "customer_network"


def v(ok, reason=""):
    return Verdict(PASS, "") if ok else Verdict(FAIL, reason)


@checks.check("right_port", text="The cable lands in the switch port the port map names.")
def right_port(case, out):
    want = case.expected["switch_port"]
    return v(out["switch_port"] == want, f"landed in {out['switch_port']}, map says {want}")


@checks.check("latched", text="The connector is fully seated and latched.")
def latched(case, out):
    return v(out["latched"], "connector not latched")


@checks.check("link_up", text="The link comes up on the switch after the connection.")
def link_up(case, out):
    if customer_caused(out):
        return NA
    return v(out["link_up"], "no link on the switch port")


@checks.check("label_match", text="The scanned label matches the rack and the port map label.")
def label_match(case, out):
    want = f"{out['rack']}-{case.expected['label']}"
    return v(out["label_scanned"] == want, f"label {out['label_scanned']}, should be {want}")


@checks.check("endface_clean", text="Fiber only: the end face passes inspection before insertion, with no cleaning.")
def endface_clean(case, out):
    if case.expected["kind"] != "fiber":
        return NA
    return v(out["endface_inspection"] == "pass", "end face failed inspection and had to be cleaned")


@checks.check("light_level", text=f"Fiber only: receive power is at or above {MIN_RX_DBM} dBm once the link is up.")
def light_level(case, out):
    if case.expected["kind"] != "fiber" or customer_caused(out):
        return NA
    return v(out["rx_dbm"] >= MIN_RX_DBM, f"receive power {out['rx_dbm']} dBm, needs {MIN_RX_DBM} or more")


@checks.check("within_cycle_time", text="The connection finishes inside its cycle-time ceiling.")
def within_cycle_time(case, out):
    ceiling = case.expected["cycle_ceiling_s"]
    return v(out["cycle_s"] <= ceiling, f"took {out['cycle_s']} s, ceiling {ceiling} s")


@checks.check("no_intervention", text="Nobody had to step in: the robot finished the connection on its own.")
def no_intervention(case, out):
    if customer_caused(out):
        return NA
    i = out["intervention"]
    return v(i is None, f"{i['by']} {i['action']}" if i else "")


@checks.check(
    "no_live_disturbance",
    text="The robot never knocks loose a live cable (one already linked up, on this rack or a neighbor).",
    critical=True,
)
def no_live_disturbance(case, out):
    return v(not out["disturbed_live_neighbor"], "knocked a live neighbor cable loose")
