"""CLI front-end for rpgpawns."""

from __future__ import annotations

import argparse
import re
import sys

from PIL import Image

from rpgpawns.pawn import DPI, make_collage, make_pawn

_MULTIPLIER_RE = re.compile(r"^x(\d+)$", re.IGNORECASE)


def parse_image_args(args: list[str]) -> list[tuple[str, int]]:
    """Parse interleaved image paths and ``xN`` multipliers.

    Parameters
    ----------
    args:
        List of positional arguments, e.g. ``["foo.jpg", "bar.png", "x2"]``.

    Returns
    -------
    List of ``(path, count)`` tuples.

    Raises
    ------
    ValueError
        If a multiplier has no preceding image or has a count < 1.
    """
    result: list[tuple[str, int]] = []
    for arg in args:
        m = _MULTIPLIER_RE.match(arg)
        if m:
            if not result:
                raise ValueError(
                    f"Multiplier '{arg}' has no preceding image file"
                )
            count = int(m.group(1))
            if count < 1:
                raise ValueError(
                    f"Multiplier must be at least 1, got '{arg}'"
                )
            path, _ = result[-1]
            result[-1] = (path, count)
        else:
            result.append((arg, 1))
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="rpgpawns",
        description=(
            "Convert images to paper-cut pawns for board games "
            "and tabletop RPGs."
        ),
    )
    parser.add_argument(
        "images",
        nargs="+",
        metavar="IMAGE_OR_MULTIPLIER",
        help=(
            "Image files (.jpg/.png) optionally followed by xN "
            "to replicate the pawn N times."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output.pdf",
        help="Output file path (default: output.pdf).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``rpgpawns`` command."""
    parser = build_parser()
    ns = parser.parse_args(argv)

    try:
        entries = parse_image_args(ns.images)
    except ValueError as exc:
        parser.error(str(exc))

    pawns: list[Image.Image] = []
    for path, count in entries:
        with Image.open(path) as img:
            pawn = make_pawn(img)
        for _ in range(count):
            pawns.append(pawn)

    collage = make_collage(pawns)
    collage.save(ns.output, dpi=(DPI, DPI))


if __name__ == "__main__":
    main()
