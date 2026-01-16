#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""
This script takes an .ics calendar file and splits it into smaller files.
You can split the file based on the file size, number of events, or both.
It's useful when you want to migrate a calendar into Google Calendar,
since it will only accept files that are smaller than about 1MB.
"""

# This script is full of globals. Please don't program like this.
# It's 11PM on a saturday. I'll come back and refactor it, I swear [1]

import argparse
import io
import os
import re
import sys

__version__ = "2.0.0"


def parse_size(s):
    """
    Parses a human-readable size to a number of bytes.
    Only accepts kilos and megs because seriously, there's no point in other units (not for ics files anyway).
    """
    sizes = {
        'K': 1024,
        'M': 1024 * 1024,
    }

    pattern = re.compile('^(\d+)([Kk]|M)[Bb]?$')
    match = pattern.match(s)
    if not match:
        raise ValueError("Cannot understand size specification {}".format(s))

    v, u = match.groups()
    return int(v) * sizes[u.upper()]


BEGIN_CALENDAR = "BEGIN:VCALENDAR\n"
END_CALENDAR = "END:VCALENDAR\n"
END_EVENT = "END:VEVENT"
BEGIN_EVENT = "BEGIN:VEVENT"


def dump():
    """
    Dumps the current stream to file and tracks output info.
    """
    global output_files
    # Use 1-indexed naming: prefix_part1.ics, prefix_part2.ics, etc.
    filename = "{}_part{}.ics".format(output_prefix, file_count + 1)
    output_path = os.path.join(output_dir, filename)
    content = stream.getvalue()
    with open(output_path, "w", encoding=args.encoding) as outfile:
        outfile.write(content)
    # Track file info for summary
    output_files.append({
        'filename': filename,
        'size': len(content.encode(args.encoding)),
        'events': event_count
    })


if __name__ == '__main__':

    # region Setup argparse
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
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)

    args = parser.parse_args(sys.argv[1:])
    try:
        args.size = parse_size(args.size)
    except ValueError as e:
        print(e)
        sys.exit(1)

    # Compute output directory and prefix
    input_path = os.path.abspath(args.input.name)
    output_dir = os.path.dirname(input_path)
    if args.output_prefix:
        output_prefix = args.output_prefix
    else:
        # Derive prefix from input filename (strip .ics extension if present)
        basename = os.path.basename(input_path)
        if basename.lower().endswith('.ics'):
            output_prefix = basename[:-4]
        else:
            output_prefix = basename
    # endregion

    stream = io.StringIO()
    size, event_count, file_count = 0, 0, 0
    output_files = []  # Track output files for summary

    # Capture the calendar header (everything before the first event)
    calendar_header = io.StringIO()
    header_captured = False

    for line in args.input:

        # Capture header lines until we hit the first BEGIN:VEVENT
        if not header_captured:
            if line.startswith(BEGIN_EVENT):
                header_captured = True
                calendar_header = calendar_header.getvalue()
            else:
                calendar_header.write(line)
                stream.write(line)
                size += len(line)
                continue

        # Copy the file line by line, tracking the current file size
        stream.write(line)
        size += len(line)

        if line.startswith(END_EVENT):
            event_count += 1
            if size > args.size or event_count >= args.number:
                # Reached a rollover point: write the calendar's end and flush the file.
                stream.write(END_CALENDAR)

                dump()

                # Reset the stream (using the full calendar header)
                stream = io.StringIO()
                stream.write(calendar_header)
                size, event_count = 0, 0

                file_count += 1
            else:
                continue

    else:
        # Finished the file, nothing to do except flushing
        pass

    # Flush the last part of the file. There's no need to add the calendar's end (the file already has it).
    dump()

    # Print summary unless quiet mode
    if not args.quiet:
        total_events = sum(f['events'] for f in output_files)
        print("Split into {} file{}:".format(
            len(output_files),
            's' if len(output_files) != 1 else ''
        ))
        for f in output_files:
            size_kb = f['size'] / 1024
            if size_kb >= 1024:
                size_str = "{:.1f} MB".format(size_kb / 1024)
            else:
                size_str = "{:.0f} KB".format(size_kb)
            print("  {} ({}, {} event{})".format(
                f['filename'],
                size_str,
                f['events'],
                's' if f['events'] != 1 else ''
            ))


# [1] Never gonna happen
