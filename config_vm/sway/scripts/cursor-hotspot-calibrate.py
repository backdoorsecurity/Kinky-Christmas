#!/usr/bin/env python3
"""Fullscreen grid to measure cursor hotspot offset under virtio-gpu.

Aim the *visual tip* of the pointer at a green crosshair, then click.
The tool records click − target. After a few samples it prints the mean
offset so we can adjust the vmflip theme hotspots.

Keys:
  Esc / q  — quit
  c        — clear samples
"""
from __future__ import annotations

import statistics
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402


CELL = 100
TARGETS = [
    (200, 200),
    (640, 200),
    (1080, 200),
    (200, 400),
    (640, 400),
    (1080, 400),
    (200, 600),
    (640, 600),
    (1080, 600),
]


class Calibrator(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="Cursor hotspot calibrator")
        self.connect("destroy", Gtk.main_quit)
        self.connect("key-press-event", self.on_key)
        self.fullscreen()

        self.samples: list[tuple[int, int]] = []
        self.last_click: tuple[int, int] | None = None
        self.last_target: tuple[int, int] | None = None

        self.area = Gtk.DrawingArea()
        self.area.connect("draw", self.on_draw)
        self.area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK
        )
        self.area.connect("button-press-event", self.on_click)
        self.add(self.area)
        self.show_all()

    def nearest_target(self, x: float, y: float) -> tuple[int, int]:
        # Prefer the last target when the click is still close to it so
        # repeated clicks on the same crosshair do not jump to a neighbor.
        if self.last_target is not None:
            tx, ty = self.last_target
            if (tx - x) ** 2 + (ty - y) ** 2 <= 40 ** 2:
                return self.last_target
        return min(TARGETS, key=lambda t: (t[0] - x) ** 2 + (t[1] - y) ** 2)

    def on_click(self, _widget, event) -> bool:
        if event.button != 1:
            return False
        cx, cy = int(event.x), int(event.y)
        tx, ty = self.nearest_target(cx, cy)
        dx, dy = cx - tx, cy - ty
        self.samples.append((dx, dy))
        self.last_click = (cx, cy)
        self.last_target = (tx, ty)
        print(
            f"target=({tx},{ty}) click=({cx},{cy}) delta=({dx:+d},{dy:+d})  "
            f"n={len(self.samples)}",
            flush=True,
        )
        if len(self.samples) >= 3:
            mdx = statistics.mean(d for d, _ in self.samples)
            mdy = statistics.mean(d for _, d in self.samples)
            print(
                f"MEAN offset click-target: ({mdx:+.1f},{mdy:+.1f})  "
                f"— apply yhot adjustment by {-mdy:+.1f}px (guest buffer)",
                flush=True,
            )
        self.area.queue_draw()
        return True

    def on_key(self, _widget, event) -> bool:
        key = Gdk.keyval_name(event.keyval)
        if key in ("Escape", "q", "Q"):
            if self.samples:
                mdx = statistics.mean(d for d, _ in self.samples)
                mdy = statistics.mean(d for _, d in self.samples)
                print(
                    f"FINAL mean offset (click - target): ({mdx:+.1f},{mdy:+.1f})",
                    flush=True,
                )
            Gtk.main_quit()
            return True
        if key in ("c", "C"):
            self.samples.clear()
            self.last_click = self.last_target = None
            print("cleared samples", flush=True)
            self.area.queue_draw()
            return True
        return False

    def on_draw(self, _widget, cr) -> bool:
        alloc = self.area.get_allocation()
        w, h = alloc.width, alloc.height
        cr.set_source_rgb(0.08, 0.08, 0.1)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # grid
        cr.set_source_rgba(0.25, 0.25, 0.3, 1)
        cr.set_line_width(1)
        for x in range(0, w, CELL):
            cr.move_to(x, 0)
            cr.line_to(x, h)
        for y in range(0, h, CELL):
            cr.move_to(0, y)
            cr.line_to(w, y)
        cr.stroke()

        # coordinate labels
        cr.set_source_rgb(0.55, 0.55, 0.6)
        cr.select_font_face("Sans")
        cr.set_font_size(12)
        for x in range(0, w, CELL):
            for y in range(0, h, CELL):
                cr.move_to(x + 4, y + 14)
                cr.show_text(f"{x},{y}")

        # targets
        for tx, ty in TARGETS:
            cr.set_source_rgb(0.2, 0.9, 0.3)
            cr.set_line_width(2)
            cr.move_to(tx - 18, ty)
            cr.line_to(tx + 18, ty)
            cr.move_to(tx, ty - 18)
            cr.line_to(tx, ty + 18)
            cr.stroke()
            cr.arc(tx, ty, 3, 0, 6.28)
            cr.fill()

        # last click
        if self.last_click:
            cx, cy = self.last_click
            cr.set_source_rgb(1.0, 0.3, 0.2)
            cr.arc(cx, cy, 6, 0, 6.28)
            cr.fill()
            if self.last_target:
                tx, ty = self.last_target
                cr.set_line_width(1.5)
                cr.move_to(tx, ty)
                cr.line_to(cx, cy)
                cr.stroke()

        # instructions
        cr.set_source_rgb(0.95, 0.95, 0.7)
        cr.set_font_size(16)
        cr.move_to(24, 36)
        cr.show_text(
            "Aim the VISUAL TIP at a green crosshair, then click.  Esc=quit  c=clear"
        )
        if self.samples:
            mdx = statistics.mean(d for d, _ in self.samples)
            mdy = statistics.mean(d for _, d in self.samples)
            cr.move_to(24, 60)
            cr.show_text(
                f"samples={len(self.samples)}  mean Δ(click−target)=({mdx:+.1f},{mdy:+.1f})"
            )
        return False


def main() -> int:
    Calibrator()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
