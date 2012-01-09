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
        self.fp.seek(file_header["position"] +  file_header["header_size"])
        
        raw = self.fp.read(file_header["compressed_size"])
        if file_header["compression"] == 1:
            data = zlib.decompress(raw)
        elif file_header["compression"] == 0:
            data = raw
        else:
            raise Exception("unknown compression",file_header["compression"])

        # try to figure out what the files actually are
        # since we don't have a list of filenames -> hashes
        if file_header["filename"] in ["e6715ac71361b9e4",
                                       "36f834cbe1d27884",
                                       "902483220a24be1e",
                                       "xxx13e36079f828e03e",
                                       ]:
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
        elif data[:4] == "GAWB":
            kind = "gawb"
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
        elif data[:34] == "|NAME|ID|REFID|FQN|ORG|ORGID|TAGS|":
            kind = "csv"
        elif data[4:11] == chr(0x00) + chr(0x0) + chr(0x00) + chr(0x00) + "cnv":
            # seems to be a list of wem filenames + some resource data
            kind = "raw"
        elif self._check_localization(file_header, data):
            kind = "raw_check"
        elif data == chr(0x00) * 8:
            # don't know why there are files of 8 nulls
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

    def _check_localization(self, file_header, data):
#        if file_header["filename"] in ["3b5b30546d955481",
#                                       "a78052459331e170",
#                                       "eedfda0077674099",
#                                       "2aaf0fa691e3639f",
#                                       "11c1050ed00f1f4a",
#                                       "0bdffb3f2e924fd7",
#                                       "98e49051d1d9ed11",
#                                       "b415479df273044a",
#                                       "ac7656066636b235",
#                                       "c9300bb68a3b40bb",
#                                       "ee14dc7d4fee13a6",
#                                       "da8e838553638838",
#                                       "76c36aea7198ad3f",
#                                       "6d8a9b006a1ef068",
#                                       "8c09a710e09e88e4",
#                                       "c41b92ce2816ab87",
#                                       "a68ccb6b692cb71d",
#                                       "c1e2f3795e5ed93c",
#                                       "4bd2e6544beb826b",
#                                       "a8c85df12f5553b3",
#                                       "10629ed1620a6d68",
#                                       "3d78e1804933a6c4",
#                                       "906a7e8596eb6f1a",
#                                       "12d5bbdc7456f4b7",
#                                       ]:
#            # a list of skill info (at least text)
#            # possibly localization
#            # this is probably a file that needs to be figured out
#            print data[3:7].encode("hex")
#            print struct.unpack("< I", data[3:7])
#            return True
#        count = struct.unpack("< I", data[3:7])[0]
#        print count
        if data[:3] == chr(0x01) + chr(0x00) + chr(0x00):
            return True
        return False


def walk_files(base, extension):
    for root, subFolders, files in os.walk(base):
        for file in files:
            f = os.path.join(root, file)
            if f.endswith(extension):
                yield f

sourcebase = r"C:\Program Files (x86)\Star Wars-The Old Republic\Assets"
destbase = r"D:\src\bespin\assets"
start_time = time.time()
for filename in walk_files(sourcebase, "tor"):
    failed = False
    myp = MYPFile(filename)
    skip_files = False
    if skip_files and \
        os.path.basename(filename).rsplit(".",1)[0] in ["swtor_en-us_area_alderaan_1",
                                                        "swtor_en-us_area_balmorra_1",
                                                        "swtor_en-us_area_belsavis_1",
                                                        "swtor_en-us_area_corellia_1",
                                                        "swtor_en-us_area_coruscant_1",
                                                        "swtor_en-us_area_dromund_kaas_1",
                                                        "swtor_en-us_area_hoth_1",
                                                        "swtor_en-us_area_hutta_1",
                                                        "swtor_en-us_area_ilum_1",
                                                        "swtor_en-us_area_korriban_1",
                                                        "swtor_en-us_area_misc_1",
                                                        "swtor_en-us_area_nar_shaddaa_1",
                                                        "swtor_en-us_area_open_worlds_1",
                                                        "swtor_en-us_area_ord_mantell_1",
                                                        "swtor_en-us_area_quesh_1",
                                                        "swtor_en-us_area_raid_1",
                                                        "swtor_en-us_area_taris_1",
                                                        "swtor_en-us_area_tatooine_1",
                                                        "swtor_en-us_area_tython_1",
                                                        "swtor_en-us_area_voss_1",
                                                        "swtor_en-us_cnv_comp_chars_imp_1",
                                                        "swtor_en-us_cnv_comp_chars_rep_1",
                                                        "swtor_en-us_cnv_misc_1",
                                                        "swtor_en-us_cnv_transitions_1",
                                                        "swtor_en-us_global_1",
                                                        "swtor_main_anim_creature_a_1",
                                                        "swtor_main_anim_creature_b_1",
                                                        "swtor_main_anim_creature_npc_1",
                                                        "swtor_main_anim_humanoid_bfab_1",
                                                        "swtor_main_anim_humanoid_bfns_1",
                                                        "swtor_main_anim_humanoid_bmaf_1",
                                                        "swtor_main_anim_humanoid_bmns_1",
                                                        "swtor_main_anim_misc_1",
                                                        "swtor_main_areadat_1",
                                                        "swtor_main_areadat_epsilon_1",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                        "",
                                                       ]:
        print "skipping", os.path.basename(filename).rsplit(".",1)[0]
        myp.close()
        continue

    dirfile = destbase + "\\" + os.path.basename(filename).rsplit(".",1)[0]
    print "proccess", os.path.basename(filename).rsplit(".",1)[0]
    
    for f in myp.filetable:
        data, namehash, kind = myp._read_file(f)
        if kind[:3] == "raw" or kind == "unknown":
            ext = "txt"
        else:
            ext = kind
        if not kind in ["raw",
                        "face",
                        "dds",
                        "amx",
                        "gfx",
                        ]:
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
        if kind == "unknown":
            print "unknown:",namehash + "." + ext
            failed = True
        assert kind != "unknown"
    if failed:
        print "faaaaail", os.path.basename(filename).rsplit(".",1)[0]
#        myp.close()
#        sys.exit()
    myp.close()

end_time = time.time()
print (end_time - start_time),"seconds"

