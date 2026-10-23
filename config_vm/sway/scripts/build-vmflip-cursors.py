#!/usr/bin/env python3
"""Build a vertically flipped Xcursor theme for virtio-gpu-gl.

Host QEMU/virgl draws hardware cursors upside-down. Feeding it a pre-flipped
theme cancels that so a single hardware cursor appears upright.

Hotspot calibration (guest screen px at XCURSOR_SIZE=48, 2026-10-22):
  mean dy(click - target) was about +22.5px with tip-aligned flipped hotspots
  (plus a 3px nudge). That screen delta is mapped into each frame's pixel
  space and subtracted from the tip-aligned yhot.

Prefer a host QEMU/virglrenderer update when available.

Usage:
  python3 ~/.config/sway/scripts/build-vmflip-cursors.py
"""
from __future__ import annotations

import os
import pathlib
import shutil
import struct
import sys

SRC = pathlib.Path("/usr/share/icons/oxy-red-argentina")
DST = pathlib.Path.home() / ".icons" / "oxy-red-argentina-vmflip"
XCURSOR_IMAGE_TYPE = 0xFFFD0002

# Seat / env should use this size so the buffer mapping matches calibration.
DISPLAY_SIZE = 48
# Extra subtract from tip-aligned yhot, in screen pixels at DISPLAY_SIZE.
# 3 (earlier nudge while measuring) + 22.5 (measured remaining dy).
YHOT_SCREEN_NUDGE = 3 + 22.5


def flip_xcursor(data: bytes) -> bytes:
    magic, header_size, version, ntoc = struct.unpack_from("<IIII", data, 0)
    if magic.to_bytes(4, "little") != b"Xcur":
        raise ValueError("not an xcursor")

    toc = [
        struct.unpack_from("<III", data, header_size + i * 12) for i in range(ntoc)
    ]

    images = []
    for typ, subtype, position in toc:
        if typ != XCURSOR_IMAGE_TYPE:
            raise ValueError(f"unsupported chunk type {typ:#x}")
        (
            size,
            _typ2,
            _subtype2,
            version2,
            width,
            height,
            xhot,
            yhot,
            delay,
        ) = struct.unpack_from("<IIIIIIIII", data, position)
        pix_off = position + size
        nbytes = width * height * 4
        pixels = bytearray(data[pix_off : pix_off + nbytes])
        row = width * 4
        flipped = bytearray(nbytes)
        for y in range(height):
            src_y = height - 1 - y
            flipped[y * row : (y + 1) * row] = pixels[src_y * row : (src_y + 1) * row]
        dy_buf = round(YHOT_SCREEN_NUDGE * height / DISPLAY_SIZE)
        yhot_new = height - 1 - yhot - dy_buf
        yhot_new = max(0, min(height - 1, yhot_new))
        images.append(
            {
                "subtype": subtype,
                "width": width,
                "height": height,
                "xhot": xhot,
                "yhot": yhot_new,
                "delay": delay,
                "pixels": flipped,
                "version": version2,
            }
        )

    out = bytearray()
    new_header_size = 16
    out += struct.pack("<IIII", magic, new_header_size, version, ntoc)
    toc_off = len(out)
    out += b"\x00" * (ntoc * 12)

    new_toc = []
    for img in images:
        pos = len(out)
        hdr_size = 36
        out += struct.pack(
            "<IIIIIIIII",
            hdr_size,
            XCURSOR_IMAGE_TYPE,
            img["subtype"],
            img["version"],
            img["width"],
            img["height"],
            img["xhot"],
            img["yhot"],
            img["delay"],
        )
        out += img["pixels"]
        new_toc.append((XCURSOR_IMAGE_TYPE, img["subtype"], pos))

    for i, (typ, subtype, pos) in enumerate(new_toc):
        struct.pack_into("<III", out, toc_off + i * 12, typ, subtype, pos)
    return bytes(out)


def main() -> int:
    if not SRC.is_dir():
        print(f"source theme missing: {SRC}", file=sys.stderr)
        return 1

    if DST.exists():
        shutil.rmtree(DST)
    (DST / "cursors").mkdir(parents=True)

    index = (SRC / "index.theme").read_text()
    (DST / "index.theme").write_text(
        index.replace("oxy-red-argentina", "oxy-red-argentina-vmflip")
    )

    n_files = n_links = 0
    for entry in sorted((SRC / "cursors").iterdir()):
        dest = DST / "cursors" / entry.name
        if entry.is_symlink():
            dest.symlink_to(os.readlink(entry))
            n_links += 1
        elif entry.is_file():
            dest.write_bytes(flip_xcursor(entry.read_bytes()))
            n_files += 1

    print(f"Wrote {n_files} flipped cursors, {n_links} symlinks -> {DST}")
    print(f"YHOT_SCREEN_NUDGE={YHOT_SCREEN_NUDGE} at DISPLAY_SIZE={DISPLAY_SIZE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
