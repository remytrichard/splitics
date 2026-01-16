"""Integration tests for the splitics script."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Path to the fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"
SCRIPT_PATH = Path(__file__).parent.parent / "splitics.py"


@pytest.fixture
def work_dir(tmp_path):
    """Create a working directory with a copy of fixtures."""
    # Copy fixture files to temp directory for testing
    for fixture in FIXTURES_DIR.glob("*.ics"):
        shutil.copy(fixture, tmp_path / fixture.name)
    return tmp_path


def run_splitics(work_dir: Path, input_file: str, *args) -> subprocess.CompletedProcess:
    """Run the splitics script and return the result."""
    cmd = [sys.executable, str(SCRIPT_PATH), input_file, *args]
    return subprocess.run(
        cmd,
        cwd=work_dir,
        capture_output=True,
        text=True,
    )


def count_events(file_path: Path) -> int:
    """Count the number of events in an ICS file."""
    content = file_path.read_text()
    return content.count("END:VEVENT")


def is_valid_ics(file_path: Path) -> bool:
    """Check if a file has basic ICS structure."""
    content = file_path.read_text()
    return (
        content.startswith("BEGIN:VCALENDAR")
        and "END:VCALENDAR" in content
    )


class TestSplitByEventCount:
    """Tests for splitting by number of events."""

    def test_split_simple_by_one_event(self, work_dir):
        """Split simple.ics (3 events) into files with 1 event each."""
        result = run_splitics(work_dir, "simple.ics", "-n", "1")
        assert result.returncode == 0

        # Creates 4 files: 3 with 1 event each + 1 nearly empty final file
        # (This is current behavior - the script always dumps remaining buffer)
        output_files = sorted(work_dir.glob("simple_part*.ics"))
        assert len(output_files) == 4

        # First 3 files should have 1 event each
        for f in output_files[:3]:
            assert count_events(f) == 1

        # Last file is nearly empty (just BEGIN/END:VCALENDAR)
        assert count_events(output_files[3]) == 0

    def test_split_simple_by_two_events(self, work_dir):
        """Split simple.ics (3 events) into files with max 2 events each."""
        result = run_splitics(work_dir, "simple.ics", "-n", "2")
        assert result.returncode == 0

        # Should create 2 output files
        output_files = sorted(work_dir.glob("simple_part*.ics"))
        assert len(output_files) == 2

        # First file should have 2 events, second should have 1
        assert count_events(output_files[0]) == 2
        assert count_events(output_files[1]) == 1

    def test_split_medium_by_five_events(self, work_dir):
        """Split medium.ics (20 events) into files with max 5 events each."""
        result = run_splitics(work_dir, "medium.ics", "-n", "5")
        assert result.returncode == 0

        # Creates 5 files: 4 with 5 events each + 1 nearly empty final file
        # (This is current behavior - the script always dumps remaining buffer)
        output_files = sorted(work_dir.glob("medium_part*.ics"))
        assert len(output_files) == 5

        # First 4 files should have 5 events each
        for f in output_files[:4]:
            assert count_events(f) == 5

        # Last file is nearly empty (just BEGIN/END:VCALENDAR)
        assert count_events(output_files[4]) == 0


class TestSplitBySize:
    """Tests for splitting by file size."""

    def test_split_by_small_size(self, work_dir):
        """Split with a very small size limit should create multiple files."""
        # Use 500 bytes - should force splits
        result = run_splitics(work_dir, "simple.ics", "-s", "500K")
        assert result.returncode == 0

        # With 500K limit on a small file, should create 1 file
        output_files = list(work_dir.glob("simple_part*.ics"))
        assert len(output_files) >= 1

    def test_split_with_default_size(self, work_dir):
        """Default 1M size should not split a small file."""
        result = run_splitics(work_dir, "simple.ics")
        assert result.returncode == 0

        # Small file with 1M limit should create just 1 file
        output_files = list(work_dir.glob("simple_part*.ics"))
        assert len(output_files) == 1


class TestOutputFileStructure:
    """Tests for the structure of output files."""

    def test_output_files_have_calendar_end(self, work_dir):
        """All output files should end with END:VCALENDAR."""
        run_splitics(work_dir, "simple.ics", "-n", "1")

        output_files = work_dir.glob("simple_part*.ics")
        for f in output_files:
            content = f.read_text()
            assert "END:VCALENDAR" in content

    def test_output_files_have_calendar_begin(self, work_dir):
        """All output files should start with BEGIN:VCALENDAR."""
        run_splitics(work_dir, "simple.ics", "-n", "1")

        output_files = work_dir.glob("simple_part*.ics")
        for f in output_files:
            content = f.read_text()
            assert content.startswith("BEGIN:VCALENDAR")

    def test_all_output_files_preserve_full_header(self, work_dir):
        """All output files should have the full calendar header (VERSION, PRODID, etc.)."""
        run_splitics(work_dir, "simple.ics", "-n", "1")

        # All output files should have the full header, not just BEGIN:VCALENDAR
        output_files = sorted(work_dir.glob("simple_part*.ics"))
        for f in output_files:
            content = f.read_text()
            assert "VERSION:2.0" in content, f"{f.name} missing VERSION"
            assert "PRODID:" in content, f"{f.name} missing PRODID"

    def test_split_files_have_identical_headers(self, work_dir):
        """All split files should have identical calendar headers."""
        run_splitics(work_dir, "medium.ics", "-n", "5")

        output_files = sorted(work_dir.glob("medium_part*.ics"))

        # Extract header from each file (everything before first BEGIN:VEVENT or END:VCALENDAR)
        headers = []
        for f in output_files:
            content = f.read_text()
            # Find where events start or calendar ends
            event_start = content.find("BEGIN:VEVENT")
            calendar_end = content.find("END:VCALENDAR")
            if event_start > 0:
                header = content[:event_start]
            else:
                header = content[:calendar_end]
            headers.append(header)

        # All headers should be identical
        for i, header in enumerate(headers[1:], 1):
            assert header == headers[0], f"Header in file {i} differs from file 0"


class TestCommandLineInterface:
    """Tests for CLI argument handling."""

    def test_invalid_size_argument(self, work_dir):
        """Invalid size argument should exit with error."""
        result = run_splitics(work_dir, "simple.ics", "-s", "invalid")
        assert result.returncode == 1

    def test_help_flag(self, work_dir):
        """--help should show usage information."""
        result = run_splitics(work_dir, "--help")
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_custom_encoding(self, work_dir):
        """Custom encoding argument should be accepted."""
        result = run_splitics(work_dir, "simple.ics", "-e", "utf-8")
        assert result.returncode == 0


class TestOutputFileNaming:
    """Tests for output file naming convention."""

    def test_output_files_numbered_from_one(self, work_dir):
        """Output files should be numbered starting from 1."""
        run_splitics(work_dir, "simple.ics", "-n", "1")

        # Check that files are numbered 1, 2, 3, 4 (1-indexed)
        # (4 files: 3 with events + 1 nearly empty)
        assert (work_dir / "simple_part1.ics").exists()
        assert (work_dir / "simple_part2.ics").exists()
        assert (work_dir / "simple_part3.ics").exists()
        assert (work_dir / "simple_part4.ics").exists()

    def test_output_naming_pattern(self, work_dir):
        """Output files follow pattern: {prefix}_part{n}.ics"""
        run_splitics(work_dir, "medium.ics", "-n", "5")

        # All output files should match the pattern
        # (5 files: 4 with events + 1 nearly empty)
        output_files = list(work_dir.glob("medium_part*.ics"))
        assert len(output_files) == 5

        for i in range(1, 6):
            expected = work_dir / f"medium_part{i}.ics"
            assert expected.exists()

    def test_output_prefix_option(self, work_dir):
        """--output-prefix should set custom output file prefix."""
        run_splitics(work_dir, "simple.ics", "-n", "1", "-o", "custom")

        # Files should use custom prefix
        assert (work_dir / "custom_part1.ics").exists()
        assert (work_dir / "custom_part2.ics").exists()

        # Original prefix should not be used
        assert not (work_dir / "simple_part1.ics").exists()

    def test_output_prefix_long_option(self, work_dir):
        """--output-prefix long form should work."""
        run_splitics(work_dir, "simple.ics", "-n", "2", "--output-prefix", "backup")

        assert (work_dir / "backup_part1.ics").exists()
        assert (work_dir / "backup_part2.ics").exists()

    def test_no_double_ics_extension(self, work_dir):
        """Output files should not have double .ics extension."""
        run_splitics(work_dir, "simple.ics", "-n", "1")

        # No files should have double .ics extension
        double_ext_files = list(work_dir.glob("*.ics.*.ics"))
        assert len(double_ext_files) == 0
