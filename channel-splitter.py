#!/usr/bin/env python3

# Batch Audio Channel Splitter (chmaha)

# Splits one or more input files by the integer pattern made up of single digits.
# e.g. 32 splits the file into a 3-channel file, followed by as many stereo files as possible.
# Mono files are created for any remaining channels.
# 
# Supports wav, flac, aiff and wavpack input.
# Output naming adds an identifying suffix.
# For example, output[3-4].wav is a file containing channels 3 and 4. 
#
# Further examples: 
# python channel-splitter.py 2 *.wav 
# - creates a series of stereo files followed by a mono remainder if needed.
# 
# python channel-splitter.py 221 *.flac 
# - creates two stereo files followed by a series of mono files.
#
# Copyright (C) 2025 chmaha
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import os
import subprocess
import sys


def check_sox_installed():
    """Check if SoX is installed."""
    # Check if SoX is in PATH
    try:
        subprocess.run(["sox", '--version'],
                       capture_output=True, text=True, check=True)
        return "sox"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # On Windows, check common installation paths
    if os.name == 'nt':
        common_paths = [
            r"C:\\Program Files (x86)\\sox-*",
            r"C:\\Program Files\\sox-*"
        ]

        for base_path in common_paths:
            path_pattern = os.path.join(base_path, "sox.exe")
            for sox_path in glob.glob(path_pattern):
                if os.path.exists(sox_path):
                    return sox_path

    # If SoX isn't found, inform the user
    if os.name == "posix":
        print("Error: SoX is not installed or not in PATH.")
        print("On Linux, you can install it with your package manager. For example:")
        print("  - On Debian/Ubuntu-based systems: sudo apt install sox")
        print("  - On Red Hat/Fedora/CentOS-based systems: sudo dnf install sox")
        print("  - On Arch-based systems: sudo pacman -S sox")
        print("On macOS, you can install it with: brew install sox")
    else:
        print("Download and install SoX from: http://sox.sourceforge.net/")
    sys.exit(1)


def validate_grouping_pattern(grouping_pattern, total_channels):
    """Validate the grouping pattern against the total channel count."""
    if len(grouping_pattern) == 1 and int(grouping_pattern) == total_channels:
        print(f"Error: The grouping pattern '{grouping_pattern}' is the same as the total channel count ({total_channels}). No splitting needed.")
        return False

    # Check if the sum of the digits in the grouping pattern exceeds the total channels
    total_pattern = sum(int(digit) for digit in grouping_pattern)
    if total_pattern > total_channels:
        print(f"Error: The sum of the digits in the grouping pattern ({total_pattern}) exceeds the number of channels ({total_channels}).")
        return False

    return True


def check_files_exist(input_file, grouping_pattern):
    """Check if any output files already exist."""
    channel_start = 1
    remaining_channels = int(subprocess.run(['sox', '--i', '-c', input_file], capture_output=True, text=True).stdout.strip())
    pattern_index = 0
    existing_files = []

    while remaining_channels > 0:
        # Determine group size based on the pattern
        if pattern_index < len(grouping_pattern):
            group_size = int(grouping_pattern[pattern_index])
            pattern_index += 1
        else:
            group_size = int(grouping_pattern[-1])

        if group_size > remaining_channels:
            group_size = 1

        # Determine the range of channels for the current output file
        if group_size == 1:
            group_name = f"{channel_start}"
        else:
            group_name = f"{channel_start}-{channel_start + group_size - 1}"

        # Create the output file name
        base_name, ext = os.path.splitext(input_file)
        output_file = f"{base_name}[{group_name}]{ext}"

        if os.path.exists(output_file):
            existing_files.append(output_file)

        channel_start += group_size
        remaining_channels -= group_size

    return existing_files


def split_channels(sox_command, input_file, grouping_pattern):
    """Split the channels of the input audio file according to a grouping pattern."""
    # Get total number of channels using SoX
    result = subprocess.run(
        [sox_command, '--i', '-c', input_file], capture_output=True, text=True)
    try:
        total_channels = int(result.stdout.strip())
    except ValueError:
        print(f"Error: Unable to determine the number of channels in {input_file}.")
        return

    print(f"Total channels in '{input_file}': {total_channels}")

    # Validate the grouping pattern
    if not validate_grouping_pattern(grouping_pattern, total_channels):
        return

    # Check if any output files already exist
    existing_files = check_files_exist(input_file, grouping_pattern)
    if existing_files:
        print(f"Warning: The following output files already exist:")
        for file in existing_files:
            print(f"  {file}")
        user_input = input("Do you want to continue and overwrite these files? (y/n): ")
        if user_input.lower() != 'y':
            print("Exiting without making changes.")
            return

    channel_start = 1
    remaining_channels = total_channels
    pattern_index = 0

    while remaining_channels > 0:
        # Determine group size based on the pattern
        if pattern_index < len(grouping_pattern):
            group_size = int(grouping_pattern[pattern_index])
            pattern_index += 1
        else:
            # Use the last digit of the pattern for remaining groups
            group_size = int(grouping_pattern[-1])

        # Adjust group size if remaining channels are less
        if group_size > remaining_channels:
            group_size = 1

        # Determine the range of channels for the current output file
        if group_size == 1:
            group_name = f"{channel_start}"
        else:
            group_name = f"{channel_start}-{channel_start + group_size - 1}"

        # Create the output file name
        base_name, ext = os.path.splitext(input_file)
        output_file = f"{base_name}[{group_name}]{ext}"

        # Run SoX to split the channels
        remix_args = [str(i) for i in range(channel_start, channel_start + group_size)]
        subprocess.run(['sox', input_file, output_file, 'remix'] + remix_args)

        print(f"Saved {output_file}")

        # Update the channel start and remaining channels
        channel_start += group_size
        remaining_channels -= group_size


def main():
    sox_command = check_sox_installed()

    if len(sys.argv) < 3:
        print("Usage: python channel-splitter.py <grouping_pattern> <input_file>")
        print("Example: python channel-splitter.py 321 test_20channel.wav")
        return

    grouping_pattern = sys.argv[1]
    if not grouping_pattern.isdigit():
        print("Error: Grouping pattern must consist of digits only.")
        return

    input_files = sys.argv[2:]

    for input_file in input_files:
        if not os.path.isfile(input_file):
            print(f"Error: File '{input_file}' not found.")
            continue

        split_channels(sox_command, input_file, grouping_pattern)


if __name__ == "__main__":
    main()
