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
    __slots__ = ('unit')  # or could use ('__dict__')

    def __new__(cls, val, unit = 'mm'):
        if isinstance(val, numbers.Number):
            self = super().__new__(cls, float(val))
            self.unit = LengthUnit[unit]
            return self
        if not isinstance(val, str):
            raise TypeError()
        for un in LengthUnit.__members__:
            if val.endswith(un):
                self = super().__new__(cls, float(val[:-len(un)].strip()) * LengthUnit[un].value)
                self.unit = LengthUnit[un]
                return self
        else:
            self = super().__new__(cls, float(val) * LengthUnit[unit].value)
            self.unit = LengthUnit[unit]
            return self

    def conv(self, unit):
        return self / LengthUnit[unit].value

    def __str__(self):
        return str(self.conv(self.unit.name)) + ' ' + self.unit.name


if __name__ == '__main__':
    for s in ['22',
              '2.3in',
              '2.3 inches',
              '7mm',
              '0.1 m',
              '37ug']:
        print(s, Length(s))
