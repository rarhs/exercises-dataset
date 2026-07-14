# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A static fitness exercise dataset (1,324 exercises, 9 instruction languages) plus two self-contained HTML tools. There is no build system, package manager, linter, or test suite — the "code" is vanilla HTML/CSS/JS inlined in two files, and the product is the data itself.

## Commands

```powershell
# Serve locally (required for setup.html, which fetches data/exercises.json at
# runtime; index.html also works when opened directly via file://)
python -m http.server 8000

# Validate schema + check index.html EXERCISES blob is in sync (what CI runs;
# requires: pip install jsonschema)
python scripts/validate_dataset.py
```

CI (`.github/workflows/validate.yml`) runs `scripts/validate_dataset.py` on every push and PR.

## Architecture

**`data/exercises.json` is the source of truth**, but the dataset exists in TWO places:

1. `data/exercises.json` — the canonical JSON array (fetched by `setup.html`)
2. `index.html` — the same data embedded inline as `const EXERCISES = [...]` (~line 1172; this is why the file is ~15 MB)

**Any data change must be applied to both**, or the browser UI and the published dataset drift apart.

Everything is connected by filename convention: a record's `id` (zero-padded 4 digits) + `media_id` form the media filenames — exercise `0001` / `2gPfomN` → `images/0001-2gPfomN.jpg` (static 180×180 thumbnail) and `videos/0001-2gPfomN.gif` (animation — GIF files, not video). The records' `image` / `gif_url` fields carry these relative paths. IDs are not contiguous (some numbers are skipped); never renumber.

`index.html` grid cards show the static thumbnail; the animated GIF appears only in the click-to-open detail modal.

## Changing the data

- Validate edits against `data/exercises.schema.json`. The schema `require`s the original six languages (`en`, `es`, `it`, `tr`, `ru`, `zh`); `hi`, `pl`, `ko` pass via `additionalProperties`.
- Instructions exist in two parallel shapes per record and must stay in sync: `instructions.<lang>` (single string) and `instruction_steps.<lang>` (array of step strings).
- **Adding a language** (see commits for Hindi/Polish/Korean as precedent): add `instructions.<lang>` + `instruction_steps.<lang>` to every record in *both* copies of the data, add the language to `LANG_LABELS` and the `langs` array in `index.html` (~line 1527), and update the README (language count badge, Overview, Data Schema table, usage examples).
- **Adding/removing exercises**: also update the hard-coded counts (1,324) in README badges/tables/statistics and drop the correctly named media pair into `images/` and `videos/`.

## Licensing constraint that affects changes

Code, data structure, and instruction text are MIT — but all media in `images/` and `videos/` is **© Gym visual, redistributed with permission, at 180×180 only** (see `NOTICE.md`). Keep every record's `attribution` field and the `© Gym visual — https://gymvisual.com/` notices intact, and never upscale or replace media resolution beyond 180×180.

### Convention about commit messages

- Never add Co-Authored-By to commit messages

## Git workflow (must follow)

Never commit to or push `main` directly. For every change: create a feature branch, commit there, push the branch, and merge it into `main` (preferably via PR so the validate workflow gates the merge). This is enforced by a GitHub ruleset on `main` (PRs required, `validate` status check must pass, no force pushes or deletions) — direct pushes to `main` are rejected server-side.

## Deployment

Merges to `main` auto-deploy via GitHub Pages: `index.html` is served at https://rarhs.github.io/exercises-dataset/. A broken `index.html` on `main` breaks a live public page, not just a local file.