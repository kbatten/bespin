import StringIO
import os
import struct
import sys


data = StringIO.StringIO("\x00\x00\xc9\x01h\xc9\x00\x13\xcf@\x00\x00\x00'\xbd\xa1K\x02 \x01\x02!\xcc\x04\xb5\xe4\xd9%\x05\x03\xcb\x83\xecH\x0b\x05\x03\xcc\x02\x8c\xe2\x14\x07\x06\x18pkg.movement.npc.regular\x01\x06\x0epkg.cover.none\xcb\x08B\xdd\xb8\x06\x17pkg.wander.npc.standard\x01\x06\x16pkg.aggro.npc.interior\xcb6H-\xdb\x03\x01\xca\xea\xfcI\x07\t\x01\x01\x01\n\x07\xcf@\x00\x00\x08-\xe6\xdeX\x06\x05probe\x02\x04\x00\x00\x80?\xcc\x01\xc7+\xbe\x1d\x01\xcf\xe0\x00\xf7\x94\xc5\x91\r,\x01\x01\xcf\xe0\x00\xf7\x94\xc5\x91\r,\x01\x01\xcf\xe0\x00\xd4D\x8b\xd3\xcc\x12\x01\x01\xcf\xe0\x00\xf7\x94\xc5\x91\r,\xcb~\n<E\x01\xcf\xe0\x00W\x91\xacc\xa8\xde\xcc\x01P*\rJ\x02\xc7\x19\xbfG\xef\xc7n\xaa\xdb\xcb\x0c\x1f\xa1L\x08\x05\x03\x01\x01\x01\x01\xcb%n\x85+\x02\xcfz\xd0m\xb0:\x8d%7\xcbm\xd3\xd8\x1a\x01\xcf\xe0\x00\xce\xf0\xd1't\x8c\xcb0\xf0\xfd\xe5\x01\xcf\xe0\x00\x02$p\xf97Q\xcb$\xb8\xf0\x9f\x01\xcf\xe0\x00\xc6t\xa8\x1a\xde\xc6\xcc\x04\xc8\x9d\xc1\xfc\x01\xcf\xe0\x00\xb4\x0f\x16\xbd\xe9\x06\xcb`d\x17\xab\x05\x03\xcc\x04\x0bi< \x08\x02\t\x01\x01\xcf\xd9\xad\xae\xc5\xf2u\xd8F\x04\x03\xcf@\x00\x00\x11\\\xe8t\x88\x02\xce\x03w\x11\x00\x00\x00\x00\x01\x06\x07str.npc\x01\x06\x16Imperial Service Droid")

#print [data]

# short string - 0x06 [length] [data]
# short int    - 0xc9 [data]x2
# int          - 0xcb [data]x4
# double       - 0xce [data]x8 ? 8 bytes seems to work, but double doesn't
# double       - 0xcf [data]x8 ? 8 bytes seems to work, but double doesn't

final = ""

# skip 0x00 0x00
data.seek(2)

COLOR_TOKEN = "\033[96m"
COLOR_C9 = "\033[95m"
COLOR_CB = "\033[94m"
COLOR_CC = "\033[94m"
COLOR_CE = "\033[93m"
COLOR_CF = "\033[92m"
COLOR_STR = "\033[91m"
COLOR_END = "\033[0m"

def format_value(value, color):
    output = str(value)
    if color:
        output = color + output + COLOR_END
    return output

def format_token(c, known=True):
    if known:
        output = COLOR_TOKEN + "\\x" + c.encode("hex") + COLOR_END
    else:
        output = "\\x" + c.encode("hex")
    return output

while True:
    # read item id
    c = data.read(1)
    if len(c) == 0:
        break

    l = None
    v = None
    known = False
    color = None
    if ord(c) == 0xc9:
        v = struct.unpack("< H", data.read(2))[0]
        known = True
        color = COLOR_C9
    elif ord(c) == 0xcb:
        v = struct.unpack("< I", data.read(4))[0]
        known = True
        color = COLOR_CB
    elif ord(c) == 0xcc:
        v = struct.unpack("< I", data.read(4))[0]
        known = True
        color = COLOR_CC
    elif ord(c) == 0xce:
        v = struct.unpack("< d", data.read(8))[0]
        known = True
        color = COLOR_CE
    elif ord(c) == 0xcf:
        v = struct.unpack("< d", data.read(8))[0]
        known = True
        color = COLOR_CF
    elif ord(c) == 0x06:
        l = data.read(1)
        v = data.read(ord(l))
        known = True
        color = COLOR_STR

    final += format_token(c, known)
    if l:
        final += format_token(l, known)
    if v:
        final += format_value(v, color)


print final
