import os
import struct
import time
import sys
import zlib
import re
import StringIO


class DBLBFile(object):
    HEADER_SIZE = 8
    OBJECT_HEADER_SIZE = 42

    TYPE1 = "04000103".decode("hex")
    
    def __init__(self, filename):
        if isinstance(filename, str):
            self.fp = file(filename, "rb")
        else:
            self.fp = filename
        self.filesize = 0
        self.header = {}
        self.objects = {}

        self._read_filesize()
        self._read_header()

        if self.header["id"] != "DBLB":
            self.fp.close()
            raise Exception("wrong file type, expected DBLB")

        self._read_objects()

    def close(self):
        self.fp.close()

    def _read_header(self):
        self.fp.seek(0)
        raw_header = self.fp.read(DBLBFile.HEADER_SIZE)
        unpacked_header = struct.unpack("< 4s I", raw_header)
        self.header["id"] = unpacked_header[0]
        self.header["1"] = unpacked_header[1] # ?

    def _read_filesize(self):
        self.fp.seek(0, os.SEEK_END)
        self.filesize = self.fp.tell()
        

    def _read_object(self):
        # 0-3:   size of object
        # 4-5:   some kind of type marker
        # 6-7:   offset of data
        # 8-41:  ?
        # 42-45: marker (04 00 01 0X)
        # 46-XX: label + 00 + 00
        # XX-  : data
        
        # align to 8 bytes
        offset = self.fp.tell()
        if offset%8:
            offset = offset + (8-(offset%8))
            self.fp.seek(offset)
       
        raw_header = self.fp.read(DBLBFile.OBJECT_HEADER_SIZE)
        if len(raw_header) != DBLBFile.OBJECT_HEADER_SIZE:
            return None, None
        unpacked_header = struct.unpack("< IHHBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB", raw_header)

        # the 6 in the following is the marker size and the 2 null padding size
        label_size = unpacked_header[2] - DBLBFile.OBJECT_HEADER_SIZE - 6
        data_size = unpacked_header[0] - DBLBFile.OBJECT_HEADER_SIZE - label_size - 6

        marker = self.fp.read(4)

        # read 4bytes (?) + label + two nulls
        self.fp.seek(4, os.SEEK_CUR)
        label = self.fp.read(label_size)
        self.fp.seek(2, os.SEEK_CUR)

        data = self._decode_data(unpacked_header[1], self.fp.read(data_size))
        return label, {"data":data,"header":unpacked_header}
        
    def _read_objects(self):
        self.fp.seek(DBLBFile.HEADER_SIZE)
        while True:
            label, value = self._read_object()
            if not label:
                break
            self.objects[label] = value

    def _decode_data(self, kind, encoded_data):
        if kind == 15:
            # container : [0x00]
            # 256byte string: [0x06][length][string]
            serialized_data = zlib.decompress(encoded_data)
#            data = self._deserialize(serialized_data)
            data = serialized_data
        else:
            data = encoded_data
        return data

    def _deserialize(self, data):
        mode = 0x00
        for c in data:
            if mode == 0x00:
                if c == 0x06:
                    mode = 0x06
                    data = ""
                    length = -1
                    continue
            if mode == 0x06:
                if length == -1:
                    length = ord(c)
                    continue
                elif length > 0:
                    print c,
                    d += c
                    length -= 1
                else:
                    mode = 0x00
                    continue

class PBUKFile(object):
    HEADER_SIZE = 12
    def __init__(self, filename):
        if isinstance(filename, str):
            self.fp = file(filename, "rb")
        else:
            self.fp = filename
        self.filesize = 0
        self.header = {}
        self.objects = {}

        self._read_filesize()
        self._read_header()

        if self.header["id"] != "PBUK":
            self.fp.close()
            raise Exception("wrong file type, expected PBUK")

        self._read_chunks()

    def close(self):
        self.fp.close()

    def _read_header(self):
        self.fp.seek(0)
        raw_header = self.fp.read(PBUKFile.HEADER_SIZE)
        unpacked_header = struct.unpack("< 4s H H I", raw_header)
        self.header["id"] = unpacked_header[0]
        self.header["chunks"] = unpacked_header[1] # number of chunks?
        self.header["2"] = unpacked_header[2] # ?
        self.header["first_chunk_size"] = unpacked_header[3] # length of the first chunk?
#        print "pbuk_header", self.header

    def _read_filesize(self):
        self.fp.seek(0, os.SEEK_END)
        self.filesize = self.fp.tell()

    def _read_chunks(self):
        self.fp.seek(PBUKFile.HEADER_SIZE)
        chunk_size = self.header["first_chunk_size"]
        for i in range(self.header["chunks"]):
            chunk_size = self._read_next_chunk(chunk_size)

    def _read_next_chunk(self, size):
        chunk = self.fp.read(size)
        # assume its a DBLB chunk
        dblb = DBLBFile(StringIO.StringIO(chunk))
        self.objects.update(dblb.objects)
        dblb.close()
        if self.fp.tell() > self.filesize - 4:
            footer = 0
        else:
            raw_footer = self.fp.read(4)
            unpacked_footer = struct.unpack("< I", raw_footer)
            footer = unpacked_footer[0] # length of next chunk?
        return footer

def walk_files(base, extension):
    for root, subFolders, files in os.walk(base):
        for file in files:
            f = os.path.join(root, file)
            if f.endswith(extension):
                yield f

sourcebase = r"C:\Program Files (x86)\Star Wars-The Old Republic\Assets"
#filenames = [r"D:\src\bespin\test\d2222ce825b29178.pbuk"]
#filenames = [r"D:\src\bespin\test\dest\red_system_1\pbuk\1d18445f5f283189.pbuk"]

filenames = walk_files(r"D:\src\bespin\assets\\","pbuk")

items = 0
for filename in filenames:
    pbuk = PBUKFile(filename)
#    item = "abl.sith_warrior.assault"
#    item = "abl.sith_warrior.vicious_throw"
#    item = "npc.location.taris.mob.shyrack.bogstalker_extractor"
#    item = "npc.location.balmorra_republic.mob.droid.empire.imperial_service_droid"
#    print filename

    for item in pbuk.objects:
#    if item in pbuk.objects:
        if item.find("vicious") >= 0:
            items += 1
            print item
            print pbuk.objects[item]
    pbuk.close()
            
print "done"
