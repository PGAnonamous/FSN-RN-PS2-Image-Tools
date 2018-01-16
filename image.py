#!/usr/bin/env python
import string, re, sys, os, os.path, struct, fnmatch
from struct import unpack, pack

if sys.version_info[0] < 3 :
	print('Must be using Python 3')
	sys.exit(0)

if len(sys.argv) != 4 :
   print('Please give an option an input file and an output directory')
   sys.exit(0)
   
if sys.argv[1] == '-e' :
		
	infile = open(sys.argv[2],'rb')
	
	directory = sys.argv[3]
	
	if not os.path.exists(directory):
		os.makedirs(directory)
	
	save_path = os.path.join(os.getcwd(), directory)
	
	HEAD = bytearray(b'\x49\x49\x46\x31')
	
	infile.seek(4)
	FILES = int.from_bytes(infile.read(4), byteorder='little')
	if FILES == 0 :
		print('This file probably does not contain images')
		sys.exit(0)
	infile.seek(32)
	
	i = 0
	tmp = 28
	
	while i < FILES :
		infile.seek(tmp+(i*32))
		BITS = int.from_bytes(infile.read(4), byteorder='little')
		WIDTH = infile.read(4)
		HEIGHT = infile.read(4)
		OFFSETCLUT = int.from_bytes(infile.read(4), byteorder='little')
		OFFSETDATA = int.from_bytes(infile.read(4), byteorder='little')
		if i == (FILES-1) :
			infile.seek(12)
		else :
			infile.seek(tmp+(i*32)+48)
		SIZE = int.from_bytes(infile.read(4), byteorder='little') - OFFSETDATA
		infile.seek(OFFSETCLUT)
		if BITS == 19 :
			CLUT = infile.read(1024)
			TYPE = bytearray(b'\x03\x00\x00\x00')
		if BITS == 20 :
			CLUT = infile.read(64)
			TYPE = bytearray(b'\x05\x00\x00\x00')
		infile.seek(OFFSETDATA)
		DATA = infile.read(SIZE)
		outfile = os.path.join(save_path, str(i)+".iif")
		file = open(outfile,'wb')
		file.write(HEAD+WIDTH+HEIGHT+TYPE+CLUT+DATA)
		file.close()
		i += 1
	
	
	
	infile.close()
elif sys.argv[1] == '-c' :
		
	outfile = open(sys.argv[3],'wb')
	
	directory = sys.argv[2]
	
	if not os.path.exists(directory):
		print(directory+' does not exist')
		sys.exit(0)
		
	files = fnmatch.filter(os.listdir(directory), '*.iif')
	if len(files) == 0 :
		print('No .iif files found')
		sys.exit(0)
	
	save_path = os.path.join(os.getcwd(), directory)
	
	ZEROS = bytearray(b'\x00\x00\x00\x00')
	
	#Write the Header
	outfile.write(ZEROS+len(files).to_bytes(4, byteorder='little')+ZEROS+ZEROS)
	i = 0
	while i < len(files) :
		infilepath = os.path.join(save_path, str(i)+".iif")
		infile = open(infilepath, 'rb')
		infile.seek(4)
		SIZE = infile.read(8)
		iiftype = int.from_bytes(infile.read(4), byteorder='little')
		if (iiftype == 5) :
			TYPE = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x14\x00\x00\x00')
		if iiftype == 3 or (iiftype == 0) :
			TYPE = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x13\x00\x00\x00')
		outfile.write(TYPE+SIZE+ZEROS+ZEROS)
		infile.close()
		i += 1

	headerlen = outfile.tell()
	
	#Write the clut data and clut offset
	i = 0
	while i < len(files) :
		infilepath = os.path.join(save_path, str(i)+".iif")
		infile = open(infilepath, 'rb')
		infile.seek(12)
		iiftype = int.from_bytes(infile.read(4), byteorder='little')
		if (iiftype == 5) :
			length = 64
		if (iiftype == 3) or (iiftype == 0) :
			length = 1024
		CLUT = infile.read(length)
		OFFSET = (outfile.tell()).to_bytes(4, byteorder='little')
		outfile.seek(40+(i*32))
		outfile.write(OFFSET)
		outfile.seek(0, 2)
		outfile.write(CLUT)
		infile.close()
		i += 1
		
	#Write the image data and image offset
	i = 0
	while i < len(files) :
		infilepath = os.path.join(save_path, str(i)+".iif")
		infile = open(infilepath, 'rb')
		infile.seek(12)
		iiftype = int.from_bytes(infile.read(4), byteorder='little')
		if (iiftype == 5) :
			infile.seek(64+16)
		if (iiftype == 3) or (iiftype == 0) :
			infile.seek(1024+16)
		DATA = infile.read()
		OFFSET = (outfile.tell()).to_bytes(4, byteorder='little')
		outfile.seek(44+(i*32))
		outfile.write(OFFSET)
		outfile.seek(0, 2)
		outfile.write(DATA)
		infile.close()
		i += 1
	
	#Write the final filesize offset
	OFFSET = (outfile.tell()).to_bytes(4, byteorder='little')
	outfile.seek(12)
	outfile.write(OFFSET)
	outfile.close()
else :
	print('Usage:\nscript.py -e input.dat outdir  to extract\nscript.py -c indir out.dat     to pack')
	sys.exit(0)
