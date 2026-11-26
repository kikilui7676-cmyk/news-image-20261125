#!/usr/bin/env python3
"""Copy the entry image to the output directory, verifying it first.

The image is rendered beforehand and shipped in this repository as
entry.png; this program does no drawing and needs no network. It checks
the file is a whole PNG of 1024x1024 pixels and at most 1 MiB, copies it
to $MAKEFUN_OUTPUT_DIR/entry.png, then verifies the copy byte for byte.
Any failed check exits non-zero so a bad entry never reaches the judge.
"""
import hashlib
import os
import struct
import sys
import zlib
from pathlib import Path

MAX_BYTES = 1048576
EXPECT_WIDTH = 1024
EXPECT_HEIGHT = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print(f"main.py: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_chunks(data):
    """Walk every PNG chunk, verifying lengths and CRCs up to IEND."""
    pos = 8
    saw_iend = False
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(data):
            fail(f"chunk {ctype!r} overruns the file")
        stored_crc = struct.unpack(">I", data[end - 4:end])[0]
        actual_crc = zlib.crc32(data[pos + 4:end - 4]) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            fail(f"chunk {ctype!r} has a bad CRC")
        if ctype == b"IEND":
            saw_iend = True
            if end != len(data):
                fail("trailing bytes after the IEND chunk")
            break
        pos = end
    if not saw_iend:
        fail("entry.png has no IEND chunk")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        fail("MAKEFUN_OUTPUT_DIR is not set")

    source = Path(__file__).resolve().parent / "entry.png"
    if not source.is_file():
        fail(f"entry.png not found next to main.py: {source}")

    data = source.read_bytes()

    if len(data) > MAX_BYTES:
        fail(f"entry.png is {len(data)} bytes, over the 1 MiB cap")
    if data[:8] != PNG_MAGIC:
        fail("entry.png does not start with the PNG signature")
    if len(data) < 24 or data[12:16] != b"IHDR":
        fail("entry.png has no IHDR chunk where a PNG must")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (EXPECT_WIDTH, EXPECT_HEIGHT):
        fail(f"entry.png is {width}x{height}, expected 1024x1024")
    check_chunks(data)

    digest = hashlib.sha256(data).hexdigest()

    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "entry.png"
    target.write_bytes(data)

    written = target.read_bytes()
    if hashlib.sha256(written).hexdigest() != digest:
        fail("written entry.png does not match the source bytes")

    print(f"main.py: OK entry.png {width}x{height} {len(data)} bytes")
    print(f"main.py: sha256 {digest}")
    print(f"main.py: wrote {target}")


if __name__ == "__main__":
    main()
