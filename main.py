#!/usr/bin/env python3
"""news-image-20261125 v3 — entry emitter.

Copies the pre-rendered broadsheet (entry.png, drawn locally with Pillow
in this repo's build session) to $MAKEFUN_OUTPUT_DIR/entry.png, then
verifies the copy byte-for-byte (SHA-256) and enforces the competition
gate: exactly 1024x1024 px and at most 1 MiB.

Stdlib only. The image is rendered at build time, not here, so this
entrypoint does no drawing and needs no third-party packages.
"""

import hashlib
import os
import shutil
import struct
import sys

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
MAX_BYTES = 1_048_576
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path):
    """Read width/height from the PNG IHDR chunk without decoding pixels."""
    with open(path, "rb") as handle:
        header = handle.read(33)
    if len(header) < 33 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file: %s" % path)
    if header[12:16] != b"IHDR":
        raise ValueError("missing PNG IHDR chunk: %s" % path)
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        print("MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 2
    if not os.path.isfile(SOURCE):
        print("missing source image: %s" % SOURCE, file=sys.stderr)
        return 2

    expected_hash = sha256_file(SOURCE)
    source_size = os.path.getsize(SOURCE)
    width, height = png_dimensions(SOURCE)
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        print("gate failed: entry.png is %dx%d, expected 1024x1024"
              % (width, height), file=sys.stderr)
        return 2
    if source_size > MAX_BYTES:
        print("gate failed: entry.png is %d bytes, over the 1 MiB limit"
              % source_size, file=sys.stderr)
        return 2

    os.makedirs(out_dir, exist_ok=True)
    if not os.path.isdir(out_dir):
        print("output path is not a directory: %s" % out_dir, file=sys.stderr)
        return 2
    target = os.path.join(out_dir, "entry.png")
    shutil.copyfile(SOURCE, target)

    actual_hash = sha256_file(target)
    actual_size = os.path.getsize(target)
    if actual_hash != expected_hash or actual_size != source_size:
        print("copy verification failed: %s" % target, file=sys.stderr)
        return 2
    target_width, target_height = png_dimensions(target)
    if (target_width, target_height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        print("gate failed: written file is %dx%d, expected 1024x1024"
              % (target_width, target_height), file=sys.stderr)
        return 2

    print("entry.png: %dx%d, %d bytes" % (width, height, actual_size))
    print("sha256: %s" % actual_hash)
    print("wrote %s" % target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
