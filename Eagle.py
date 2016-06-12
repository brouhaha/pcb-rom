#!/usr/bin/env python3

# Write Eagle CAD files
# Copyright 2016 Eric Smith <spacewar@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the version 3 of the GNU General Public License
# as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from abc import ABCMeta
import io
from xml.etree.ElementTree import ElementTree, Element, SubElement, Comment, tostring

class EagleXMLElement:
    def __init__(self, name, attrs = None, from_element = None):
        if from_element is None:
            if attrs is None:
                self.element = Element(name)
            else:
                self.element = Element(name, attrs)
        else:
            self.element = from_element
        self.primitives = []

    def get_element(self):
        return self.element

    def add_subelement(self, subelement):
        self.element.append(subelement)

    def add_primitive(self, primitive):
        self.primitives.append(primitive)
        self.add_subelement(primitive.get_element())
        return primitive


class EagleSetting(EagleXMLElement):
    def __init__(self, name, value):
        super().__init__('setting', {name: value})


class EagleSettings(EagleXMLElement):
    def __init__(self):
        super().__init__('settings')
        self.settings = []
        self.settings.append(EagleSetting ('alwaysvectorfont', 'no'))
        self.settings.append(EagleSetting ('verticaltext', 'up'))
        for setting in self.settings:
            self.element.append(setting.get_element())
        

class EagleGrid(EagleXMLElement):
    def __init__(self):
        super().__init__('grid', { 'distance': '0.1',
                                   'unitdist': 'inch',
                                   'unit': 'inch',
                                   'style': 'lines',
                                   'multiple': '1',
                                   'display': 'no',
                                   'altdistance': '0.01',
                                   'altunitdist': 'inch',
                                   'altunit': 'inch' })


def eagle_boolean(b):
    if b:
        return 'yes'
    else:
        return 'no'
    
class EagleLayer(EagleXMLElement):
    def __init__(self, number, name, color, fill, visible, active):
        super().__init__('layer', { 'number':  str(number),
                                    'name':    name,
                                    'color':   str(color),
                                    'fill':    str(fill),
                                    'visible': eagle_boolean(visible),
                                    'active':  eagle_boolean(active) })
        self.number = number
        self.name = name



