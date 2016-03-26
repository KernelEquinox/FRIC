# FRamework for Image Corruption (and glitching)
An extremely customizable and granular image corrupting and glitching framework, or at least it will be in time.

This started out as a script to automate some image glitching stuff, then evolved into a framework idea, then evolved into my first program using object-oriented programming. It's nothing great right now, but I totally plan to work on it.

## Usage
The required parameters are the image file, the image's width, and the Y-offset range for glitching. Optional parameters include the output file name, the channel interleaving, and the glitching method.

The input image must be a 24-bit RAW image with interleaved channels. The output image is a 24-bit RAW image with either interleaved or non-interleaved channels, depending on the arguments.

## Example
These arguments would take a 350-pixel wide image and glitch the section between Y-offsets 114 and 148 and output the image with non-interleaved channels:
```
FRIC.py -i normal.raw -o glitched.raw -w 350 -y 114 148 --wordpad --noint
```

## To-Do
- Add more glitching methods.
- Add custom glitching method parameters and functionality.
- Add non-interleaved image processing functionality.
- Allow for multiple offset pair specifications.
- Clean up and refactor code.
