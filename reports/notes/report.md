# Intervention note triage gate: NO-GO

Agent `agent:live_triage`, 30 cases, 3 run(s).

- run 1: clear notes passed 24 of 27, needs 25 (no-go)

## Pass counts by run

| Run | Passed | Critical failures |
|---|---|---|
| 1 | 26 of 30 | 0 |
| 2 | 27 of 30 | 0 |
| 3 | 29 of 30 | 0 |

Agent cost 0.7380 USD, judge cost 0.4168 USD, mean latency 1814.5 ms per case.

## Cases

| Case | Group | Result | Failed checks |
|---|---|---|---|
| C05 not clicked in, reseated by hand, link came up | robot | 3 of 3 runs |  |
| C31 same thing, latch not engaged. 2nd one today | robot | 3 of 3 runs |  |
| F22 landed in FE-LEAF2/5 instead of /4, moved it over | robot | 3 of 3 runs |  |
| Gripper fault on C27, arm retried 3x then gave up, I finishe | robot | 3 of 3 runs |  |
| C19 gripper dropped the RJ45 under the tray, fished it out a | robot | 3 of 3 runs |  |
| tag on C40 reads M2, map says M1. printed a new one | robot | 3 of 3 runs |  |
| While routing C12 the arm caught the BMC cable next to it, t | robot | 1 of 3 runs | summary_faithful |
| C47 took about 4 min, arm kept re-planning around the bundle | robot | 3 of 3 runs |  |
| camera lost the port on F31 twice under the aisle LEDs, thir | robot | 3 of 3 runs |  |
| F28 tag printed for the P1 port, cable is on P2. swapped tag | robot | 3 of 3 runs |  |
| F03 scope fail, cleaned, passed second inspection | site | 3 of 3 runs |  |
| F17 dust on ferrule again - these jumpers came out of the ba | site | 3 of 3 runs |  |
| F09 jacket kinked right behind the connector, swapped in a n | site | 1 of 3 runs | summary_faithful |
| Kit for this rack came 2 copper patch cords short, pulled fr | site | 3 of 3 runs |  |
| Rear door locked, waited on a security badge for 20 min | site | 3 of 3 runs |  |
| Somebody left a laptop cart in the aisle, robot sat for 4 mi | site | 3 of 3 runs |  |
| cord for C33 is 0.5 m, needs 1 m to reach the mgmt switch wi | site | 3 of 3 runs |  |
| F14 bend radius blown near the boot, cable came that way out | site | 3 of 3 runs |  |
| Tray 9 not in the rack yet when the robot got there, it skip | site | 2 of 3 runs | summary_faithful |
| F30 no link. Robot did it right per the map but the map had  | customer | 3 of 3 runs |  |
| F35 leaf port was admin-down, network team enabled it, link  | customer | 3 of 3 runs |  |
| MGMT-SW2 uplink not patched yet at shift start, network team | customer | 3 of 3 runs |  |
| Map rev C on the tablet and rev D on the rack sheet disagree | customer | 3 of 3 runs |  |
| Contractor walked into the aisle behind the rack while the a | safety | 3 of 3 runs |  |
| Arm swung toward my hand when I reached in to clear a zip ti | safety | 3 of 3 runs |  |
| Robot pinched my glove on the fiber tray door while I was ho | safety | 3 of 3 runs |  |
| Electrician working the PDU in this row pressed the stop as  | safety | 3 of 3 runs |  |
| something off with the fiber on this one, ask Dana | unclear | 3 of 3 runs |  |
| few ports flapping after lunch, not sure if it's us or the s | unclear | 3 of 3 runs |  |
| see photo | unclear | 0 of 3 runs | summary_faithful |

## Checks

| Check | Critical | Text |
|---|---|---|
| mode_correct |  | The note gets the right failure mode from the fixed list. |
| owner_correct |  | The note goes to the team that owns the fix. |
| safety_caught | yes | Every note about a person near the robot, an e-stop, or contact is flagged as safety. |
| no_false_safety |  | Notes with no person, e-stop or contact are not flagged as safety. |
| blocker_caught | yes | A live cable disturbed, or the robot moving toward or touching a person, blocks unsupervised work. |
| no_false_blocker |  | Other notes do not block unsupervised work. |
| review_when_unclear |  | Unclear notes go to a person; clear notes do not. |
| summary_faithful |  | The summary is one sentence that restates the tech note: what happened and, if the note says, what was done. It fails if it adds a cause, number, fix, actor or outcome that the note does not state or clearly imply, or if it contradicts the note. Plain paraphrase, expanding shorthand the note clearly means (a slot name such as C19 is the connection being made; the map is the customer's port map) and naming the rack are fine. |
