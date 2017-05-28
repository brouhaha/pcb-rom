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
import math
import sys

# https://github.com/scott-griffiths/bitstring
from bitstring import BitArray

from length import Length, LengthUnit

from eagle import EagleBoardFile, EaglePackage, EagleDeviceset, EagleDevice, EagleRectangle


def get_bit(data, word_width, word, bit):
    return data[word * word_width + bit]


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

parser.add_argument("-u", "--unit",
                    help = "default distance measurement unit",
            	    choices = [str(x) for x in LengthUnit.__members__],
                    default = 'mm')


parser.add_argument("--width",             help = "board width",  type = Length, default = Length('3.9 in'))
parser.add_argument("--length",            help = "board length", type = Length, default = Length('3.9 in'))

parser.add_argument("--trace-width",       help = "trace width", type = Length, default = Length('8.3 mil'))

parser.add_argument("--drive-layer",       help = "drive layer number", type = int, default = 2)
parser.add_argument("--drive-pitch",       help = "drive pitch", type = Length, default = Length('50 mil'))

#parser.add_argument("--coupling-length",   help = "drive-to-sense trace coupling length in mils", type = Length, default = Length('40 mil'))

parser.add_argument("--sense-layer",       help = "sense layer number", type = int, default = 1)
parser.add_argument("--sense-pitch",       help = "sense pitch", type = Length, default = Length('50 mil'))

parser.add_argument("--pad-drill",         help = "pad drill diameter", type = Length, default = Length('42 mil'))

#parser.add_argument("--ground-layer",      help = "ground plane layer number (0 for none)", type = int, default = 15)

parser.add_argument("input",      help="ROM data file", type = argparse.FileType('rb'))
parser.add_argument("-o", "--output",     help="new Eagle board file", type = argparse.FileType('wb'), default = sys.stdout)


args = parser.parse_args()
#print(args)


w_conv = 'W%%0%dd' % (1 + int(math.floor(math.log10(args.words - 1))))
b_conv = 'B%%0%dd' % (1 + int(math.floor(math.log10(args.bits - 1))))

default_unit = args.unit


drive_space = (args.drive_pitch - (3 * args.trace_width)) / 3.0
#print("drive space %f %s" % (drive_space, default_unit))

array_width = args.words * args.drive_pitch
#print("array width %f %s" % (array_width, default_unit))

sense_space = (args.sense_pitch - (3 * args.trace_width)) / 3.0
#print("sense space %f %s" % (sense_space, default_unit))

array_height = args.bits * args.sense_pitch - sense_space
#print("array height %f %s" % (array_height, default_unit))

data = BitArray(args.input)
if len(data) != args.words * args.bits:
    raise RuntimeError("input file size %d bits, should be %d bits\n" % (len(data), args.words * args.bits))
for i in range(0, len(data), 8):
    data.reverse(i, i+8)


board = EagleBoardFile(numlayers = 4)

board.add_rectangular_board_outline(0, 0, args.width, args.length);


