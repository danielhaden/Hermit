# Contributing to Hermit

## Branching workflow (GitHub Flow)

`main` is the stable, always-releasable branch. **Never commit directly to
`main`** — all changes land through a pull request.

1. **Branch off `main`:**
   ```bash
   git switch main && git pull
   git switch -c <type>/<short-description>
   ```
   Branch name prefixes:
   | Prefix                | For                            |
   |-----------------------|--------------------------------|
   | `feat/` or `feature/` | new features                   |
   | `fix/`                | bug fixes                      |
   | `chore/`              | tooling, deps, maintenance     |
   | `docs/`               | documentation only             |
   | `refactor/`           | non-behavioral restructuring   |

2. **Commit** in focused, logical steps (see commit style below).

3. **Push and open a PR** into `main`:
   ```bash
   git push -u origin <branch>
   ```
   Open the PR from the link the push prints, and fill in the template.

4. **Review happens in the browser**, by the repository owner. Merge once
   reviewed, then delete the branch.

## Commit style

- Imperative subject line ("Add …", "Fix …"), ~50 chars, no trailing period.
- A body explaining **why**, not just what, when the change isn't obvious.
- Keep unrelated changes in separate commits/PRs.

## This repository is public

Hermit is a public repo. Before every commit:

- **No personal data.** No real names, email addresses, or absolute paths such
  as `/Users/<name>/…`. Build paths from `Path.home()` or the data directory.
- **Commits are attributed to a GitHub noreply address**, so no email reaches
  the public history:
  ```bash
  git config user.name  "danielhaden"
  git config user.email "15604099+danielhaden@users.noreply.github.com"
  ```
- **Never commit book files.** `*.pdf` and `*.epub` are gitignored; the library
  database (`*.db`) is too.

## Before opening a PR

- **Run the tests:** `pytest`. They run offscreen against a scratch
  `HERMIT_DATA_DIR` and generate their own PDFs, so they touch nothing of
  yours.
- **Run the app:** `python -m hermit` — confirm it launches and your change
  works.
- **GUI changes:** verify offscreen and inspect the result, e.g.
  ```bash
  QT_QPA_PLATFORM=offscreen python -c "..."  # build the window, drive it, assert
  ```
  Point `HERMIT_DATA_DIR` at a scratch directory so tests never touch the real
  library.
- **Model changes:** exercise the affected model code directly.
- **Byte-compile check:** `python -m compileall -q hermit`.

## Design invariants (don't break these)

- **`hermit.model` must not import `QtWidgets`.** It stays free of the GUI so
  it can be driven headlessly. The one Qt dependency is `model/pdf_info.py`,
  which uses `QtPdf` to parse PDFs — Qt is the PDF engine, not the interface.
- **Books are indexed in place.** Adding a book records its path; Hermit never
  copies, moves, renames, or writes to a book file. Removing a book from the
  library leaves it on disk.
- **PDFs are identified by their `%PDF` header**, not by file extension —
  books are routinely saved without a `.pdf` suffix.
- **A book is whatever has a `%PDF` header.** Don't put an extension filter
  in front of the user — file dialogs must not hide books stored without a
  `.pdf` suffix, which is common.
- **Reading position is restored behind a guard.** `ReaderView._restore_page`
  suppresses position recording while the view settles. Without it,
  fit-to-width relayout lands the jump on a page boundary and walks the saved
  page forward on every reopen. Don't remove the guard without a test proving
  the drift is gone.
- **All app state lives in one SQLite file** under the per-user data directory,
  overridable with `HERMIT_DATA_DIR`.

## House conventions

- Default branch is `main`.
- `.venv/` and `__pycache__/` are gitignored; never commit them.
- Keep `STATUS.md` current at the end of a working session that changed the
  project.
