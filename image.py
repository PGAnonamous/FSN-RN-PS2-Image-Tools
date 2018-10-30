import os, sys, argparse
from fnmatch import filter
from struct import *
from typing import BinaryIO
from pathlib import Path
from collections import namedtuple

image_format = '<4xI4xI'
rnimage_format = '<8x6I'
iif_format = '<4s3I'
iif_magic = b'\x49\x49\x46\x31'
clutDepths = { 0x13 : 3, 0x14 : 5 , 3 : 0x13, 5 : 0x14}
realBitDepths = { 0x13 : 0, 0x14 : 1, 3 : 0, 5 : 1}
clutSizes = { 0x13 : 0x400, 0x14 : 0x40 , 3 : 0x400, 5 : 0x40 }

parser = argparse.ArgumentParser(description='Extract iif file images from packed FSNRN PS2 data file')
parser.add_argument('input', metavar='N', type=Path, help='Path to input file or folder')
parser.add_argument('output', metavar='N', type=Path, help='Path to output file or folder')
args = parser.parse_args()

class image:
    def __init__(self):
        self.header = namedtuple('header', ['numImages', 'fileSize'])
        self.rnimage = namedtuple('rnimage', ['colorDepth', 'bitDepth', 'width', 'height', 'clut_offset', 'data_offset'])
        self.iif = namedtuple('iif', ['magic', 'width', 'height', 'type'])
        self.image_list = list()
        self.iif_list = list()
        
    def read(self, stream: BinaryIO):
        self.header = self.header._make(unpack(image_format, stream.read(calcsize(image_format))))
        for i in range(self.header.numImages):
            self.image_list.append(self.rnimage._make(unpack(rnimage_format, stream.read(calcsize(rnimage_format)))))
    
    def toiif(self, istream: BinaryIO, path):
        for n, i in enumerate(self.image_list) :
            with open(os.path.join(path, str(n)+'.iif'), 'wb+') as ostream :
                ostream.write(pack(iif_format, iif_magic, i.width, i.height, clutDepths.get(i.bitDepth)))
                istream.seek(i.clut_offset)
                ostream.write(istream.read(clutSizes.get(i.bitDepth)))
                istream.seek(i.data_offset)
                ostream.write(istream.read((i.width*i.height) >> realBitDepths.get(i.bitDepth)))
    
    def toRN_image(self, files, ostream: BinaryIO):
        files = sorted(files.glob('*.iif'), key=(lambda file : int(file.stem)))
        self.header._fields_defaults
        self.rnimage._fields_defaults
        self.header.numImages = len(files)
        ostream.write(pack(image_format, self.header.numImages, 0))
        clut = list()
        data = list()
        self.rnimage.colorDepth = 8 # default to this. I'm not actualy sure what it is there for
        headerSize = len(files)*calcsize(rnimage_format)
        ostream.write(b'\x00' * headerSize)
        for n, file in enumerate(files):
            with file.open(mode='rb') as istream:
                self.iif_list.append(self.iif._make(unpack(iif_format, istream.read(calcsize(iif_format)))))
                clut.append(istream.read(clutSizes.get(self.iif_list[n].type)))
                data.append(istream.read((self.iif_list[n].width*self.iif_list[n].height) >> realBitDepths.get(self.iif_list[n].type)))
        del files
        for n, i in enumerate(self.iif_list):
            self.rnimage.bitDepth = clutDepths[i.type]
            self.rnimage.width = i.width
            self.rnimage.height = i.height
            self.image_list.append(pack(rnimage_format, self.rnimage.colorDepth, self.rnimage.bitDepth, self.rnimage.width,
                                        self.rnimage.height, ostream.tell(), 0))
            ostream.write(clut[n])
        del clut
        for n, i in enumerate(self.iif_list):
            self.image_list[n] = self.image_list[n][:-4] + pack('<I', ostream.tell())
            ostream.write(data[n])
            ostream.write(bytearray(b'\x00' * (ostream.tell() % 16)))
        del data, headerSize
        EOF = ostream.tell()
        ostream.seek(0xC)
        ostream.write(pack('<I', EOF))
        del EOF
        for i in self.image_list: ostream.write(i)
            
if __name__ == '__main__':
    test = image()
    if args.input.is_file()  :
        with open(sys.argv[1], 'rb') as stream :
            test.read(stream)
            args.output.mkdir(exist_ok=True)
            test.toiif(stream, args.output)
    elif args.input.is_dir:
        with args.output.open(mode='wb+') as stream :
            test.toRN_image(args.input, stream)
    sys.exit()
    
        