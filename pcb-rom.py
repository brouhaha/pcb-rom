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

from eagle import EagleBoardFile, EaglePackage, EagleDeviceset, EagleDevice, EagleRectangle


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

parser.add_argument("--drive-layer",       help = "drive layer number", type = int, default = 16)
parser.add_argument("--drive-width",       help = "drive trace width", type = Length, default = Length('12.5 mil'))
parser.add_argument("--drive-pitch",       help = "drive pitch", type = Length, default = Length('50 mil'))

#parser.add_argument("--coupling-length",   help = "drive-to-sense trace coupling length in mils", type = Length, default = Length('40 mil'))

parser.add_argument("--sense-layer",       help = "sense layer number", type = int, default = 1)
parser.add_argument("--sense-width",       help = "sense trace width", type = Length, default = Length('8.5 mil'))
parser.add_argument("--sense-pitch",       help = "sense pitch", type = Length, default = Length('50 mil'))

parser.add_argument("--pad-drill",         help = "pad drill diameter", type = Length, default = Length('42 mil'))

#parser.add_argument("--ground-layer",      help = "ground plane layer number (0 for none)", type = int, default = 15)

parser.add_argument("-i", "--input",      help="ROM data file", type = argparse.FileType('rb'), default = sys.stdin)
parser.add_argument("-o", "--output",     help="new Eagle board file", type = argparse.FileType('wb'), default = sys.stdout)


args = parser.parse_args()
#print(args)

default_unit = args.unit


drive_space = (args.drive_pitch - (2 * args.drive_width)) / 2.0
#print("drive space %f %s" % (drive_space, default_unit))

array_width = args.words * args.drive_pitch
#print("array width %f %s" % (array_width, default_unit))

sense_space = (args.sense_pitch - (3 * args.sense_width)) / 3.0
#print("sense space %f %s" % (sense_space, default_unit))

array_height = args.bits * args.sense_pitch - sense_space
#print("array height %f %s" % (array_height, default_unit))

#data = read_data(args.input, args.words, args.bits, args.stride)


board = EagleBoardFile()

# XXX add board outline to dimension layer
board.add_rectangular_board_outline(0, 0, args.width, args.length);


y = args.length / 2.0 - ((args.words // 2) - 0.5) * args.drive_pitch
word_y = [None] * args.words
for word in range(args.words):
    word_y [word] = [y,
                     y - (args.drive_width + drive_space) / 2.0,
                     y + (args.drive_width + drive_space) / 2.0]
    y += args.drive_pitch

x = args.width / 2.0 + (args.bits // 2) * args.sense_pitch
bit_x = [None] * (args.bits + 1)
for bit in range(args.bits):
    # entry is [jog, true, comp]
    bit_x [bit] = [x, x - (args.sense_width + sense_space)]
    x -= args.sense_pitch
bit_x[args.bits] = [x, None, None]

for word in range(args.words):
    name = 'W%03d' % word
    signal = board.add_signal(name)
    if word % 2:
        cx1 = args.width - Length('100.0 mil')
        cx2 = args.width - Length('200.0 mil')
        cy = word_y[word][0] - args.drive_pitch / 2.0

        lx = cx2 - Length('100.0 mil')
        ly = cy
        ls = name
        la = 'center-right'

        x1 = cx2 - args.drive_pitch
        x2 = bit_x[args.bits][0]
        y1 = word_y[word][2]
        y2 = word_y[word][1]

        cx1a = cx1 - args.drive_pitch
        cy1a = cy + args.drive_pitch

        cx2a = x1 + args.drive_pitch / 2.0
        cy2a = cy1a
    else:
        cx1 = Length('100.0 mil')
        cx2 = Length('200.0 mil')
        cy = word_y[word][0] + args.drive_pitch / 2.0

        lx = cx2 + Length('100.0 mil')
        ly = cy
        ls = name
        la = 'center-left'

        x1 = cx2 + args.drive_pitch
        x2 = bit_x[0][0]
        y1 = word_y[word][1]
        y2 = word_y[word][2]

        cx1a = cx1 + args.drive_pitch
        cy1a = cy - args.drive_pitch

        cx2a = x1 - args.drive_pitch / 2.0
        cy2a = cy1a

    signal.add_wire(cx1,  cy,   cx1a, cy1a, layer=args.drive_layer, width=args.drive_width)
    signal.add_wire(cx1a, cy1a, cx2a, cy2a, layer=args.drive_layer, width=args.drive_width)
    signal.add_wire(cx2a, cy2a, x1,   y1,   layer=args.drive_layer, width=args.drive_width)
    signal.add_wire(x1,   y1,   x2,   y1,   layer=args.drive_layer, width=args.drive_width)
    signal.add_wire(x2,   y1,   x2,   y2,   layer=args.drive_layer, width=args.drive_width)
    signal.add_wire(x2,   y2,   x1,   y2,   layer=args.drive_layer, width=args.drive_width)
    signal.add_wire(x1,   y2,   cx2,  cy,   layer=args.drive_layer, width=args.drive_width)

    signal.add_via(cx1, cy, drill = args.pad_drill)
    signal.add_via(cx2, cy, drill = args.pad_drill)

    board.add_text(ls, lx, ly, size=args.drive_pitch, align=la, layer=21)

if False:
  for bit in range(args.bits):
    signal = board.add_signal('bit%03d' % bit)
    signal.add_wire(bit_x[bit][0], 5, bit_x[bit][0], 95, width=args.sense_width, layer=args.sense_layer)
    signal.add_wire(bit_x[bit][1], 5, bit_x[bit][1], 95, width=args.sense_width, layer=args.sense_layer)
    if bit % 2:
        y = 5
    else:
        y = 95
    signal.add_wire(bit_x[bit][0], y, bit_x[bit][1], y, width=args.sense_width, layer=args.sense_layer)

board.write(args.output)
