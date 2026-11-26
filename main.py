#!/usr/bin/env python3
"""Emit the v7 front page for news-image-20261125.

The image is rendered locally beforehand and shipped in this repo as
entry.png (1024x1024, under 1 MiB). This entrypoint only copies it into
the grader's output directory and proves the copy is exact.

Stdlib only. No rendering, no fonts, no network, no clock: the two runs
a grader performs must produce byte-identical output.

Usage:
    MAKEFUN_OUTPUT_DIR=<dir> python3 main.py
Exit 0 on success; any gate failure exits non-zero with a message.
"""

import hashlib
import json
import os
import struct
import sys
import zlib

SOURCE_NAME = "entry.png"
MAX_BYTES = 1024 * 1024
MAX_EDGE = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print("main.py: FAIL: " + message, file=sys.stderr)
    return 1


def read_png(path):
    with open(path, "rb") as handle:
        return handle.read()


def check_png(blob):
    """Verify signature, IHDR size and every chunk CRC. Returns (w, h)."""
    if len(blob) < 8 or blob[:8] != PNG_MAGIC:
        raise ValueError("not a PNG file (bad magic)")
    if len(blob) > MAX_BYTES:
        raise ValueError("PNG over 1 MiB: %d bytes" % len(blob))
    offset = 8
    width = height = None
    seen_iend = False
    seen_idat = False
    first = True
    while offset + 8 <= len(blob):
        length, kind = struct.unpack(">I4s", blob[offset:offset + 8])
        if first and kind != b"IHDR":
            raise ValueError("first chunk is not IHDR")
        first = False
        start = offset + 8
        end = start + length
        if end + 4 > len(blob):
            raise ValueError("truncated chunk %r" % kind)
        stored_crc, = struct.unpack(">I", blob[end:end + 4])
        actual_crc = zlib.crc32(kind + blob[start:end]) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            raise ValueError("CRC mismatch in chunk %r" % kind)
        if kind == b"IHDR":
            width, height = struct.unpack(">II", blob[start:start + 8])
            if width > MAX_EDGE or height > MAX_EDGE:
                raise ValueError("image too large: %dx%d" % (width, height))
        if kind == b"IDAT":
            seen_idat = True
        if kind == b"IEND":
            seen_iend = True
            break
        offset = end + 4
    if width is None:
        raise ValueError("no IHDR chunk")
    if not seen_idat:
        raise ValueError("no IDAT chunk (no image data)")
    if not seen_iend:
        raise ValueError("no IEND chunk")
    return width, height


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        return fail("MAKEFUN_OUTPUT_DIR is not set")
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, SOURCE_NAME)
    if not os.path.isfile(source):
        return fail("missing " + source)
    try:
        blob = read_png(source)
        width, height = check_png(blob)
    except (OSError, ValueError) as exc:
        return fail(str(exc))
    digest = hashlib.sha256(blob).hexdigest()
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, SOURCE_NAME)
    with open(target, "wb") as handle:
        handle.write(blob)
    with open(target, "rb") as handle:
        written = handle.read()
    if hashlib.sha256(written).hexdigest() != digest:
        return fail("written copy hash differs from source")
    if len(written) != len(blob):
        return fail("written copy size differs from source")
    report = {
        "entry": SOURCE_NAME,
        "width": width,
        "height": height,
        "bytes": len(blob),
        "sha256": digest,
        "output": target,
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
