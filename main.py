#!/usr/bin/env python3
"""news-image-20261125 — emit the finished broadsheet image.

The artwork (entry.png, 1024x1024, "THE WORLD TODAY", 39 stories,
25 Nov 2026) is already rendered and shipped in this repository.
This program does exactly one thing: copy that file into
$MAKEFUN_OUTPUT_DIR and verify the copy byte-for-byte with SHA-256.

Standard library only: no Pillow, no fonts, no network, no rendering.
"""

import hashlib
import os
import shutil
import struct
import sys

SOURCE_NAME = "entry.png"
TARGET_NAME = "entry.png"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def check_png_dimensions(path):
    """Confirm the file is a PNG of the expected size (IHDR only)."""
    with open(path, "rb") as handle:
        header = handle.read(33)
    if len(header) < 33 or header[:8] != PNG_SIGNATURE:
        return "not a PNG file"
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        return f"unexpected dimensions {width}x{height}"
    return None


def main():
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not output_dir:
        print("error: MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 1

    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, SOURCE_NAME)
    if not os.path.isfile(source):
        print(f"error: source image not found: {source}", file=sys.stderr)
        return 1

    source_hash = sha256_file(source)

    os.makedirs(output_dir, exist_ok=True)
    target = os.path.join(output_dir, TARGET_NAME)
    shutil.copyfile(source, target)

    target_hash = sha256_file(target)
    if target_hash != source_hash:
        print(
            f"error: sha256 mismatch after copy: "
            f"source {source_hash} != target {target_hash}",
            file=sys.stderr,
        )
        return 1

    dimension_error = check_png_dimensions(target)
    if dimension_error is not None:
        print(f"error: copied image failed check: {dimension_error}",
              file=sys.stderr)
        return 1

    size = os.path.getsize(target)
    print(
        f"wrote {target} ({size} bytes, "
        f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}, sha256 {target_hash})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
