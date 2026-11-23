# Intervention note triage guide

A field tech writes a short note every time they step in during a supervised robot cabling shift.
Tag each note so the weekly report counts the right causes and the right team gets the fix.

## failure_mode (pick exactly one)
- not_latched: connector not fully seated or latched by the robot.
- wrong_port: robot landed the cable in a port other than the one on the port map.
- label_mismatch: the label on the cable does not match the port map label.
- live_disturbance: the robot knocked loose, unseated or pulled a live cable (one whose link was already up, on this rack or a neighbor).
- robot_fault: gripper, vision, arm or navigation fault on the robot (including retries the robot recovered from).
- slow_cycle: the robot finished on its own but far slower than normal.
- dirty_endface: fiber end face failed inspection and needed cleaning.
- damaged_cable: cable or connector arrived kinked, crushed, broken or bent past its radius.
- missing_or_short_cable: the cable kit was missing a cable or a cable was too short.
- access_blocked: the robot could not reach the work (locked door, missing tray, object in the aisle).
- customer_config: the customer's port map or switch configuration was wrong, out of date or unfinished.
- safety_stop: a person was in or near the robot's work zone, an e-stop was pressed, or the robot came close to or touched a person.
- unclear: the note does not say enough to pick a cause.

## owner
- robot_team: not_latched, wrong_port, label_mismatch, live_disturbance, robot_fault, slow_cycle, and any safety_stop where the robot moved toward or touched a person.
- site_ops: dirty_endface, damaged_cable, missing_or_short_cable, access_blocked, and any safety_stop caused by people or work around the robot.
- customer_network: customer_config.
- unknown: unclear.

## flags
- safety: true for every note about a person in or near the work zone, an e-stop, or the robot coming close to or touching a person, even with no injury. Otherwise false.
- blocks_unsupervised: true only when the robot disturbed a live connection, or moved toward or touched a person. These must be fixed before the robot works without a tech watching. Otherwise false.
- needs_review: true only when failure_mode is unclear. A person reads the note and asks the tech.

## summary
One plain sentence a customer's operations lead can read: what happened and, if the note says, what was done. Use only what the note says. Do not add causes, numbers, fixes, outcomes or who did what unless the note states it, and do not link two facts with "because" or "after" unless the note does.
