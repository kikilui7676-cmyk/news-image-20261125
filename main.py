#!/usr/bin/env python3
"""news-image-20261125 v6 entrypoint.

Copies the pre-rendered entry.png (1024x1024, built in-session) to
$MAKEFUN_OUTPUT_DIR/entry.png, then verifies the copy: SHA-256 match,
PNG signature, IHDR dimensions 1024x1024, and size <= 1 MiB.
Standard library only. Deterministic: every run writes identical bytes.
"""

import hashlib
import os
import shutil
import struct
import sys

EXPECTED_SHA256 = "a4e248a1cc314b27303293e840646aca1a8de9b28fd0511c8a92f7b8b10bfc24"
MAX_BYTES = 1024 * 1024
WIDTH = HEIGHT = 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print(f"main.py: error: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_png(path):
    if not os.path.isfile(path):
        fail(f"{path}: file not found")
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) > MAX_BYTES:
        fail(f"{path}: {len(data)} bytes exceeds 1 MiB limit")
    if data[:8] != PNG_SIGNATURE:
        fail(f"{path}: bad PNG signature")
    if data[12:16] != b"IHDR":
        fail(f"{path}: first chunk is not IHDR")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (WIDTH, HEIGHT):
        fail(f"{path}: dimensions {width}x{height}, expected 1024x1024")
    bit_depth, color_type = data[24], data[25]
    if bit_depth != 8 or color_type != 2:
        fail(f"{path}: bit depth {bit_depth}, color type {color_type}; expected 8 / 2 (RGB)")
    return data


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        fail("MAKEFUN_OUTPUT_DIR is not set")
    data = check_png(source)
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        fail(f"entry.png sha256 mismatch: {digest}")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    shutil.copyfile(source, dest)
    copied = check_png(dest)
    if hashlib.sha256(copied).hexdigest() != EXPECTED_SHA256:
        fail("copied entry.png sha256 mismatch")
    print(f"entry.png: 1024x1024, {len(data)} bytes, sha256 {digest}")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
