---
description: Run the full loop for the next uncompleted phase only, then stop at the acceptance gate and report.
agent: glass-conductor
---

Read `docs/ROADMAP.md`, `docs/PROGRESS-LOG.md`, and `docs/HEALTH-LOG.md` to
establish state from disk, exactly as `/run-block` does.

Run the full loop — brief, build, test, review (up to 3 fix cycles), docs,
checkpoint, monitor — for the next uncompleted phase ONLY. Stop at the
acceptance gate and report, including the health verdict.

This is fine-grained control; `/run-block` is the default cadence.
