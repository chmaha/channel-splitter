#!/bin/sh

# Splits one or more input files by the integer pattern made up of single digits.
# e.g. 32 splits the file into a 3-channel file, followed by as many stereo files as possible.
# Mono files are created for any remaining channels.
# 
# Supports wav, flac, aiff and wavpack input.
# Output naming adds an identifying suffix.
# For example, output[3-4].wav is a file containing channels 3 and 4. 
#
# Further examples: 
# channelsplitter.sh 2 *.wav 
# - creates a series of stereo files followed by a mono remainder if needed.
# 
# channelsplitter.sh 221 *.flac 
# - creates two stereo files followed by a series of mono files.

# Function to check if SoX is installed
check_sox_installed() {
  if command -v sox > /dev/null 2>&1; then
    return 0
  else
    echo "SoX is not installed."
    return 1
  fi
}

check_sox_installed || exit 1  # Exit if SoX is not found

# Function to handle the splitting logic
split_channels() {
    input_file="$1"
    grouping_pattern="$2"
    total_channels=$(sox --i -c "$input_file")  # Get the number of channels in the input file

    # Check if total_channels is a valid number
    echo "$total_channels" | grep -qE '^[0-9]+$' || {
        echo "Error: Unable to determine the number of channels in $input_file."
        exit 1
    }

    echo "Total channels in '$input_file': $total_channels"

    # Check if the grouping pattern is a single digit that equals the total channel count
    if [ ${#grouping_pattern} -eq 1 ] && [ "$grouping_pattern" -eq "$total_channels" ]; then
        echo "Error: The grouping pattern '$grouping_pattern' is the same as the channel count ($total_channels). No splitting needed."
        exit 1
    fi

    # Check if the sum of the digits in the grouping pattern exceeds the channel count
    sum=0
    len=${#grouping_pattern}
    i=0
    while [ $i -lt $len ]; do
        sum=$((sum + ${grouping_pattern:i:1}))
        i=$((i + 1))
    done

    if [ "$sum" -gt "$total_channels" ]; then
        echo "Error: The sum of the digits in the grouping pattern ($sum) exceeds the number of channels ($total_channels)."
        exit 1
    fi

    # Initialize channel_start and pattern_index
    channel_start=1
    pattern_index=0

    # Initialize a flag for checking if any files exist
    files_exist=false

    # Check for existing files before splitting
    while [ "$channel_start" -le "$total_channels" ]; do
        group_size=$(echo "$grouping_pattern" | cut -c $((pattern_index + 1)))

        # Ensure group_size is a valid integer
        if ! echo "$group_size" | grep -qE '^[0-9]+$'; then
            echo "Error: Invalid group_size '$group_size'. It must be a valid number."
            exit 1
        fi

        pattern_index=$((pattern_index + 1))

        if [ "$pattern_index" -ge "$len" ]; then
            pattern_index=$((len - 1))
        fi

        if [ "$group_size" -eq 1 ]; then
            group_name="$channel_start"
            output_file="${input_file%.*}[$group_name].${input_file##*.}"
        elif [ "$group_size" -ge 2 ] && [ $((total_channels - channel_start + 1)) -ge "$group_size" ]; then
            group_name=$(seq -s'-' "$channel_start" $((channel_start + group_size - 1)))
            output_file="${input_file%.*}[$group_name].${input_file##*.}"
        else
            group_name="$channel_start"
            output_file="${input_file%.*}[$group_name].${input_file##*.}"
        fi

        # Check if the output file already exists
        if [ -f "$output_file" ]; then
            files_exist=true
        fi

        channel_start=$((channel_start + group_size))
    done

    # If any files exist, ask for confirmation to overwrite
    if $files_exist; then
        echo "Some output files already exist. Do you want to overwrite them? (y/n): "
        read answer
        if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
            echo "Operation cancelled."
            exit 1
        fi
    fi

    # Reset channel_start and pattern_index for actual file splitting
    channel_start=1
    pattern_index=0

    # Split the channels
    while [ "$channel_start" -le "$total_channels" ]; do
        group_size=$(echo "$grouping_pattern" | cut -c $((pattern_index + 1)))

        # Ensure group_size is a valid integer
        if ! echo "$group_size" | grep -qE '^[0-9]+$'; then
            echo "Error: Invalid group_size '$group_size'. It must be a valid number."
            exit 1
        fi

        pattern_index=$((pattern_index + 1))

        if [ "$pattern_index" -ge "$len" ]; then
            pattern_index=$((len - 1))
        fi

        if [ "$group_size" -eq 1 ]; then
            group_name="$channel_start"
            output_file="${input_file%.*}[$group_name].${input_file##*.}"
            sox "$input_file" "$output_file" remix "$channel_start"
            echo "Saved $output_file"
            channel_start=$((channel_start + 1))
        elif [ "$group_size" -ge 2 ] && [ $((total_channels - channel_start + 1)) -ge "$group_size" ]; then
            group_name=$(seq -s'-' "$channel_start" $((channel_start + group_size - 1)))
            output_file="${input_file%.*}[$group_name].${input_file##*.}"
            sox "$input_file" "$output_file" remix $(seq $channel_start $((channel_start + group_size - 1)))
            echo "Saved $output_file"
            channel_start=$((channel_start + group_size))
        else
            while [ "$channel_start" -le "$total_channels" ]; do
                group_name="$channel_start"
                output_file="${input_file%.*}[$group_name].${input_file##*.}"
                sox "$input_file" "$output_file" remix "$channel_start"
                echo "Saved $output_file"
                channel_start=$((channel_start + 1))
            done
        fi
    done
}

# Main script
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <grouping_pattern> <input_file(s)>"
    echo "Example: For a 6-channel input, '$0 32 input.wav' will create input[1-2-3].wav, input[4-5].wav, input[6].wav"
    exit 1
fi

grouping_pattern="$1"
shift

# Loop over all files passed as arguments
for input_file in "$@"; do
    if [ ! -f "$input_file" ]; then
        echo "Error: File '$input_file' not found."
        continue
    fi

    # Check if the input file has a supported extension (wav, flac, aiff, wv)
    case "$input_file" in
        *.wav|*.flac|*.wv|*.aiff) ;;
        *)
            echo "Error: '$input_file' is not a supported audio file. Supported formats are .wav, .flac, .wv, and .aiff."
            continue
            ;;
    esac

    split_channels "$input_file" "$grouping_pattern"
done
