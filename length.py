#!/usr/bin/env python3

# Subclass of float for length measurements
# Copyright 2017 Eric Smith <spacewar@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the version 3 of the GNU General Public License
# as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from enum import Enum
import numbers

LengthUnit = Enum('LengthUnit', names = (('inch',     25.4),
                                         ('mil',       0.0254),
                                         ('mm',        1.0),
                                         ('cm',       10.0),
                                         ('m',      1000.0),
                                         ('inches',   25.4),
                                         ('in',       25.4),
                                         ('mils',      0.0254)))

class Length(float):
    def __new__(cls, val, default_unit = 'mm'):
        if isinstance(val, numbers.Number):
            return super().__new__(cls, val)
        if not isinstance(val, str):
            raise TypeError()
        for un in LengthUnit.__members__:
            if val.endswith(un):
                return super().__new__(cls, float(val[:-len(un)].strip()) * LengthUnit[un].value)
        else:
            return float(val) * LengthUnit[default_unit].value

    def conv(self, unit):
        return self / LengthUnit[unit].value


if __name__ == '__main__':
    for s in ['22',
              '2.3in',
              '2.3 inches',
              '7mm',
              '0.1 m',
              '37ug']:
        print(s, Length(s))
