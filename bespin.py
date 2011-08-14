#!/usr/bin/env python
"""Mine swtor data files

Only mines xml files, and only if they are less than 10MB in size
Stores the results into the provided sqlite database.swtor

Kinds:
Ability -- abilities, talents

Todo:
Seperate out gui from processing so even if wx isn't installed it can
still run in cli mode
"""


import wx
import time
import threading
import sys
import os
import getopt

import bespin



class BespinFrameMain(wx.Frame):
    def __init__(self, app):
        wx.Frame.__init__(self, None, title="Bespin", size=(600,300), style=wx.SYSTEM_MENU | wx.CLOSE_BOX | wx.CAPTION)

        self.app = app
        #self.control_source = wx.TextCtrl(self)
        self.panel = wx.Panel(self)

        self.static_source = wx.StaticText(self.panel, label="source: ")
        self.text_source = wx.TextCtrl(self.panel, size=(300,-1))
        self.static_destination = wx.StaticText(self.panel, label="destination: ")
        self.text_destination = wx.TextCtrl(self.panel, size=(300,-1))
        self.button_mine = wx.Button(self.panel, label="Mine", size=(100,30))

        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer2.Add(self.static_source, 1, wx.ALIGN_CENTER)
        self.sizer2.Add(self.text_source, 1, wx.ALIGN_CENTER)
        self.sizer2.Add(self.static_destination, 1, wx.ALIGN_CENTER)
        self.sizer2.Add(self.text_destination, 1, wx.ALIGN_CENTER)

        self.sizer3 = wx.BoxSizer()
        self.sizer3.Add(self.button_mine, 1, wx.ALIGN_CENTER)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.sizer2, 1, wx.ALIGN_CENTER)
        self.sizer.Add(self.sizer3, 1, wx.ALIGN_CENTER)

        self.panel.SetSizer(self.sizer, wx.EXPAND)

        self.statusbar = self.CreateStatusBar()

        self.Bind(wx.EVT_BUTTON, self.OnButtonMineClick, self.button_mine)

        self.statusbar.SetFields(["idle",""])
        self.statusbar.SetStatusWidths([150,-1])


    def OnButtonMineClick(self, event):
        if not self.app.started:
            return

        if self.app.processing:
            self.app.cancelled = True
            return
        else:
            source = self.text_source.GetValue()
            destination = self.text_destination.GetValue()
            if not source or not destination:
                return
            self.app.process_thread(source, destination, [self.text_source, self.text_destination], self.button_mine, self.statusbar)



class BespinApp(object):
    def __init__(self, app=None):
        self.started = False
        self.processing = False
        self.cancelled = False

        if app:
            self.app = app
            self.frames = {
                'main':BespinFrameMain(self)
                }


    def start(self):
        """Start the windowed app"""
        if not self.started:
            self.frames['main'].Show(True)
            self.started = True
            self.app.MainLoop()


    def process_thread(self, source, destination, frames, button, statusbar):
        """Start processing data in a thread

        Keyword arguments:
        source -- base directory to recurse through
        destination -- sqlite database to write to
        frames -- wxFrames to disable
        button -- wxButton to change to cancel
        statusbar -- wxStatusBar to update
        """
        if self.processing:
            return
        self.cancelled = False

        processing_thread = threading.Thread(name="processing",
                                             target=self.process,
                                             args=(source, destination, frames, button, statusbar))
        processing_thread.daemon = True
        processing_thread.start()


    def process(self, source, destination, frames=None, button=None, statusbar=None):
        """Process data from source and put it in destination database

        Keyword arguments:
        source -- base directory to recurse through
        destination -- sqlite database to write to
        frames -- wxFrames to disable
        button -- wxButton to change to cancel
        statusbar -- wxStatusBar to update
        """
        if statusbar:
            statusbar.SetStatusText("processing", 0)

        if button:
            button.SetLabel("&Cancel")

        if frames:
            for frame in frames:
                frame.Enable(False)

        self.processing = True

        miner = bespin.Miner(destination)
        count = 0
        for xmlfile in self._walk_files(source, '.xml', 10*1024*1024):
            if self.cancelled:
                break
            if statusbar:
                if xmlfile.find(source) == 0:
                    statustext = "..." + xmlfile[len(source):]
                else:
                    statustext = xmlfile
                statusbar.SetStatusText(statustext, 1)
            if miner.loadxml(xmlfile, kinds=['Ability', 'DataTable']):
                count += 1
        miner.close()

        if statusbar:
            statusbar.SetStatusText("processed {0} files".format(count), 0)

        if button:
            button.SetLabel("Mine")

        if frames:
            for frame in frames:
                frame.Enable(True)

        if statusbar:
            statusbar.SetStatusText("", 1)

        self.cancelled = False
        self.processing = False
        return count


    def _walk_files(self, base, extension, maxsize):
        for root, subFolders, files in os.walk(base):
            for file in files:
                f = os.path.join(root, file)
                if f.endswith(extension) and os.path.getsize(f) < maxsize:
                    yield f



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
        self.gui = True
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
                    self.gui = False
                elif o == '-d' or o == '--destination':
                    self.destination = a
                    self.gui = False
                elif o == '-f' or o == '--filter':
                    self.gui = False
                    self.filter = a

            if not self.source and self.destination:
                usage("missing source")
            if self.source and not self.destination:
                usage("missing destination")

        except IndexError:
            usage()
        except getopt.GetoptError, err:
            usage(err)



if __name__ == "__main__":
    config = Config(sys.argv)

    if config.gui:
        app = BespinApp(app=wx.App(False))
        app.start()
    else:
        app = BespinApp()
        count = app.process(config.source, config.destination)
        print "processed {0} files.".format(count)


