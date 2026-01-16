# Claude Code Instructions for Splitics

This file provides instructions for Claude Code when working on the splitics modernization project.

## Project Overview

**Splitics** is a single-file Python utility that splits large ICS calendar files into smaller chunks for Google Calendar import (which has a ~1MB file size limit).

### Key Constraints

- **Single file**: The script must remain a single Python file (`splitics.py`) with zero runtime dependencies
- **Python 3.10+**: Target Python 3.10 or higher
- **Simplicity**: Keep the code simple and readable - don't over-engineer

### Project Structure

```
splitics/
├── splitics.py          # Main script (single file, no runtime deps)
├── README.md            # User documentation
├── LICENSE              # Unlicense (public domain)
├── Plan.md              # Modernization plan with PR breakdown
├── Claude.md            # This file
├── pyproject.toml       # Dev dependencies only (pytest)
└── tests/
    ├── __init__.py
    ├── test_parse_size.py
    ├── test_split.py
    └── fixtures/
        ├── simple.ics
        ├── medium.ics
        └── malformed.ics
```

## Development Workflow

### Before Making Any Changes

1. **Read the Plan**: Check `Plan.md` to understand which PR you're implementing
2. **Run tests**: Ensure all existing tests pass before starting

```bash
pytest -v
```

### Implementation Feedback Loop

For EVERY change to `splitics.py`:

1. **Make the change** to `splitics.py`
2. **Run tests immediately** after the change:
   ```bash
   pytest -v
   ```
3. **If tests fail**: Fix the issue before proceeding
4. **If tests pass**: Continue with the next change

### After Completing a PR

1. Run full test suite: `pytest -v`
2. Verify the script still works manually with a test file
3. Commit with a clear message referencing the PR
4. Push to the branch
5. Stop and notify the user before starting the next PR

## Test Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_parse_size.py

# Run tests matching a pattern
pytest -k "test_parse"

# Run with coverage (if pytest-cov installed)
pytest --cov=splitics
```

## PR Implementation Order

Implement PRs in this order, stopping after each one for review:

1. **PR 0**: Test harness setup (create tests directory, fixtures, pyproject.toml)
2. **PR 1**: Fix ICS format bug (preserve calendar header in split files)
3. **PR 2**: Fix output file naming (`input_part1.ics` format, `--output-prefix`)
4. **PR 3**: Add user feedback (summary output, `--quiet`, `--version`)
5. **PR 4**: Code cleanup & refactor (class-based, type hints, remove dead code)
6. **PR 5**: Add `--dry-run` and `--overwrite` flags
7. **PR 6**: Progress indicator and better error handling

## Commit Message Format

Use clear, descriptive commit messages:

```
PR0: Set up test harness with pytest

- Add pyproject.toml with dev dependencies
- Create test fixtures (simple.ics, medium.ics, malformed.ics)
- Add unit tests for parse_size()
- Add integration tests for splitting logic
```

## Important Reminders

### Do

- Run `pytest -v` after every change to `splitics.py`
- Keep the script as a single file
- Write tests for new functionality
- Update existing tests when behavior changes
- Stop after each PR for review

### Don't

- Add runtime dependencies to `splitics.py`
- Create additional Python modules (keep it single-file)
- Skip running tests
- Combine multiple PRs into one commit
- Over-engineer simple solutions

## ICS File Format Reference

Basic ICS structure:

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example//Calendar//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
DTSTART:20240101T100000Z
DTEND:20240101T110000Z
SUMMARY:Meeting
UID:event1@example.com
END:VEVENT
BEGIN:VEVENT
...
END:VEVENT
END:VCALENDAR
```

Key points:
- Calendar starts with `BEGIN:VCALENDAR` and ends with `END:VCALENDAR`
- Events are wrapped in `BEGIN:VEVENT` / `END:VEVENT`
- Properties like VERSION, PRODID appear after `BEGIN:VCALENDAR` but before any events
- When splitting, each output file needs the full header (not just `BEGIN:VCALENDAR`)
