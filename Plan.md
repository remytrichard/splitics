# Splitics Modernization Plan

This document outlines the plan to modernize the splitics codebase, a 9-year-old Python utility that splits large ICS calendar files into smaller chunks for Google Calendar import.

## Goals

- Fix bugs and improve correctness
- Improve user experience
- Clean up technical debt
- Maintain simplicity: **single Python file, zero external dependencies**
- Target Python 3.10+

## Current Issues

| Priority | Issue | Impact |
|----------|-------|--------|
| **Critical** | Split files are malformed - only `BEGIN:VCALENDAR` is copied to new files, missing essential properties (VERSION, PRODID, CALSCALE, etc.) | Split files may fail to import |
| **High** | Output naming: `file.ics.0.ics` (double extension) | Confusing for users |
| **Medium** | Silent operation - no feedback on results | Poor UX |
| **Medium** | No `--output` or `--prefix` option | Files created in current dir with awkward names |
| **Low** | Dead code (`else: continue`, `else: pass`) | Code smell |
| **Low** | Global variables (acknowledged by original author) | Maintainability |
| **Low** | No `--version` flag | Nice to have |

---

## PR 0: Test Harness Setup

**Goal:** Establish a test framework and baseline tests before any refactoring begins.

### Rationale

Having tests in place before modifying the code provides:
- A safety net to catch regressions during refactoring
- Documentation of expected behavior
- Confidence that changes work correctly
- A feedback loop during implementation

### Test Framework

**pytest** - Modern, ergonomic, widely used. Only a dev dependency, doesn't affect the "single file to download and run" goal.

### Project Structure

```
splitics/
├── splitics.py              # The script (unchanged)
├── Plan.md
├── Claude.md                # Implementation instructions for Claude Code
├── pyproject.toml           # Dev dependencies (pytest)
├── tests/
│   ├── __init__.py
│   ├── test_parse_size.py   # Unit tests for size parsing
│   ├── test_split.py        # Integration tests for splitting logic
│   └── fixtures/
│       ├── simple.ics       # Simple calendar (3-5 events)
│       ├── medium.ics       # ~20 events for split testing
│       └── malformed.ics    # Invalid ICS for error handling tests
```

### Test Coverage

| Area | Tests |
|------|-------|
| `parse_size()` | Valid inputs ("1M", "500k", "100K"), invalid inputs, edge cases |
| Splitting logic | Correct number of files, correct event distribution, size limits respected |
| ICS validity | Split files have proper headers, BEGIN/END tags balanced |
| CLI args | Default values, custom values, invalid combinations |
| Error handling | Missing file, bad encoding, invalid ICS (added in later PRs) |

### Files Created

- `pyproject.toml` - Project metadata and dev dependencies
- `tests/__init__.py` - Test package marker
- `tests/test_parse_size.py` - Unit tests for `parse_size()` function
- `tests/test_split.py` - Integration tests for the splitting functionality
- `tests/fixtures/*.ics` - Sample ICS files for testing

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_parse_size.py
```

---

## PR 1: Fix ICS Format Bug

**Goal:** Ensure split files are valid ICS files that will actually import.

### Problem

When the script starts a new split file, it only writes `BEGIN:VCALENDAR\n` as the header. However, valid ICS files require additional properties that appear between `BEGIN:VCALENDAR` and the first `BEGIN:VEVENT`, such as:

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example//Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
...
```

Currently, split files (except the first) are missing VERSION, PRODID, etc., which may cause import failures.

### Solution

- During initial parsing, capture the full calendar header (everything from `BEGIN:VCALENDAR` up to and excluding the first `BEGIN:VEVENT`)
- Store this header and use it when starting each new split file
- This ensures all split files have identical, valid headers

### Files Changed

- `splitics.py`

---

## PR 2: Fix Output File Naming

**Goal:** Clean up the awkward double-extension naming and add output customization.

### Problem

Current output: `my_calendar.ics.0.ics`, `my_calendar.ics.1.ics` (double `.ics` extension, 0-indexed)

### Solution

- Change output format to: `my_calendar_part1.ics`, `my_calendar_part2.ics` (1-indexed)
- Add `--output-prefix` option to allow custom naming: `--output-prefix backup` produces `backup_part1.ics`, etc.
- Write output files to the same directory as the input file (not current working directory)

### New CLI Options

```
-o, --output-prefix PREFIX    Prefix for output files (default: derived from input filename)
```

### Files Changed

- `splitics.py`
- `README.md` (update examples)

