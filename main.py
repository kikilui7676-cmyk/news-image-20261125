#!/usr/bin/env python3
"""news-image-20261125 v5 entrypoint.

The broadsheet is rendered at build time and shipped as entry.png:
68 stories from Wednesday 25 November 2026, 10 regions, 25+ drawn
elements, a UTC timeline and a DATE CHECK audit. This program only
delivers it: it checks the image against the kit gates (1024x1024,
and proves the copy is byte-identical. Standard library only, so it
runs the same way in the grader image as it does locally.
"""

import hashlib
import os
import shutil
import struct
import sys

IMAGE = "entry.png"
LIMIT_BYTES = 1_048_576
EXPECTED_SIZE = (1024, 1024)


def _digest(path):
    total = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1 << 20)
            if not block:
                break
            total.update(block)
    return total.hexdigest()


def _dimensions(path):
    with open(path, "rb") as handle:
        prefix = handle.read(33)
    if prefix[:8] != b"\x89PNG\r\n\x1a\n" or prefix[12:16] != b"IHDR":
        raise ValueError("entry.png is not a PNG with an IHDR chunk")
    width, height = struct.unpack(">II", prefix[16:24])
    return width, height


def run():
    target = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not target:
        print("MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 2
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, IMAGE)
    if not os.path.isfile(source):
        print("entry.png missing next to main.py", file=sys.stderr)
        return 2
    width, height = _dimensions(source)
    if (width, height) != EXPECTED_SIZE:
        print("bad size: %dx%d, want 1024x1024" % (width, height),
              file=sys.stderr)
        return 1
    nbytes = os.path.getsize(source)
    if nbytes >= LIMIT_BYTES:
        print("entry.png too big: %d bytes" % nbytes, file=sys.stderr)
        return 1
    want = _digest(source)
    os.makedirs(target, exist_ok=True)
    dest = os.path.join(target, IMAGE)
    shutil.copyfile(source, dest)
    got = _digest(dest)
    if got != want:
        print("copy mismatch", file=sys.stderr)
        return 1
    print("entry.png %dx%d, %d bytes, sha256 %s" % (width, height, nbytes, want))
    print("delivered to %s (verified byte-identical)" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(run())
