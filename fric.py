#!/usr/bin/env python
import sys
import argparse
import io
from itertools import chain
from PIL import Image


#  FRIC (FRamework for Image Corrupting)
#
#  Too lazy to put anything fancy here right now.
#  It's 1:27 am, cut me some slack mang.
#
#
#  0x30797263


##################
#                #
#  Parser setup  #
#                #
##################

parser = argparse.ArgumentParser(
	usage=argparse.SUPPRESS,
	description=" \nFRIC is a highly customizable image glitching framework.\n  Usage: %(prog)s -i normal.raw -o glitched.raw -w 350 -y 114 148",
	epilog="Inspired by Rosa Menkman's \"A Vernacular of File Formats\" study.",
	formatter_class=argparse.RawTextHelpFormatter)

parser._optionals.title = "OPTIONAL ARGUMENTS"
parser.add_argument("-o", action="store", dest="output_file", metavar="string", type=str, help="Filename to save as (default: output.<ext>)")

required = parser.add_argument_group("IMAGE SPECIFICATIONS")
required.add_argument("-i", action="store", dest="input_file", metavar="string", type=str, help="Image to glitch", required=True)
required.add_argument("-y", action="store", dest="offset", metavar=("y1", "y2"), type=int, nargs=2, help="Starting and ending Y-offsets for glitching", required=True)

format_parser = parser.add_argument_group("OUTPUT FORMATS")
format_list = format_parser.add_mutually_exclusive_group()
format_list.add_argument("--int", action="store_const", dest="interleaved", const=1, default=1, help="Save using interleaved channels (default)")
format_list.add_argument("--noint", action="store_const", dest="interleaved", const=0, help="Save using non-interleaved channels")

method_parser = parser.add_argument_group("GLITCHING METHODS")
method_list = method_parser.add_mutually_exclusive_group()
method_list.add_argument("--custom", action="store_const", dest="method", const="custom", default="wordpad", help="Use a custom transform")
method_list.add_argument("--wordpad", action="store_const", dest="method", const="wordpad", help="Use the Wordpad transform (default)")

custom = parser.add_argument_group("CUSTOM CONTROLS")
custom.add_argument("-f", action="store", dest="find", metavar="[bytes]", help="Find these chars (e.g. \\x0a\\x0b\\x0d)")
custom.add_argument("-r", action="store", dest="replace", metavar="[bytes]", help="Convert found chars to this byte sequence")
custom.add_argument("-n", action="store", dest="ignore", metavar="[bytes]", help="Ignore this char sequence (optional)")



args = parser.parse_args()

if args.method == "custom":
	if not args.find or not args.replace:
		parser.error("both -f and -r are required when using --custom")
	args.find = args.find.decode("string_escape")
	args.replace = args.replace.decode("string_escape")


#######################
#                     #
#  Class definitions  #
#                     #
#######################

# Defines an image to be glitched.
class ImageData(object):
	# Initialize the object and read the file.
	def __init__(self):
		# Fetch the image data
		self.img = Image.open(args.input_file)
		self.ext = self.img.format
		self.width = self.img.width
		self.height = self.img.height
		self.datalen = len(self.img.tobytes())
		if args.interleaved:
			self.src_data = self.img.tobytes()
		else:
			self.src_data = [
				str(bytearray(self.img.getdata(0))),
				str(bytearray(self.img.getdata(1))),
				str(bytearray(self.img.getdata(2)))
			]
		self.offset = args.offset
		self.get_glitching_method()

	# List of glitching methods and the chars they modify.
	# More to come soon.
	def get_glitching_method(self):
		if args.method == "custom":
			self.chars_to_replace = []
			for char in args.find:
				self.chars_to_replace.append(char)
			self.chars_to_insert = [args.replace]
			if args.ignore:
				self.chars_to_ignore = [args.ignore]
			else:
				self.chars_to_ignore = []
		if args.method == "wordpad":
			self.chars_to_replace = ["\x0a", "\x0b", "\x0d"]
			self.chars_to_ignore = ["\x0d\x0a"]
			self.chars_to_insert = ["\x0d\x0a"]

	# Determine glitch segment(s) by interleave type.
	def get_section_for_glitching(self, offset):
		offset[0] *= self.width * self.bytes_per_pixel
		offset[1] *= self.width * self.bytes_per_pixel
		self.offset = offset
		# Defer to subclasses.
		self.data_to_glitch = self.get_data_to_glitch()
		return offset

	# Called by subclasses.
	# Counts char instances to determine offsets.
	# Subtracts correctly-formed char sequences from count.
	def adjust_chars_to_glitch(self, data_to_count):
		count = 0
		ignore = 0
		for char in self.chars_to_replace:
			count += data_to_count.count(char)
		for char in self.chars_to_ignore:
			ignore += data_to_count.count(char) * len(char)
		count -= ignore
		return count

	# Called by subclasses.
	# Modifies chars according to the selected method.
	def perform_glitch_method(self, glitched_data):
		for char in self.chars_to_ignore:
			glitched_data = glitched_data.replace(char, "nonExistentString")
		for char in self.chars_to_replace:
			glitched_data = glitched_data.replace(char, "nonExistentString")
		for char in self.chars_to_insert:
			glitched_data = glitched_data.replace("nonExistentString", char)
		return glitched_data

	# Saves the glitched file.
	# Truncates the file if it becomes bigger than the original.
	def save_glitched_file(self):
		self.img = Image.frombytes("RGB", (self.img.width, self.img.height), self.glitched_image)
		if args.output_file:
			output_file = args.output_file
		else:
			output_file = "output.bmp"
			self.ext = "BMP"
		self.img.save(output_file, format=self.ext)
		print "Glitched file saved as %s" % output_file
		exit()

