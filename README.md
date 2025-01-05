# Batch Audio Channel Splitter

#### Requirements: SoX

Split any number of audio files (wav, flac, aiff or wv) into smaller channel groups via a numeric pattern made up of single digits.

Users can choose between a python script (all OSes) or POSIX shell script (Linux/MacOS).

### Example 1

```sh
channelsplitter.sh 2 input.wav
```
creates a series of stereo wav files with any remainder as mono
e.g. 
```
input[1-2].wav
input[3-4].wav
```
### Example 2

```sh
python channelsplitter.py 221 *.aiff
```
creates two initial stereo files followed by a series of mono files all in aiff format.
e.g.
```
mozart[1-2].aiff
mozart[3-4].aiff
mozart[5].aiff
mozart[6].aiff
```
### Example 3

```sh
channelsplitter.sh 312 *.wv
```
creates a 3-channel file, followed by a mono file, followed by a series of stereo files with mono remainders as required (all in wavpack format).
e.g.
```
bach_violin_sontata[1-2-3].wv
bach_violin_sontata[4].wv
bach_violin_sontata[5-6].wv
bach_violin_sontata[7-8].wv
bach_violin_sontata[9-10].wv
bach_violin_sontata[11].wv
```

Essentially, if the individual digits of the pattern add up to less than the initial channel count, it will reuse the final digit as much as it can until it needs to create mono remainders. It also checks if files already exist as well as showing messages if the summed digits of the pattern exceed the input channel count or if there is an attempt at a needless split (i.e. using a pattern of 2 for stereo file).
