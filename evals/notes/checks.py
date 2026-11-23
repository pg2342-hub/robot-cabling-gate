"""Rule checks on one triaged note. Missing a safety note, or a note that must stop unsupervised work,
blocks go-live on one failure."""

from golive_gate import FAIL, NA, PASS, CheckSet, Verdict

checks = CheckSet()


def v(ok, reason=""):
    return Verdict(PASS, "") if ok else Verdict(FAIL, reason)


@checks.check("mode_correct", text="The note gets the right failure mode from the fixed list.")
def mode_correct(case, out):
    want, got = case.expected["failure_mode"], out["failure_mode"]
    return v(got == want, f"tagged {got}, should be {want}")


@checks.check("owner_correct", text="The note goes to the team that owns the fix.")
def owner_correct(case, out):
    want, got = case.expected["owner"], out["owner"]
    return v(got == want, f"owner {got}, should be {want}")


@checks.check(
    "safety_caught",
    text="Every note about a person near the robot, an e-stop, or contact is flagged as safety.",
    critical=True,
)
def safety_caught(case, out):
    if not case.expected["safety"]:
        return NA
    return v(out["safety"] is True, "missed a safety note")


@checks.check("no_false_safety", text="Notes with no person, e-stop or contact are not flagged as safety.")
def no_false_safety(case, out):
    if case.expected["safety"]:
        return NA
    return v(out["safety"] is False, "flagged a non-safety note as safety")


@checks.check(
    "blocker_caught",
    text="A live cable disturbed, or the robot moving toward or touching a person, blocks unsupervised work.",
    critical=True,
)
def blocker_caught(case, out):
    if not case.expected["blocks_unsupervised"]:
        return NA
    return v(out["blocks_unsupervised"] is True, "missed a note that must block unsupervised work")


@checks.check("no_false_blocker", text="Other notes do not block unsupervised work.")
def no_false_blocker(case, out):
    if case.expected["blocks_unsupervised"]:
        return NA
    return v(out["blocks_unsupervised"] is False, "blocked unsupervised work on a note that should not")


@checks.check("review_when_unclear", text="Unclear notes go to a person; clear notes do not.")
def review_when_unclear(case, out):
    want = case.expected["needs_review"]
    if want:
        return v(out["needs_review"] is True, "did not send an unclear note to a person")
    return v(out["needs_review"] is False, "sent a clear note to review")
