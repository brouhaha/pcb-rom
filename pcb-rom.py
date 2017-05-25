#!/usr/bin/env python3

# Generate inductively-coupled memory PCB
# Copyright 2016, 2017 Eric Smith <spacewar@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the version 3 of the GNU General Public License
# as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import io
import sys

# https://github.com/scott-griffiths/bitstring
from bitstring import Bits

from length import Length, LengthUnit

from Eagle import EagleBoardFile, EaglePackage, EagleDeviceset, EagleDevice, EagleRectangle


def read_data(f, words, bits, stride):
    # We can't read in binary from a text file (e.g., stdin),
    # so if it is a text file, get the underlying binary file
    if isinstance(f, io.TextIOBase):
        f = f.buffer
    data = bytes()
    print(type(data))
    bytes_per_word = (bits + 7) // 8
    if stride is None:
        stride = bytes_per_word
    else:
        assert stride >= bytes_per_word
    for w in range(words):
        w = f.read(bytes_per_word)
        b = Bits(w)
        data += w
        if stride > bytes_per_word:
            f.read(stride - bytes_per_word)
    return data


show_default_units = ['mil', 'mm']


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        help = action.help
        if '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    if action.type == Length:
                        dv = action.default
                        help += ' (default: %.1f mils = %.3f mm)' % (dv.conv('mil'), dv)
                    else:
                        help += ' (default: %(default)s)'
        return help


parser = argparse.ArgumentParser(description='inductively coupled PCB memory generator',
                                 formatter_class=CustomFormatter)

parser.add_argument("-w", "--words",      help = "word count (drive lines)", type = int, default = 64)
parser.add_argument("-b", "--bits",       help = "bit count (sense loops)", type = int, default = 64)
parser.add_argument("--stride",           help = "data input word stride in bytes", type = int, default = None)

parser.add_argument("-u", "--unit",
                    help = "default distance measurement unit",
            	    choices = [str(x) for x in LengthUnit.__members__],
                    default = 'mm')


parser.add_argument("--width",            help = "board width",  type = Length, default = Length('3.9 in'))
parser.add_argument("--length",           help = "board length", type = Length, default = Length('3.9 in'))

parser.add_argument("--drive-layer",       help = "drive layer number", type = int, default = 1)
parser.add_argument("--drive-trace",       help = "drive trace width", type = Length, default = Length('10 mil'))
#parser.add_argument("--drive-space",       help = "drive trace spacing", type = Length, default = Length('10 mil))
parser.add_argument("--drive-pitch",       help = "drive pitch", type = Length, default = Length('50 mil'))

#parser.add_argument("--coupling-length",   help = "drive-to-sense trace coupling length in mils", type = Length, default = Length('40 mil'))

parser.add_argument("--sense-layer",       help = "sense layer number", type = int, default = 16)
parser.add_argument("--sense-trace",       help = "sense trace width", type = Length, default = Length('10 mil'))
#parser.add_argument("--sense-space",       help = "sense trace spacing", type = Length, default = Length('10 mil'))
parser.add_argument("--sense-pitch",       help = "sense pitch", type = Length, default = Length('50 mil'))

parser.add_argument("--pad-drill",         help = "pad drill diameter", type = Length, default = Length('42 mil'))

#parser.add_argument("--ground-layer",      help = "ground plane layer number (0 for none)", type = int, default = 15)

parser.add_argument("-i", "--input",      help="ROM data file", type = argparse.FileType('rb'), default = sys.stdin)
parser.add_argument("-o", "--output",     help="new Eagle board file", type = argparse.FileType('wb'), default = sys.stdout)


args = parser.parse_args()
#print(args)

default_unit = args.unit


drive_space = args.drive_trace
#print("drive space %f %s" % (from_mm(drive_space), default_unit))

array_width = args.words * args.drive_pitch - drive_space
#print("array width %f %s" % (from_mm(array_width), default_unit))

sense_space = (args.sense_pitch - (3 * args.sense_trace)) / 3.0
#print("sense space %f %s" % (from_mm(sense_space), default_unit))

array_height = args.bits * args.sense_pitch - sense_space
#print("array height %f %s" % (from_mm(array_height), default_unit))

#data = read_data(args.input, args.words, args.bits, args.stride)


board = EagleBoardFile()

# XXX add board outline to dimension layer
board.add_rectangular_board_outline(0, 0, args.width, args.length);


y = args.length / 2.0 + (args.words // 2) * args.drive_pitch
word_y = [None] * args.words
for word in range(args.words):
    word_y [word] = [y, y - (args.drive_pitch - (args.drive_trace + drive_space))]
    y -= args.drive_pitch

x = args.width / 2.0 + (args.bits // 2) * args.sense_pitch
bit_x = [None] * (args.bits + 1)
for bit in range(args.bits):
    # entry is [jog, true, comp]
    bit_x [bit] = [x, x - (args.sense_trace + sense_space)]
    x -= args.sense_pitch
bit_x[args.bits] = [x, None, None]

for word in range(args.words):
    name = 'word%03d' % word
    signal = board.add_signal(name)
    if word == 1:
        x = args.bits + 1
        signal.add_wire(5, word_y[word][0], bit_x[bit][0], word_y[word][0])
        signal.add_wire(bit_x[bit][0], word_y[word][0], bit_x[bit][0], word_y[word][1])
        y = 1
        while bit >= 0:
            signal.add_wire(x, word_y[word][0], x, word_y[word][1])
            bit -= 1
        signal.add_wire(bit_x[bit][0], word_y[word][0], 95, word_y[word][0])
    else:
        signal.add_wire(5, word_y[word][0], 95, word_y[word][0], width=args.drive_trace, layer=args.drive_layer)
    if word % 2 == 0:
        signal.add_via(to_mm(100.0), word_y[word][0], drill = args.pad_drill)
        signal.add_via(args.width - to_mm(200.0), word_y[word][0], drill = args.pad_drill)
    else:
        signal.add_via(to_mm(200.0), word_y[word][0] - args.drive_pitch, drill = args.pad_drill)
        signal.add_via(args.width - to_mm(100.0), word_y[word][0] - args.drive_pitch, drill = args.pad_drill)

for bit in range(args.bits):
    signal = board.add_signal('bit%03d' % bit)
    signal.add_wire(bit_x[bit][0], 5, bit_x[bit][0], 95, width=args.sense_trace, layer=args.sense_layer)
    signal.add_wire(bit_x[bit][1], 5, bit_x[bit][1], 95, width=args.sense_trace, layer=args.sense_layer)
    if bit % 2:
        y = 5
    else:
        y = 95
    signal.add_wire(bit_x[bit][0], y, bit_x[bit][1], y, width=args.sense_trace, layer=args.sense_layer)

board.write(args.output)
