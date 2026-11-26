#!/usr/bin/env python3
"""news-image-20261125 v8 entrypoint.

Stdlib only. Copies the pre-rendered front page (entry.png, bundled in
this repo) into $MAKEFUN_OUTPUT_DIR and verifies it on the way out:
PNG signature, IHDR dimensions, size gate (max 1024x1024 px, max 1 MiB),
SHA-256 of the delivered copy. No rendering happens here.
"""

import hashlib
import os
import struct
import sys
import zlib

ENTRY = "entry.png"
MAX_BYTES = 1024 * 1024
MAX_SIDE = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print("entry error: " + message, file=sys.stderr)
    raise SystemExit(1)


def read_png_chunks(data):
    """Walk the chunk stream; return (width, height, saw_iend)."""
    if data[:8] != PNG_MAGIC:
        fail("entry.png is not a PNG file")
    pos = 8
    width = height = None
    saw_iend = False
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        if length > len(data) - pos - 12:
            fail("truncated PNG chunk: " + ctype.decode("latin-1", "replace"))
        body = data[pos + 8:pos + 8 + length]
        stored_crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        if zlib.crc32(ctype + body) & 0xFFFFFFFF != stored_crc:
            fail("PNG chunk CRC mismatch: " + ctype.decode("latin-1", "replace"))
        if ctype == b"IHDR":
            width, height = struct.unpack(">II", body[:8])
            depth, colour = body[8], body[9]
            if depth != 8 or colour not in (2, 6):
                fail("entry.png must be 8-bit RGB/RGBA, got depth %d colour %d"
                     % (depth, colour))
        elif ctype == b"IEND":
            saw_iend = True
            break
        pos += 12 + length
    if width is None:
        fail("PNG has no IHDR chunk")
    if not saw_iend:
        fail("PNG has no IEND chunk")
    return width, height


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        fail("MAKEFUN_OUTPUT_DIR is not set")
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, ENTRY)
    try:
        with open(source, "rb") as handle:
            data = handle.read()
    except OSError as exc:
        fail("cannot read " + ENTRY + ": " + str(exc))
    if len(data) > MAX_BYTES:
        fail("entry.png is %d bytes, over the 1 MiB limit" % len(data))
    width, height = read_png_chunks(data)
    if width > MAX_SIDE or height > MAX_SIDE:
        fail("entry.png is %dx%d, over the 1024x1024 limit" % (width, height))
    digest = hashlib.sha256(data).hexdigest()
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, ENTRY)
    with open(target, "wb") as handle:
        handle.write(data)
    with open(target, "rb") as handle:
        delivered = handle.read()
    if len(delivered) != len(data):
        fail("delivered copy is %d bytes, expected %d"
             % (len(delivered), len(data)))
    if hashlib.sha256(delivered).hexdigest() != digest:
        fail("delivered copy failed SHA-256 verification")
    print("entry.png %dx%d %d bytes sha256=%s" % (width, height, len(data), digest))
    print("delivered to " + target)


if __name__ == "__main__":
    main()
