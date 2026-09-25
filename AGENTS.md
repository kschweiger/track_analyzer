# Repository Guidelines

## Project Structure

`geo_track_analyzer/` contains the library. Core track and data models live in `track.py` and `model.py`; format and analysis helpers are organized under `utils/`, `visualize/`, `cli/`, and `postgis/`. Tests are in `tests/`, with reusable GPX, FIT, GeoJSON, and other fixtures in `tests/resources/`. User documentation is in `docs/`; runnable examples and sample data are in `examples/`.

## Development and Test Commands

- `uv sync` installs the default development and test dependency groups.
- `uv run pytest` runs the test suite. Run one test with `uv run pytest tests/test_track.py::test_fit_track`.
- `make test-cov` runs tests with coverage reports (XML, JSON, and terminal output).
- `uv run ruff check .` checks lint; `uv run ruff format --check .` checks formatting.
- `pre-commit run --all-files` runs the configured Ruff and repository hygiene hooks.
- `uv build` builds the distributable package.

CI tests Python 3.11–3.14, including optional integrations. Database tests require PostGIS configuration; see `.github/workflows/test.yml` for the CI setup.

## Coding Style

Use Python 3.11+ and four-space indentation. Follow the 88-character Ruff line length and the lint rules in `pyproject.toml`. Use `snake_case` for functions, variables, and modules, and `PascalCase` for classes. Keep type annotations on public APIs and follow nearby patterns when extending the track, visualization, or format-handling code.

Export every public function intended for library users from the `__init__.py` of its relevant package. Functions in the top-level `geo_track_analyzer` package belong in `geo_track_analyzer/__init__.py`; functions belonging to a subpackage must be exported from that subpackage's `__init__.py`. Keep private or internal helpers unexported.

## Testing Guidelines

Use pytest with `test_*.py` files and `test_*` functions. Prefer real, small fixtures from `tests/resources/` when validating file parsing or track behavior. Assert meaningful output contracts and units with reasonable ranges when exact measurements are incidental. Add fixture files under `tests/resources/` and keep tests independent of personal files or local environment paths. No repository-wide coverage threshold is configured.

## Commits and Pull Requests

Recent history generally uses Conventional Commit prefixes such as `feat:`, `fix:`, `test:`, `build:`, and `doc:`; use a concise imperative summary (for example, `test: cover FIT distance units`). Pull requests should explain the behavior change, mention compatibility or unit changes, and list the tests and checks run. Link a related issue when applicable; include documentation updates for user-visible API changes.

Do not edit `CHANGELOG.md` manually. It is generated automatically during releases.
Releases are performed manually by a human using the release script in the repository root; agents must never run or perform a release.

## Configuration

Keep credentials and machine-specific settings out of commits. Use environment variables for local configuration and check `.gitignore` before adding generated coverage, build, or cache files.
