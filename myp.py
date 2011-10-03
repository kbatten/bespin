import os
import struct
import time
import sys
import zlib
import re


class MYPFile(object):
    def __init__(self, filename, ignore_id=False):
        self.fp = file(filename, "rb")
        self.filesize = 0
        self.header = {}
        self.filetable = []

        self._load_header()
        self._load_filesize()

        if self.header["id"] != "MYP" and not ignore_id:
            self.fp.close()
            raise Exception("wrong file type")

        self._load_filetable()

    def close(self):
        self.fp.close()

    def _load_header(self):
        self.fp.seek(0)
        raw_header = self.fp.read(40)
        unpacked_header = struct.unpack("< 3sx 4x 4x Q I I I 4x 4x", raw_header)
        self.header["id"] = unpacked_header[0]
        self.header["first_filetable"] = unpacked_header[1]
        self.header["first_maxfiles"] = unpacked_header[2]
        self.header["files"] = unpacked_header[3]
        self.header["filetables"] = unpacked_header[4]
#        print "header", self.header

    def _load_filesize(self):
        self.fp.seek(0, os.SEEK_END)
        self.filesize = self.fp.tell()
#        print "filesize", self.filesize

    def _load_filetable(self):
        # root filetable entry
        filetable_header = {
            "maxfiles" : 0,
            "next_filetable" : self.header["first_filetable"]
            }
        while filetable_header["next_filetable"] != 0:
            # iterate through all filetables
            pos = filetable_header["next_filetable"]
            filetable_header = self._read_filetable_header(pos)
            filetable_entries = self._read_filetable_entries(pos + 12, filetable_header["maxfiles"])
            self.filetable.extend(filetable_entries)
#        print len(self.filetable)

    def _read_filetable_header(self, pos):
        self.fp.seek(pos)
        filetable_header = {}
        raw_filetable_header = self.fp.read(12)
        unpacked_filetable_header = struct.unpack("< I Q", raw_filetable_header)
        filetable_header["maxfiles"] = unpacked_filetable_header[0]
        filetable_header["next_filetable"] = unpacked_filetable_header[1]
#        print filetable_header
        return filetable_header

    def _read_filetable_entries(self, pos, maxfiles):
        self.fp.seek(pos)
        file_headers = []
        for i in range(maxfiles):
            file_header = {}
            raw_file_header = self.fp.read(34)
            unpacked_file_header = struct.unpack("< Q I I I 8s I H", raw_file_header)
            file_header["position"] = unpacked_file_header[0]
            file_header["header_size"] = unpacked_file_header[1]
            file_header["compressed_size"] = unpacked_file_header[2]
            file_header["uncompressed_size"] = unpacked_file_header[3]
            file_header["filename"] = unpacked_file_header[4].encode("hex")
            file_header["crc32"] = unpacked_file_header[5]
            file_header["compression"] = unpacked_file_header[6]
            if file_header["position"] == 0:
                break
            file_headers.append(file_header)
        return file_headers

    def _read_file(self, file_header):
        self.fp.seek(file_header["position"])
        # read file header?
        assert(file_header["header_size"] == 0)
        
        raw = self.fp.read(file_header["compressed_size"])
        if file_header["compression"] == 1:
            data = zlib.decompress(raw)
        elif file_header["compression"] == 0:
            data = raw
        else:
            raise Exception("unknown compression",file_header["compression"])

        # try to figure out what the files actually are
        # since we don't have a list of filenames -> hashes
        if file_header["filename"] in ["13e36079f828e03e",
                                       "e6715ac71361b9e4"]:
            # no clue at all what these files are
            kind = "raw"
        elif data[:4] == "RIFF":
            # audio file
            kind = "riff"
        elif data[:4] == "BKHD":
            kind = "bkhd"
        elif data[:4] == "FACE":
            kind = "face"
        elif data[:4] == "PROT":
            kind = "prot"
        elif data[:4] == "SCPT":
            kind = "scpt"
        elif data[:4] == "PBCK":
            kind = "pbck"
        elif data[:4] == "PBUK":
            kind = "pbuk"
        elif data[:4] == "SDEF":
            kind = "sdef"
        elif data[:4] == "PINF":
            kind = "pinf"
        elif data[:4] == "DBLB":
            kind = "dblb"
        elif data[:3] == "AMX":
            kind = "amx"
        elif data[:3] == "DDS":
            kind = "dds"
        elif data[:3] == "GFX":
            kind = "gfx"
        elif data[:3] == "CWS":
            kind = "cws"
        elif data[:3] == "CFX":
            kind = "cfx"
        elif data == chr(0x0d) + chr(0x0a):
            # wtf is this?
            kind = "raw"
        elif data[:18] == "29DE6CC0BAA4532B25F5B7A5F666E2EEC801".decode("hex"):
            # not sure what this is, its some kind of 3d file
            kind = "raw"
        elif data[:8] == "E80300000C000000".decode("hex"):
            # not sure what this is, its some kind of 3d file
            kind = "raw"
