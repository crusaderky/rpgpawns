# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

`rpgpawns` is a Python library that converts images into two-sided paper-cut pawns for tabletop RPGs. The core flow is: image → scaled pawn with mirrored back → arranged collage on A4 pages → exported as PDF or image.

## Commands

This project uses [Pixi](https://pixi.sh/) for environment and task management.

```bash
pixi run tests                  # Run pytest
pixi run tests-cov              # Run pytest with coverage
pixi run lint                   # Run all linters (via lefthook)
pixi run docs                   # Build Sphinx docs
pixi run smoke-test             # Quick import sanity check
pixi run cli [args]             # Run the rpgpawns CLI
```

Run a single test file or test:

```bash
pixi run pytest rpgpawns/tests/test_pawn.py
pixi run pytest rpgpawns/tests/test_pawn.py::test_make_pawn -x
```

Slow tests are marked with `@pytest.mark.slow` and included by default.

## Architecture

### Core modules

**[rpgpawns/pawn.py](rpgpawns/pawn.py)** — All image processing logic:

- `PawnSize` enum (SMALL, MEDIUM, LARGE, HUGE): defines physical dimensions in mm
- `make_pawn()`: scales an image to fit within size constraints, mirrors it horizontally to create a two-sided pawn, adds white padding to ensure all pawns of the same size have identical height, and draws a faint grey fold line
- `make_collage()`: packs multiple pawns onto A4 pages using a row-based, tallest-first algorithm; uses `has_white_border()` to overlap white margins between adjacent pawns
- All dimensions are in mm internally and converted to pixels at 300 DPI

**[rpgpawns/cli.py](rpgpawns/cli.py)** — CLI entry point (`rpgpawns` command):

- `parse_image_args()`: parses the `path[:size][:count]` colon-separated format
- Wraps `make_pawn()` + `make_collage()` and saves to PDF or image

### Key design constraints

- Output is always 300 DPI RGB for print quality
- Pawns of the same `PawnSize` always have identical total height (white padding fills the difference), which is required for consistent collage row alignment
- The pawn image is mirrored so both sides are readable when the pawn is folded along the centre line

## Linting and Type Checking

The project uses strict mypy and ruff. Run `pixi run lint` to check everything. Type hints are mandatory — the package ships a `py.typed` marker.

Notable ruff ignores are defined in `pyproject.toml` under `[tool.ruff.lint]`. Do not add broad ignores; fix the underlying issue instead.

## Environments

| Pixi env          | Purpose                                        |
| ----------------- | ---------------------------------------------- |
| `default`         | Development (py3.14, all tools)                |
| `mindeps`         | Minimum supported deps (py3.11, Pillow 10.0)   |
| `py311` / `py314` | Version-specific test runs                     |
| `nogil`           | Free-threading (py3.14t + pytest-run-parallel) |
| `lint`            | Linting tools only                             |
| `docs`            | Sphinx documentation                           |

CI tests all environments across 5 OS/architecture combinations.
