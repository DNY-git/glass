---
description: Run every remaining phase in the current block through the full loop without per-phase stops, then present the block acceptance report.
agent: glass-conductor
---

Read `docs/ROADMAP.md`, `docs/PROGRESS-LOG.md`, and `docs/HEALTH-LOG.md` to
establish state from disk.

Determine the current block: the block containing the first unaccepted
phase, per the block table (Block 1 = Phases 1-3, Block 2 = 4-6,
Block 3 = 7-9, Block 4 = 10-12, Block 5 = 13).

Run every remaining phase in that block through the full loop — brief,
build, test, review (up to 3 fix cycles each), docs, checkpoint, monitor
sweep — without stopping between phases. Halt immediately on any hard-stop
condition, including a monitor ERROR.

At block end, present the block acceptance report and wait for acceptance.
