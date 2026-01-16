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

This project uses `uv` for dependency management.

```bash
# Run all tests (uv handles venv and dependencies automatically)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_parse_size.py

# Run tests matching a pattern
uv run pytest -k "test_parse"

# Run with coverage (if pytest-cov installed)
uv run pytest --cov=splitics

# Or sync dependencies first, then run pytest directly
uv sync
pytest -v
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

## Git Commit Guidelines

Use **Conventional Commits** format for all commit messages.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring, no feature change |
| `test` | Adding or updating tests |
| `chore` | Build, config, tooling changes |

### Scope

Use the PR number as scope: `pr0`, `pr1`, etc.

### Examples

```
test(pr0): add pytest infrastructure and baseline tests

- Add pyproject.toml with dev dependencies
- Create test fixtures (simple.ics, medium.ics)
- Add unit tests for parse_size()
- Add integration tests for splitting logic
```

```
fix(pr1): preserve calendar header in split files

The split files were missing VERSION, PRODID, and other required
properties, causing import failures in Google Calendar.

- Capture full header during initial parsing
- Use complete header when starting each new split file
```

```
feat(pr2): improve output file naming

- Change output from input.ics.0.ics to input_part1.ics
- Add --output-prefix option for custom naming
```

### Rules

- Use imperative mood: "add feature" not "added feature"
- First line max 72 characters
- Body wrapped at 72 characters
- Reference issues/PRs in footer if applicable

## Engineering Best Practices

Follow these practices like a senior software engineer:

### Code Quality

- **Read before writing**: Always read existing code before modifying
- **Minimal changes**: Only change what's necessary for the task
- **No dead code**: Remove unused code, don't comment it out
- **Clear naming**: Use descriptive variable/function names
- **Single responsibility**: Each function does one thing well

### Testing

- **Test first**: Write or update tests before implementing
- **Test edge cases**: Cover boundary conditions and error paths
- **Descriptive test names**: `test_parse_size_returns_bytes_for_megabytes`
- **Independent tests**: Tests should not depend on each other

### Error Handling

- **Fail fast**: Validate inputs early
- **Clear messages**: Error messages should explain what went wrong and how to fix it
- **No silent failures**: Don't swallow exceptions without logging

### Documentation

- **Self-documenting code**: Prefer clear code over comments
- **Docstrings**: Add for public functions with non-obvious behavior
- **Update README**: Keep user documentation current

### Git Workflow

- **Atomic commits**: Each commit is a complete, working change
- **Review before commit**: `git diff --staged` before committing
- **Don't commit broken code**: All tests must pass
- **Push frequently**: Don't accumulate unpushed commits

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