---

## PR 3: Add User Feedback

**Goal:** Make the tool more user-friendly with output feedback.

### Changes

1. **Print summary when done:**
   ```
   Split into 3 files:
     my_calendar_part1.ics (847 KB, 42 events)
     my_calendar_part2.ics (923 KB, 45 events)
     my_calendar_part3.ics (312 KB, 18 events)
   ```

2. **Add `--quiet` flag** for silent operation (current behavior)

3. **Add `--version` flag** to display version information

4. **Improve help text** with better argument descriptions

### New CLI Options

```
-q, --quiet      Suppress output messages
-V, --version    Show version and exit
```

### Files Changed

- `splitics.py`
- `README.md`

---

## PR 4: Code Cleanup and Refactor

**Goal:** Clean up technical debt while keeping single-file simplicity.

### Changes

1. **Refactor to class-based approach:**
   - Create a `CalendarSplitter` class to encapsulate state
   - Remove global variables (`stream`, `size`, `event_count`, `file_count`, `args`)
   - Keep `parse_size()` as a standalone utility function

2. **Remove dead code:**
   - Remove `else: continue` on line 92-93
   - Remove meaningless `else: pass` on lines 95-97

3. **Add type hints** (Python 3.10+ style):
   - Function signatures
   - Class attributes
   - Use `str | None` syntax instead of `Optional[str]`

4. **Update Python version markers:**
   - Keep shebang: `#!/usr/bin/env python3`
   - Remove legacy encoding declaration (not needed in Python 3)
   - Add minimum version check or document requirement

5. **Update README:**
   - Document Python 3.10+ requirement
   - Update examples with new options
   - Add installation/usage section

### Files Changed

- `splitics.py`
- `README.md`

---

## PR 5: Add Dry-Run and Overwrite Flags

**Goal:** Give users more control over file writing behavior.

### Changes

1. **Add `--dry-run` flag:**
   - Show what files would be created without actually writing them
   - Display projected file sizes and event counts
   - Useful for previewing before committing to disk

2. **Add `--overwrite` flag:**
   - Current behavior: silently overwrites existing files
   - New behavior: check if output files exist, warn and exit if they do
   - With `--overwrite`: allow overwriting (explicit consent)

### New CLI Options

```
--dry-run        Show what would be created without writing files
--overwrite      Overwrite existing output files without warning
```

### Example Output (dry-run)

```
Dry run - no files written
Would create 3 files:
  my_calendar_part1.ics (~850 KB, ~43 events)
  my_calendar_part2.ics (~920 KB, ~46 events)
  my_calendar_part3.ics (~310 KB, ~16 events)
```

### Files Changed

- `splitics.py`
- `README.md`

---

## PR 6: Progress Indicator and Error Handling

**Goal:** Improve feedback for large files and provide better error messages.

### Changes

1. **Progress indicator for large files:**
   - Show progress when processing files (e.g., percentage or event count)
   - Only display for files above a certain threshold (e.g., >1000 events)
   - Respect `--quiet` flag

2. **Better error messages:**
   - Non-existent input file: clear message instead of Python traceback
   - Invalid ICS file: detect and warn if file doesn't look like valid ICS
   - Permission errors: helpful message if can't write to output directory
   - Encoding errors: suggest trying different encoding

### Example Error Messages

```
Error: Input file 'calendar.ics' not found.

Error: Cannot write to '/readonly/dir/' - permission denied.
       Try specifying a different output location with --output-prefix.

Error: File doesn't appear to be a valid ICS file (missing BEGIN:VCALENDAR).

Warning: Encoding error on line 1547. Try: splitics.py calendar.ics -e latin1
```

### Files Changed

- `splitics.py`
- `README.md`

---

## Summary

| PR | Title | Complexity | Risk |
|----|-------|------------|------|
| 0 | Test harness setup | Low | None |
| 1 | Fix ICS format bug | Medium | Low (fixes a bug) |
| 2 | Fix output file naming | Low | Low |
| 3 | Add user feedback | Low | Low |
| 4 | Code cleanup & refactor | Medium | Medium (refactoring) |
| 5 | Add dry-run and overwrite flags | Low | Low |
| 6 | Progress indicator & error handling | Medium | Low |

## Implementation Notes

- Each PR should be self-contained and independently reviewable
- PRs can be merged in order; later PRs may depend on earlier ones
- All changes maintain the single-file, zero-dependency philosophy
- Target Python 3.10+ for all changes
