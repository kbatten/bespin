#/usr/bin/env python
"""Mine swtor data files

Only mines xml files, and only if they are less than 1MB in size
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

 -f <id>, --filter=<id>
     Only extract objects with an Id that matches the pattern

Example:
 """ + sys.argv[0] + """ -s assets_locale_en_us_1/ -d data.sdb -f "abl.*"
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

    outputfile = file(config.destination,"w")

    for xmlfile in walk_files(config.source, '.xml', 1*1024*1024):
        try:
            data = miner.loadxml(xmlfile, kind='Ability', idfilter=config.filter)
        except Exception as ex:
            print xmlfile
            raise ex
        if data:
            outputfile.write(xmlfile + "\n")
            print xmlfile
            try:
                outputfile.write(data['^']['Id'] + "\n")
                print data['^']['Id']
                outputfile.write(data['Name']['text']['%'] + "\n")
                print data['Name']['text']['%']
                outputfile.write(data['Description']['text']['%'] + "\n")
                print data['Description']['text']['%']
            except:
                pass
            outputfile.write("\n")
            print
