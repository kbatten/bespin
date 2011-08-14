#/usr/bin/env python
"""Mine swtor data files

Only mines xml files, and only if they are less than 1MB in size
Stores the results into the provided sqlite database.swtor

Kinds:
Ability -- abilities, talents
"""
import sys
import getopt
import json
import os

import bespin

def usage(err=None):
    if err:
        print "Error: %s\n" % err
        r = 1
    else:
        r = 0

    print """\
Syntax: """ + sys.argv[0] + """ [options]

Options:
 -h, --help

 -s <source>, --source=<source>
     Data source that will be imported from
     Files will be opened recursively from here

 -d <destination>, --destination=<destination>
     Data destination that will be exported to
     This is an sqlite database, and the table is "swtor"

 -f <id>, --filter=<id>
     NYI
     Only extract objects with an Id that matches the pattern

Example:
 """ + sys.argv[0] + """ -s assets_locale_en_us_1 -d data.sdb
"""
    sys.exit(r)


class Config(object):
    def __init__(self, argv):
        self.source = ""
        self.destination = ""
        self.filter = ""
        self.parse_argv(argv)

    def parse_argv(self, argv):
        try:
            opts, args = getopt.getopt(argv[1:],
                'hs:d:f:', [
                'help',
                'source=',
                'destination=',
                'filter='])
            for o, a in opts:
                if o == '-h' or o == '--help':
                    usage()
                elif o == '-s' or o == '--source':
                    self.source = a
                elif o == '-d' or o == '--destination':
                    self.destination = a
                elif o == '-f' or o == '--filter':
                    self.filter = a

            msg = ""
            if not self.source or not self.destination:
                usage("missing source or destination")
        
        except IndexError:
            usage()
        except getopt.GetoptError, err:
            usage(err)

def walk_files(base, extension, maxsize):
    for root, subFolders, files in os.walk(base):
        print root
        for file in files:
            f = os.path.join(root, file)
            if f.endswith(extension) and os.path.getsize(f) < maxsize:
                yield f

if __name__ == "__main__":
    
    config = Config(sys.argv)
    miner = bespin.Miner(config.destination)
    count = 0

    for xmlfile in walk_files(config.source, '.xml', 1*1024*1024):
        if miner.loadxml(xmlfile, kinds=['Ability', 'DataTable'], idfilter=config.filter):
            count += 1

    print "Added/updated {0} records".format(count)
