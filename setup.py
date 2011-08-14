from distutils.core import setup
import py2exe
import sys


if len(sys.argv) == 1:
    sys.argv.append("py2exe")
    sys.argv.append("-q")


class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "1.0.0"
        self.company_name = "No Company"
        self.copyright = "no copyright"
        self.name = "bespin"

        
manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
  />
  <description>%(prog)s</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel
            level="asInvoker"
            uiAccess="false">
        </requestedExecutionLevel>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.21022.8"
            processorArchitecture="x86"
            publicKeyToken="1fc8b3b9a1e18e3b">
      </assemblyIdentity>
    </dependentAssembly>
  </dependency>
  <dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
  </dependency>
</assembly>
'''

RT_MANIFEST = 24

bespin = Target(
    # used for the versioninfo resource
    description = "A swtor datamining tool",

    # what to build
    script = "bespin.py",
    other_resources = [(RT_MANIFEST, 1, manifest_template % dict(prog="test_wx"))],
##    icon_resources = [(1, "icon.ico")],
    dest_base = "bespin")

bespin_console = Target(
    # used for the versioninfo resource
    description = "A swtor datamining tool with console",

    # what to build
    script = "bespin.py",
    other_resources = [(RT_MANIFEST, 1, manifest_template % dict(prog="test_wx"))],
##    icon_resources = [(1, "icon.ico")],
    dest_base = "bespin_console")

excludes = []
dll_excludes = ['MSVCP90.dll']

setup(
    options = {"py2exe": {"compressed": 1,
                          "optimize": 2,
                          "bundle_files": 1,
                          "excludes": excludes,
                          "dll_excludes": dll_excludes}},
    zipfile = None,

    console = [bespin_console],
    windows = [bespin],
    )