#        elif data[:80].find("<?xml") != -1:
#            kind = "xml"
        elif data[:3] == chr(0xef) + chr(0xbb) + chr(0xbf) and data[3:80].strip().find("<") == 0:
            kind = "xml"
        elif data[:80].strip().find("<") == 0:
            kind = "xml"
        elif data[:2] == chr(0xff) + chr(0xfe) and data[2:80].decode("utf8").strip().find("<") == 0:
            kind = "xml"
        elif self._check_ini(data[:512]):
            kind = "ini"
        elif self._check_filelist(data[:512]):
            kind = "txt"
        elif data.find("GOD"+chr(0)+"Root") != -1: # TODO: need a better match
            kind = "raw"
        elif data.find("GOD"+chr(0)+"root") != -1: # TODO: need a better match
            kind = "raw"
        elif data.find("GOD"+chr(0)+"Camera"+chr(0)+"Root") != -1: # TODO: need a better match
            kind = "raw"
#        elif data.find(chr(0)) != -1:
#            # catchall for binary files
#            kind = "raw"
        else:
            kind = "unknown"
        return data, file_header["filename"], kind

    def _check_ini(self, data):
        if data.find(chr(0)) != -1:
            return False
        for line in data.split("\n"):
            # TODO: need a better match
            if re.search("^\s*[-\\\_a-zA-Z0-9.]+\s*=\s*[-\\\_a-zA-Z0-9.]+\s*$", line):
                return True
        return False

    def _check_filelist(self, data):
        if data.find(chr(0)) != -1:
            return False
        for line in data.split("\n"):
            # TODO: need a better match
            if re.search("^\s*[-\\\_a-zA-Z0-9.]+\s*$", line):
                return True
        return False

def walk_files(base, extension):
    for root, subFolders, files in os.walk(base):
        for file in files:
            f = os.path.join(root, file)
            if f.endswith(extension):
                yield f

sourcebase = r"C:\Program Files (x86)\Star Wars-The Old Republic\Assets"
destbase = r"D:\src\bespin\test\dest"
start_time = time.time()
for filename in walk_files(sourcebase, "tor"):
    failed = False
    myp = MYPFile(filename)
    if os.path.basename(filename).rsplit(".",1)[0] in ["red_locale_en_us_1",
                                                       "red_locale_en_us_2",
                                                       "red_locale_en_us_3",
                                                       "red_locale_en_us_4",
                                                       "red_locale_en_us_5",
                                                       "red_locale_en_us_6",
                                                       "red_locale_en_us_7",
                                                       "red_locale_en_us_8",
                                                       "red_locale_en_us_9",
                                                       "red_locale_en_us_10",
                                                       "red_locale_en_us_11",
                                                       "red_locale_en_us_12",
                                                       "red_locale_en_us_13",
                                                       "red_locale_en_us_14",
                                                       "red_locale_en_us_15",
                                                       "red_main_1",
                                                       "red_main_10",
                                                       "red_main_11",
                                                       "red_main_12",
                                                       "red_main_13",
                                                       "red_main_14",
                                                       "red_main_15",
                                                       "red_main_16",
                                                       "red_main_17",
                                                       "red_main_18",
                                                       "red_main_19",
                                                       "red_main_2",
                                                       "red_main_20",
                                                       "red_main_21",
                                                       "red_main_22",
                                                       "red_main_23",
                                                       "red_main_24",
                                                       "red_main_25x",
                                                       "red_main_26x",
                                                       "red_main_27x",
                                                       "red_main_3x",
                                                       "red_main_4x",
                                                       "red_main_5x",
                                                       "red_main_6x",
                                                       "red_main_7x",
                                                       "red_main_8x",
                                                       "red_main_9x",
                                                       "red_system_1x",
                                                       ]:
        print "skipping", os.path.basename(filename).rsplit(".",1)[0]
        myp.close()
        continue
#        pass

    dirfile = destbase + "\\" + os.path.basename(filename).rsplit(".",1)[0]
    print "proccess", os.path.basename(filename).rsplit(".",1)[0]
    
    for f in myp.filetable:

        data, namehash, kind = myp._read_file(f)
        if kind == "raw" or kind == "unknown":
            ext = "txt"
        else:
            ext = kind
#        if kind in ["xml"]:
        if True:
            try:
                os.makedirs(dirfile + "\\" + kind)
            except:
                pass
            try:
                outfile = file(dirfile + "\\" + kind + "\\" + namehash + "." + ext,"wb")
            except Exception as e:
                outfile = file(dirfile + "\\" + namehash,"wb")
                outfile.write(data)
                outfile.close()
                raise e
            outfile.write(data)
            outfile.close()
#        assert kind != "unknown"
        if kind == "unknown":
#            print "unknown:",namehash + "." + ext
            failed = True
    if failed:
        print "faaaaail", os.path.basename(filename).rsplit(".",1)[0]
#        myp.close()
#        sys.exit()
    myp.close()

end_time = time.time()
print (end_time - start_time),"seconds"

