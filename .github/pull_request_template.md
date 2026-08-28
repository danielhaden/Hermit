## Summary

<!-- What does this PR do, and why? -->

## Changes

<!-- Bullet the notable changes. -->
-

## Testing

<!-- How did you verify this? App run, offscreen render, model checks. -->
- [ ] `python -m hermit` launches and the change works
- [ ] `python -m compileall -q hermit` passes
- [ ] GUI changes verified with an offscreen run (output or screenshot below)
- [ ] Ran against a scratch `HERMIT_DATA_DIR`, not the real library

## Screenshots

<!-- For UI changes. -->

## Checklist

- [ ] Branch follows the naming convention (`feat/`, `fix/`, `chore/`, …)
- [ ] No personal data: no real names, emails, or `/Users/<name>/…` paths
- [ ] No book files or `.db` files committed
- [ ] `hermit.model` still free of `QtWidgets`
- [ ] Books are still indexed in place — nothing copies, moves, or writes to them
- [ ] `STATUS.md` updated if the project state changed
