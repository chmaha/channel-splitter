import os
import subprocess
import sys


def check_sox_installed():
    """Check if SoX is installed and accessible."""
    try:
        subprocess.run(['sox', '--version'],
                       capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print("Error: SoX is not installed or not available in the system PATH.")
        sys.exit(1)


def validate_grouping_pattern(grouping_pattern, total_channels):
    """Validate the grouping pattern against the total channel count."""
    if len(grouping_pattern) == 1 and int(grouping_pattern) == total_channels:
        print(f"Error: The grouping pattern '{grouping_pattern}' is the same as the total channel count ({
              total_channels}). No splitting needed.")
        return False

    # Check if the sum of the digits in the grouping pattern exceeds the total channels
    total_pattern = sum(int(digit) for digit in grouping_pattern)
    if total_pattern > total_channels:
        print(f"Error: The sum of the digits in the grouping pattern ({
              total_pattern}) exceeds the number of channels ({total_channels}).")
        return False

    return True


def split_channels(input_file, grouping_pattern):
    """Split the channels of the input audio file according to a grouping pattern."""
    # Get total number of channels using SoX
    result = subprocess.run(
        ['sox', '--i', '-c', input_file], capture_output=True, text=True)
    try:
        total_channels = int(result.stdout.strip())
    except ValueError:
        print(f"Error: Unable to determine the number of channels in {
              input_file}.")
        return

    print(f"Total channels in '{input_file}': {total_channels}")

    # Validate the grouping pattern
    if not validate_grouping_pattern(grouping_pattern, total_channels):
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
        remix_args = [str(i) for i in range(
            channel_start, channel_start + group_size)]
        subprocess.run(['sox', input_file, output_file, 'remix'] + remix_args)

        print(f"Saved {output_file}")

        # Update the channel start and remaining channels
        channel_start += group_size
        remaining_channels -= group_size


def main():
    check_sox_installed()

    if len(sys.argv) < 3:
        print("Usage: python channelsplitter.py <grouping_pattern> <input_file>")
        print("Example: python channelsplitter.py 321 test_20channel.wav")
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

        split_channels(input_file, grouping_pattern)


if __name__ == "__main__":
    main()