class EagleLayers(EagleXMLElement):
    def __init__(self):
        super().__init__('layers')

        self.layers_by_name = { }
        self.layers_by_number = { }

        for layer in [ EagleLayer(1,  'Top',       4,  1,  True,   True),
                       EagleLayer(2,  'Route2',    1,  3,  False,  True),
                       EagleLayer(3,  'Route3',    4,  3,  False,  True),
                       EagleLayer(4,  'Route4',    1,  4,  False,  True),
                       EagleLayer(5,  'Route5',    4,  4,  False,  True),
                       EagleLayer(6,  'Route6',    1,  8,  False,  True),
                       EagleLayer(7,  'Route7',    4,  8,  False,  True),
                       EagleLayer(8,  'Route8',    1,  2,  False,  True),
                       EagleLayer(9,  'Route9',    4,  2,  False,  True),
                       EagleLayer(10, 'Route10',   1,  7,  False,  True),
                       EagleLayer(11, 'Route11',   4,  7,  False,  True),
                       EagleLayer(12, 'Route12',   1,  5,  False,  True),
                       EagleLayer(13, 'Route13',   4,  5,  False,  True),
                       EagleLayer(14, 'Route14',   1,  6,  False,  True),
                       EagleLayer(15, 'Route15',   4,  6,  False,  True),
                       EagleLayer(16, 'Bottom',    1,  1,  True,   True),
                       EagleLayer(17, 'Pads',      2,  1,  True,   True),
                       EagleLayer(18, 'Vias',      2,  1,  True,   True),
                       EagleLayer(19, 'Unrouted',  6,  1,  True,   True),
                       EagleLayer(20, 'Dimension', 15, 1,  True,   True),
	               EagleLayer(21, 'tPlace',    7,  1,  True,   True),
                       EagleLayer(22, 'bPlace',    7,  1,  True,   True),
                       EagleLayer(23, 'tOrigins',  15, 1,  True,   True),
                       EagleLayer(24, 'bOrigins',  15, 1,  True,   True),
                       EagleLayer(25, 'tNames',    7,  1,  True,   True),
                       EagleLayer(26, 'bNames',    7,  1,  True,   True),
                       EagleLayer(27, 'tValues',   7,  1,  True,   True),
                       EagleLayer(28, 'bValues',   7,  1,  True,   True),
                       EagleLayer(29, 'tStop',     7,  3,  False,  True),
                       EagleLayer(30, 'bStop',     7,  6,  False,  True),
                       EagleLayer(31, 'tCream',    7,  4,  False,  True),
                       EagleLayer(32, 'bCream',    7,  5,  False,  True),
                       EagleLayer(33, 'tFinish',   6,  3,  False,  True),
                       EagleLayer(34, 'bFinish',   6,  6,  False,  True),
                       EagleLayer(35, 'tGlue',     7,  4,  False,  True),
                       EagleLayer(36, 'bGlue',     7,  5,  False,  True),
                       EagleLayer(37, 'tTest',     7,  1,  False,  True),
                       EagleLayer(38, 'bTest',     7,  1,  False,  True),
                       EagleLayer(39, 'tKeepout',  4,  11, True,   True),
                       EagleLayer(40, 'bKeepout',  1,  11, True,   True),
                       EagleLayer(41, 'tRestrict', 4,  10, True,   True),
                       EagleLayer(42, 'bRestrict', 1,  10, True,   True),
                       EagleLayer(43, 'vRestrict', 2,  10, True,   True),
                       EagleLayer(44, 'Drills',    7,  1,  False,  True),
                       EagleLayer(45, 'Holes',     7,  1,  False,  True),
                       EagleLayer(46, 'Milling',   3,  1,  False,  True),
                       EagleLayer(47, 'Measures',  7,  1,  False,  True),
                       EagleLayer(48, 'Document',  7,  1,  True,   True),
                       EagleLayer(49, 'Reference', 7,  1,  True,   True),
                       EagleLayer(51, 'tDocu',     7,  1,  True,   True),
                       EagleLayer(52, 'bDocu',     7,  1,  True,   True),
                       EagleLayer(91, 'Nets',      2,  1,  True,   True),
                       EagleLayer(92, 'Busses',    1,  1,  True,   True),
                       EagleLayer(93, 'Pins',      2,  1,  False,  True),
                       EagleLayer(94, 'Symbols',   4,  1,  True,   True),
                       EagleLayer(95, 'Names',     7,  1,  True,   True),
                       EagleLayer(96, 'Values',    7,  1,  True,   True),
                       EagleLayer(97, 'Info',      7,  1,  True,   True),
                       EagleLayer(98, 'Guide',     6,  1,  True,   True) ]:
            self.layers_by_name [layer.name] = layer
            self.layers_by_number [layer.number] = layer
            self.add_subelement(layer.element)



class EagleFile(metaclass = ABCMeta):
    def __init__(self):
        self.eagle = Element('eagle', { 'version': '6.5.0' })
        self.drawing = SubElement(self.eagle, 'drawing')

        self.settings = EagleSettings()
        self.drawing.append(self.settings.get_element())

        self.grid = EagleGrid()
        self.drawing.append(self.grid.get_element())

        self.layers = EagleLayers()
        self.drawing.append(self.layers.get_element())

    # Eagle's XML reader doesn't like extremely long lines, and xml.etree.ElementTree
    # doesn't have built-in support for pretty printing, so this function can be used
    # to add suitable 'tails' to each element for newlines and indentation.  (Eagle
    # doesn't need the indentation, but it makes it easier to inspect the library as
    # text.)
    #   http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    def _indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
        

    def write(self, outfile):
        # We can't write XML to a text file (e.g., stdout),
        # so if it is a text file, get the underlying binary file
        if isinstance(outfile, io.TextIOBase):
            outfile = outfile.buffer

        self._indent(self.eagle)
        doc = ElementTree(self.eagle)
        doc.write(outfile, encoding='utf-8', xml_declaration=True)



class EaglePrimitive(EagleXMLElement):
    def __init__(self, kind, attrs):
        super().__init__(kind, attrs)