y = args.length / 2.0 - ((args.words // 2) - 0.5) * args.drive_pitch
word_y = [None] * args.words
for word in range(args.words):
    word_y [word] = [y,
                     y - (args.trace_width + drive_space) / 2.0,
                     y + (args.trace_width + drive_space) / 2.0]
    y += args.drive_pitch

x = args.width / 2.0 + ((args.bits // 2) - 0.5) * args.sense_pitch
bit_x = [None] * (args.bits + 1)
for bit in range(args.bits):
    # entry is [jog, true, comp]
    bit_x [bit] = [x,
                   x - (args.sense_pitch - 2.0 * args.trace_width) / 2.0,
                   x + (args.sense_pitch - 2.0 * args.trace_width) / 2.0 ]
    x -= args.sense_pitch
bit_x[args.bits] = [x, None, None]

for word in range(args.words):
    name = w_conv % word
    signal = board.add_signal(name)
    if word % 2:
        cx1 = args.width - Length('100.0 mil')
        cx2 = args.width - Length('200.0 mil')
        cy = word_y[word][0] - args.drive_pitch / 2.0

        lx = cx2 - Length('50.0 mil')
        ly = cy
        ls = name
        la = 'center-right'

        x1 = cx2 - args.drive_pitch
        x2 = bit_x[args.bits - 1][1] - 2.0 * args.trace_width
        x3 = cx2 - 1.5 * args.drive_pitch
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

        lx = cx2 + Length('50.0 mil')
        ly = cy
        ls = name
        la = 'center-left'

        x1 = cx2 + args.drive_pitch
        x2 = bit_x[0][2] + 2.0 * args.trace_width
        x3 = cx2 + 1.5 * args.drive_pitch
        y1 = word_y[word][1]
        y2 = word_y[word][2]

        cx1a = cx1 + args.drive_pitch
        cy1a = cy - args.drive_pitch

        cx2a = x1 - args.drive_pitch / 2.0
        cy2a = cy1a

    signal.add_wire(cx1,  cy,   cx1a, cy1a, layer=args.drive_layer, width=args.trace_width)
    signal.add_wire(cx1a, cy1a, cx2a, cy2a, layer=args.drive_layer, width=args.trace_width)
    signal.add_wire(cx2a, cy2a, x1,   y1,   layer=args.drive_layer, width=args.trace_width)
    signal.add_wire(x1,   y1,   x2,   y1,   layer=args.drive_layer, width=args.trace_width)
    signal.add_wire(x2,   y1,   x2,   y2,   layer=args.drive_layer, width=args.trace_width)

    signal.add_wire(x2,   y2,   x3,   y2,   layer=args.drive_layer, width=args.trace_width)
    signal.add_wire(x3,   y2,   x1,   cy,   layer=args.drive_layer, width=args.trace_width)
    signal.add_wire(x1,   cy,   cx2,  cy,   layer=args.drive_layer, width=args.trace_width)

    signal.add_via(cx1, cy, drill = args.pad_drill)
    signal.add_via(cx2, cy, drill = args.pad_drill)

    board.add_text(ls, lx, ly, size=args.drive_pitch, align=la, layer=21)

board.add_text('+', Length('100.0 mil'), word_y[0][0] - args.drive_pitch, size=args.drive_pitch, align='center', layer=21)
board.add_text('-', Length('200.0 mil'), word_y[0][0] - args.drive_pitch, size=args.drive_pitch, align='center', layer=21)
board.add_text('-', args.width - Length('200.0 mil'), word_y[0][0] - args.drive_pitch, size=args.drive_pitch, align='center', layer=21)
board.add_text('+', args.width - Length('100.0 mil'), word_y[0][0] - args.drive_pitch, size=args.drive_pitch, align='center', layer=21)
board.add_text('+', Length('100.0 mil'), word_y[args.words-1][0] + args.drive_pitch, size=args.drive_pitch, align='center', layer=21)
board.add_text('-', Length('200.0 mil'), word_y[args.words-1][0] + args.drive_pitch, size=args.drive_pitch, align='center', layer=21)
board.add_text('-', args.width - Length('200.0 mil'), word_y[args.words-1][0] + args.drive_pitch, size=args.drive_pitch, align='center', layer=21)
board.add_text('+', args.width - Length('100.0 mil'), word_y[args.words-1][0] + args.drive_pitch, size=args.drive_pitch, align='center', layer=21)

for bit in range(args.bits):
    signal = board.add_signal(b_conv % bit)

    if bit % 2 == 0:
        cx = bit_x[bit][0] - args.drive_pitch / 2.0
        cy1 = Length('100.0 mil')
        cy2 = args.length - Length('200.0 mil')
    else:
        cx = bit_x[bit][0] + args.drive_pitch / 2.0
        cy1 = Length('200.0 mil')
        cy2 = args.length - Length('100.0 mil')

    y1 = word_y[0][1] - 2.0 * args.trace_width
    y2 = word_y[args.words - 1][2] + 2.0 * args.trace_width

    signal.add_via(cx, cy1, drill = args.pad_drill)

    if bit % 2 == 0:
        signal.add_wire(cx, cy1, cx + args.sense_pitch, cy1 + args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(cx + args.sense_pitch, cy1 + args.sense_pitch, cx + args.sense_pitch, cy1 + 3.0 * args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(cx + args.sense_pitch, cy1 + 3.0 * args.sense_pitch, cx + args.sense_pitch / 2.0, cy1 + 3.5 * args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        x = bit_x[bit][0]
        y = word_y[0][1] - 2.0 * args.trace_width
        signal.add_wire(cx + args.sense_pitch / 2.0, cy1 + 3.5 * args.sense_pitch, x, y, width=args.trace_width, layer=args.sense_layer)
    else:
        signal.add_wire(cx, cy1, cx, cy1 + args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(cx, cy1, cx, cy1 + args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(cx, cy1 + args.sense_pitch, cx - args.sense_pitch / 2.0, cy1 + 1.5 * args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        x = bit_x[bit][0]
        y = word_y[0][1] - 2.0 * args.trace_width
        signal.add_wire(cx - args.sense_pitch / 2.0, cy1 + 1.5 * args.sense_pitch, x, y, width=args.trace_width, layer=args.sense_layer)

    for word in range(args.words):
        data_bit = get_bit(data, args.bits, word, bit)
        if data_bit == 0:
            x0 = bit_x[bit][1]
            x1 = bit_x[bit][2]
        else:
            x0 = bit_x[bit][2]
            x1 = bit_x[bit][1]
        new_x = x0
        if x0 != x:
            signal.add_wire(x, y, x0, y, width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(x0, y, x0, word_y[word][1], width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(x0, word_y[word][1], x1, word_y[word][1], width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(x1, word_y[word][1], x1, word_y[word][2], width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(x1, word_y[word][2], x0, word_y[word][2], width=args.trace_width, layer=args.sense_layer)
        x = x0
        y = word_y[word][2] + 2.0 * args.trace_width
        signal.add_wire(x0, word_y[word][2], x, y, width = args.trace_width, layer = args.sense_layer)

    signal.add_wire(x, y, bit_x[bit][0], y, width = args.trace_width, layer=args.sense_layer)

    if bit % 2 == 0:
        signal.add_wire(bit_x[bit][0], y, bit_x[bit][0], cy2 - 1.5 * args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(bit_x[bit][0], cy2 - 1.5 * args.sense_pitch, cx, cy2 - args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(cx, cy2 - args.sense_pitch, cx, cy2, width = args.trace_width, layer=args.sense_layer)
    else:
        signal.add_wire(bit_x[bit][0], y, bit_x[bit][0], cy2 - 3.5 * args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(bit_x[bit][0], cy2 - 3.5 * args.sense_pitch, cx - args.sense_pitch, cy2 - 3.0 * args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(cx - args.sense_pitch, cy2 - 3.0 * args.sense_pitch, cx - args.sense_pitch, cy2 - args.sense_pitch, width=args.trace_width, layer=args.sense_layer)
        signal.add_wire(cx - args.sense_pitch, cy2 - args.sense_pitch, cx, cy2, width=args.trace_width, layer=args.sense_layer)
    
    signal.add_via(cx, cy2, drill = args.pad_drill)


board.add_text(b_conv % 0, bit_x[0][0] + args.sense_pitch, Length('100.0 mil'), size=args.drive_pitch, align='center-left', layer=21)
board.add_text(b_conv % (args.bits - 1), bit_x[args.bits - 1][0] - args.sense_pitch, Length('200.0 mil'), size=args.drive_pitch, align='center-right', layer=21)
board.add_text(b_conv % 0, bit_x[0][0] + args.sense_pitch, args.length - Length('200.0 mil'), size=args.drive_pitch, align='center-left', layer=21)
board.add_text(b_conv % (args.bits - 1), bit_x[args.bits - 1][0] - args.sense_pitch, args.length - Length('100.0 mil'), size=args.drive_pitch, align='center-right', layer=21)

board.write(args.output)