# Defines an image to be saved with interleaved channels.
# Interleaved channels chunk data together in a constant RGB stream.
class Interleaved_Image(ImageData):
	# Since all bytes are clumped together, sequential reading is possible.
	def __init__(self):
		super(Interleaved_Image, self).__init__()
		self.bytes_per_pixel = 3

	# Simply return the data between the offsets.
	def get_data_to_glitch(self):
		offset = self.offset
		return self.src_data[offset[0]:offset[1]]

	# Move up the offset to account for byte displacement.
	def adjust_chars_to_glitch(self, data_to_count):
		count = super(Interleaved_Image, self).adjust_chars_to_glitch(data_to_count)
		self.glitch_offset[1] += count

	# Compile regular and glitched data together.
	def glitch_the_image(self, non_glitched_data):
		glitched_data = self.perform_glitch_method(non_glitched_data)
		dst_data  = self.src_data[0:self.glitch_offset[0]]
		dst_data += glitched_data
		dst_data += self.src_data[self.glitch_offset[1]::]
		return dst_data

# Defines an image to be saved with non-interleaved channels.
# Non-interleaved channels save data in their own separate R, G, and B channels.
class Non_Interleaved_Image(ImageData):
	# Sequential reading not possible due to separated channels.
	def __init__(self):
		super(Non_Interleaved_Image, self).__init__()
		self.bytes_per_pixel = 1

	# Make a list of three separate data blocks.
	def get_data_to_glitch(self):
		offset = self.offset
		data_to_glitch = []
		for channel in range(0, 3):
			data_to_glitch.append(self.src_data[channel][offset[0]:offset[1]])
		return data_to_glitch

	# Account for three different byte displacements, one per channel.
	def adjust_chars_to_glitch(self, data_to_count):
		count = 0
		channel_offset = self.glitch_offset * 3
		self.glitch_offset = []
		for i in range(0, 3):
			count = super(Non_Interleaved_Image, self).adjust_chars_to_glitch(data_to_count[i])
			channel_offset[(i*2)+1] += count
			self.glitch_offset.append(channel_offset[(i*2):(i*2)+2])

	# Stitch the three channels of regular and glitched data together.
	def glitch_the_image(self, non_glitched_data):
		dst_data = ""
		for channel in range(0, 3):
			glitched_data = self.perform_glitch_method(non_glitched_data[channel])
			dst_data += self.src_data[channel][0:self.glitch_offset[channel][0]]
			dst_data += glitched_data
			dst_data += self.src_data[channel][self.glitch_offset[channel][1]::]
		return dst_data


#######################
#                     #
#  Main program code  #
#                     #
#######################

if args.interleaved:
	test = Interleaved_Image()
else:
	test = Non_Interleaved_Image()

test.glitch_offset = test.get_section_for_glitching(test.offset)
test.adjust_chars_to_glitch(test.data_to_glitch)

test.glitched_image = test.glitch_the_image(test.data_to_glitch)
test.save_glitched_file()