class EagleRectangle(EaglePrimitive):
    def __init__(self, layer, x1, y1, x2, y2):
        super().__init__('rectangle', { 'layer': str(layer),
                                        'x1': '%.6f' % x1,
                                        'y1': '%.6f' % y1,
                                        'x2': '%.6f' % x2,
                                        'y2': '%.6f' % y2 })


class EaglePackage(EagleXMLElement):
    def __init__(self, name):
        super().__init__('package', {'name': name })
        self.name = name


class EaglePackages(EagleXMLElement):
    def __init__(self):
        super().__init__('packages')
        self.packages = {}

    def add_package(self, package):
        self.packages [package.name] = package
        self.add_subelement(package.get_element())


class EagleSymbols(EagleXMLElement):
    def __init__(self):
        super().__init__('symbols')


class EagleTechnology(EagleXMLElement):
    def __init__(self, name):
        super().__init__('technology', { 'name': name })


class EagleTechnologies(EagleXMLElement):
    def __init__(self):
        super().__init__('technologies')
        self.technologies = { '': EagleTechnology('') }
        self.add_subelement(self.technologies[''].get_element())


class EagleDevice(EagleXMLElement):
    def __init__(self, name, package):
        super().__init__('device', { 'name': name,
                                     'package': package })
        self.technologies = EagleTechnologies()
        self.add_subelement(self.technologies.get_element())


class EagleGates(EagleXMLElement):
    def __init__(self):
        super().__init__('gates')


class EagleDevices(EagleXMLElement):
    def __init__(self):
        super().__init__('devices')
        self.devices = []

    def add_device(self, device):
        self.devices.append(device)
        self.add_subelement(device.get_element())


class EagleDeviceset(EagleXMLElement):
    def __init__(self, name):
        super().__init__('deviceset', { 'name': name })
        self.gates = EagleGates()
        self.add_subelement(self.gates.get_element())
        self.devices = EagleDevices()
        self.add_subelement(self.devices.get_element())

    def add_device(self, device):
        self.devices.add_device(device)


class EagleDevicesets(EagleXMLElement):
    def __init__(self):
        super().__init__('devicesets')
        self.devicesets = []

    def add_deviceset(self, deviceset):
        self.devicesets.append(deviceset)
        self.add_subelement(deviceset.get_element())


class EagleLibrary(EagleXMLElement):
    def __init__(self):
        super().__init__('library')
        self.packages = EaglePackages()
        self.add_subelement(self.packages.get_element())
        self.symbols = EagleSymbols()
        self.add_subelement(self.symbols.get_element())
        self.devicesets = EagleDevicesets()
        self.add_subelement(self.devicesets.get_element())

    def add_deviceset(self, deviceset):
        self.devicesets.add_deviceset(deviceset)

    def add_package(self, package):
        self.packages.add_package(package)


class EaglePlain(EagleXMLElement):
    def __init__(self):
        super().__init__('plain')

class EagleLibraries(EagleXMLElement):
    def __init__(self):
        super().__init__('libraries')

class EagleAttributes(EagleXMLElement):
    def __init__(self):
        super().__init__('attributes')

class EagleVariantdefs(EagleXMLElement):
    def __init__(self):
        super().__init__('variantdefs')

class EagleClasses(EagleXMLElement):
    def __init__(self):
        super().__init__('classes')

class EagleDesignrules(EagleXMLElement):
    def __init__(self):
        super().__init__('designrules')

class EagleAutorouter(EagleXMLElement):
    def __init__(self):
        super().__init__('autorouter')

class EagleElements(EagleXMLElement):
    def __init__(self):
        super().__init__('elements')


class EagleSignal(EaglePrimitive):
    def __init__(self, name):
        super().__init__('signal', { 'name' : name })

    def add_wire(self, x1, y1, x2, y2, layer, width):
        self.add_primitive(EagleWire(x1, y1, x2, y2, layer, width))

    def add_via(self, x, y, drill, diameter = None, extent = (1, 16), shape = None):
        self.add_primitive(EagleVia(x, y, drill, diameter, extent, shape))


class EagleSignals(EagleXMLElement):
    def __init__(self):
        super().__init__('signals')

    def add_signal(self, name):
        return self.add_primitive(EagleSignal(name))


