#!/usr/bin/env python3
"""
Split large ICS calendar files into smaller chunks.

This script takes an .ics calendar file and splits it into smaller files.
You can split the file based on the file size, number of events, or both.
It's useful when you want to migrate a calendar into Google Calendar,
since it will only accept files that are smaller than about 1MB.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
from typing import TextIO

__version__ = "2.0.0"


def parse_size(size_str: str) -> int:
    """
    Parse a human-readable size string to bytes.

    Accepts formats like '1M', '500K', '1MB', '500kb'.
    Only kilobytes and megabytes are supported.

    Args:
        size_str: Size specification (e.g., '1M', '500K')

    Returns:
        Size in bytes

    Raises:
        ValueError: If the size specification is invalid
    """
    sizes = {
        'K': 1024,
        'M': 1024 * 1024,
    }

    pattern = re.compile(r'^(\d+)([Kk]|M)[Bb]?$')
    match = pattern.match(size_str)
    if not match:
        raise ValueError(f"Cannot understand size specification {size_str}")

    value, unit = match.groups()
    return int(value) * sizes[unit.upper()]


class CalendarSplitter:
    """Splits ICS calendar files into smaller chunks."""

    BEGIN_CALENDAR = "BEGIN:VCALENDAR\n"
    END_CALENDAR = "END:VCALENDAR\n"
    END_EVENT = "END:VEVENT"
    BEGIN_EVENT = "BEGIN:VEVENT"

    def __init__(
        self,
        input_file: TextIO,
        max_size: int,
        max_events: int | float,
        encoding: str,
        output_dir: str,
        output_prefix: str,
        dry_run: bool = False,
        overwrite: bool = False,
    ) -> None:
        """
        Initialize the calendar splitter.

        Args:
            input_file: Open file handle for the input ICS file
            max_size: Maximum size per output file in bytes
            max_events: Maximum number of events per output file
            encoding: File encoding for output files
            output_dir: Directory for output files
            output_prefix: Prefix for output filenames
            dry_run: If True, don't write files, just show what would be created
            overwrite: If True, overwrite existing files without warning
        """
        self.input_file = input_file
        self.max_size = max_size
        self.max_events = max_events
        self.encoding = encoding
        self.output_dir = output_dir
        self.output_prefix = output_prefix
        self.dry_run = dry_run
        self.overwrite = overwrite

        # State variables
        self._stream: io.StringIO = io.StringIO()
        self._current_size: int = 0
        self._event_count: int = 0
        self._file_count: int = 0
        self._calendar_header: str = ""
        self._header_captured: bool = False
        self._output_files: list[dict[str, str | int]] = []

    def _dump(self) -> None:
        """Write the current buffer to a file and track output info."""
        filename = f"{self.output_prefix}_part{self._file_count + 1}.ics"
        output_path = os.path.join(self.output_dir, filename)
        content = self._stream.getvalue()

        if not self.dry_run:
            if os.path.exists(output_path) and not self.overwrite:
                raise FileExistsError(
                    f"Output file already exists: {output_path}\n"
                    "Use --overwrite to replace existing files."
                )
            with open(output_path, "w", encoding=self.encoding) as outfile:
                outfile.write(content)

        self._output_files.append({
            'filename': filename,
            'size': len(content.encode(self.encoding)),
            'events': self._event_count,
        })

    def split(self) -> list[dict[str, str | int]]:
        """
        Split the input file into smaller chunks.

        Returns:
            List of dictionaries with info about each output file
            (filename, size in bytes, event count)
        """
        header_buffer = io.StringIO()

        for line in self.input_file:
            # Capture header lines until we hit the first BEGIN:VEVENT
            if not self._header_captured:
                if line.startswith(self.BEGIN_EVENT):
                    self._header_captured = True
                    self._calendar_header = header_buffer.getvalue()
                else:
                    header_buffer.write(line)
                    self._stream.write(line)
                    self._current_size += len(line)
                    continue

            # Copy the file line by line, tracking the current file size
            self._stream.write(line)
            self._current_size += len(line)

            if line.startswith(self.END_EVENT):
                self._event_count += 1
                if self._current_size > self.max_size or self._event_count >= self.max_events:
                    # Reached a rollover point: write the calendar's end and flush
                    self._stream.write(self.END_CALENDAR)
                    self._dump()

                    # Reset the stream with the calendar header
                    self._stream = io.StringIO()
                    self._stream.write(self._calendar_header)
                    self._current_size = 0
                    self._event_count = 0
                    self._file_count += 1

        # Flush the last part of the file
        self._dump()

        return self._output_files

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format a size in bytes as a human-readable string."""
        size_kb = size_bytes / 1024
        if size_kb >= 1024:
            return f"{size_kb / 1024:.1f} MB"
        return f"{size_kb:.0f} KB"

    def print_summary(self, output_files: list[dict[str, str | int]] | None = None) -> None:
        """Print a summary of the split operation."""
        files = output_files if output_files is not None else self._output_files
        count = len(files)
        action = "Would split" if self.dry_run else "Split"
        print(f"{action} into {count} file{'s' if count != 1 else ''}:")

        for f in files:
            size_str = self.format_size(int(f['size']))
            events = f['events']
            print(f"  {f['filename']} ({size_str}, {events} event{'s' if events != 1 else ''})")


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Split large ICS calendar files into smaller chunks.',
        epilog='Example: %(prog)s calendar.ics -s 500K -n 50'
    )
    parser.add_argument('input', type=argparse.FileType('r'),
                        help='Input .ics calendar file to split')
    parser.add_argument('-s', '--size', type=str, default='1M',
                        help='Maximum size per output file, e.g., 500K or 1M (default: 1M)')
    parser.add_argument('-n', '--number', type=int, default=float('inf'),
                        help='Maximum number of events per output file')
    parser.add_argument('-e', '--encoding', type=str, default='utf8',
                        help='File encoding (default: utf8)')
    parser.add_argument('-o', '--output-prefix', type=str, default=None,
                        help='Prefix for output files (default: derived from input filename)')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Suppress output messages')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be created without writing files')
    parser.add_argument('--overwrite', action='store_true',
                        help='Overwrite existing output files without warning')
    parser.add_argument('-V', '--version', action='version',
                        version=f'%(prog)s {__version__}')

    args = parser.parse_args()

    # Parse size argument
    try:
        max_size = parse_size(args.size)
    except ValueError as e:
        print(e)
        return 1

    # Compute output directory and prefix
    input_path = os.path.abspath(args.input.name)
    output_dir = os.path.dirname(input_path)

    if args.output_prefix:
        output_prefix = args.output_prefix
    else:
        basename = os.path.basename(input_path)
        if basename.lower().endswith('.ics'):
            output_prefix = basename[:-4]
        else:
            output_prefix = basename

    # Create splitter and run
    splitter = CalendarSplitter(
        input_file=args.input,
        max_size=max_size,
        max_events=args.number,
        encoding=args.encoding,
        output_dir=output_dir,
        output_prefix=output_prefix,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
    )

    try:
        output_files = splitter.split()
    except FileExistsError as e:
        print(e, file=sys.stderr)
        return 1

    if not args.quiet:
        splitter.print_summary(output_files)

    return 0


if __name__ == '__main__':
    sys.exit(main())
