# mgt409-homework

Coursework repository for MGT 409, set up as a Python project for assignments,
analysis, and Jupyter notebooks.

## Getting started

Requires Python 3.12 (already available in the Cloud Agent environment).

```bash
# One-time setup: creates a .venv and installs dependencies
make install
# or: bash .cursor/install.sh

# Activate the virtual environment
source .venv/bin/activate
```

## Common tasks

| Command | Description |
| --- | --- |
| `make test` | Run the test suite with pytest |
| `make demo` | Run the end-to-end demo analysis (prints a report, saves a chart to `artifacts/`) |
| `make lab`  | Start Jupyter Lab on port 8888 |

## Layout

```
src/mgt409/        Reusable helpers (statistics utilities), importable as `mgt409`
tests/             Pytest test suite
scripts/           Runnable analysis scripts
.cursor/           Cloud Agent environment config + install script
```

## Adding an assignment

Put shared, reusable logic in `src/mgt409/` (and add tests in `tests/`), then
write assignment-specific scripts in `scripts/` or notebooks at the repo root
that import from `mgt409`.