class EagleWire(EaglePrimitive):
    def __init__(self, x1, y1, x2, y2, layer, width):
        super().__init__('wire', { 'layer': str(layer),
                                   'width': '%.6f' % width,
                                   'x1': '%.6f' % x1,
                                   'y1': '%.6f' % y1,
                                   'x2': '%.6f' % x2,
                                   'y2': '%.6f' % y2 })


class EagleVia(EaglePrimitive):
    def __init__(self, x, y, drill,
                 diameter = None, # None for automatic
                 extent = (1, 16),
                 shape = None): # None for round
        d = { 'x': '%.6f' % x,
              'y': '%.6f' % y,
              'drill': '%.6f' % drill,
              'extent': '%d-%d' % (extent[0], extent[1]) }
        if diameter is not None:
            d['diameter'] = '%.6f' % diameter
        if shape is not None:
            d['shape'] = shape
        super().__init__('via', d)


class EagleBoard(EagleXMLElement):
    def __init__(self):
        super().__init__('board')
        self.plain = EaglePlain()
        self.add_subelement(self.plain.get_element())
        self.libraries = EagleLibraries()
        self.add_subelement(self.libraries.get_element())
        self.attributes = EagleAttributes()
        self.add_subelement(self.attributes.get_element())
        self.variantdefs = EagleVariantdefs()
        self.add_subelement(self.variantdefs.get_element())
        self.classes = EagleClasses()
        self.add_subelement(self.classes.get_element())
        self.designrules = EagleDesignrules()
        self.add_subelement(self.designrules.get_element())
        self.autorouter = EagleAutorouter()
        self.add_subelement(self.autorouter.get_element())
        self.elements = EagleElements()
        self.add_subelement(self.elements.get_element())
        self.signals = EagleSignals()
        self.add_subelement(self.signals.get_element())

    def add_rectangular_board_outline(self, x1, y1, x2, y2):
        self.plain.add_primitive(EagleWire(x1 = x1, y1 = y1,
                                           x2 = x1, y2 = y2,
                                           layer = 20, width = 0))
        self.plain.add_primitive(EagleWire(x1 = x1, y1 = y2,
                                           x2 = x2, y2 = y2,
                                           layer = 20, width = 0))
        self.plain.add_primitive(EagleWire(x1 = x2, y1 = y2,
                                           x2 = x2, y2 = y1,
                                           layer = 20, width = 0))
        self.plain.add_primitive(EagleWire(x1 = x2, y1 = y1,
                                           x2 = x1, y2 = y1,
                                           layer = 20, width = 0))

    def add_signal(self, name):
        return self.signals.add_signal(name)


class EagleLibraryFile(EagleFile):
    def __init__(self):
        super().__init__()
        self.library = EagleLibrary()
        self.drawing.append(self.library.get_element())

    def add_deviceset(self, deviceset):
        self.library.add_deviceset(deviceset)

    def add_package(self, package):
        self.library.add_package(package)


class EagleBoardFile(EagleFile):
    def __init__(self):
        super().__init__()
        self.board = EagleBoard()
        self.drawing.append(self.board.get_element())

    def add_rectangular_board_outline(self, x1, y1, x2, y2):
        self.board.add_rectangular_board_outline(x1, y1, x2, y2)

    def add_signal(self, name):
        return self.board.add_signal(name)

'''
class EagleSchematic(EagleFile):
    def __init__(self):
        super().__init__()
'''


if __name__ == '__main__':
    lib = EagleLibraryFile()

    print(lib)
    print(lib.library)
    print(lib.library.devicesets)

    package_name = 'PKG'
    deviceset_name = 'DEV'

    package = EaglePackage(package_name)
    package.add_primitive(EagleRectangle(21, 18.2448, 4.6690, 19.6850, 4.7836))
    package.add_primitive(EagleRectangle(21, 17.7368, 4.7836, 20.1930, 4.8684))

    lib.add_package(package)

    deviceset = EagleDeviceset(deviceset_name)
    device = EagleDevice('', package_name)
    deviceset.add_device(device)
    
    lib.add_deviceset(deviceset)

    lib.write('test.lbr')

    brd = EagleBoardFile()
    brd.board.add_rectangular_board_outline(0, 0, 100, 100);

    brd.write('test.brd')
