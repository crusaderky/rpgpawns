"""CLI front-end for rpgpawns."""

from __future__ import annotations

import argparse
import re

from PIL import Image

from rpgpawns.pawn import DPI, PawnSize, make_collage, make_pawn

_SIZE_NAMES = {s.value for s in PawnSize}

# Matches modifiers like "small:2", "large", "3", "medium:4"
_MODIFIER_RE = re.compile(
    r"^(?:(?P<size>[a-z]+):(?P<count>\d+)"  # size:count
    r"|(?P<size_only>[a-z]+)"  # size alone
    r"|(?P<count_only>\d+))$",  # count alone
    re.IGNORECASE,
)


def parse_image_args(
    args: list[str],
) -> list[tuple[str, PawnSize, int]]:
    """Parse interleaved image paths and ``[size][:count]`` modifiers.

    Parameters
    ----------
    args:
        List of positional arguments, e.g.
        ``["foo.jpg", "small:2", "bar.png", "large"]``.

    Returns
    -------
    List of ``(path, size, count)`` tuples.

    Raises
    ------
    ValueError
        If a modifier has no preceding image, has a count < 1, or
        specifies an unknown size name.
    """
    result: list[tuple[str, PawnSize, int]] = []
    for arg in args:
        m = _MODIFIER_RE.match(arg)
        if m and (
            m.group("size_only") in _SIZE_NAMES
            or m.group("size") in _SIZE_NAMES
            or m.group("count_only") is not None
        ):
            if not result:
                raise ValueError(
                    f"Modifier '{arg}' has no preceding image file"
                )

            size_str = m.group("size") or m.group("size_only")
            count_str = m.group("count") or m.group("count_only")

            size = PawnSize(size_str) if size_str else result[-1][1]
            count = int(count_str) if count_str else 1

            if count < 1:
                raise ValueError(f"Count must be at least 1, got '{arg}'")

            path = result[-1][0]
            result[-1] = (path, size, count)
        else:
            result.append((arg, PawnSize.MEDIUM, 1))
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="rpgpawns",
        description=(
            "Convert images to paper-cut pawns for board games and tabletop RPGs."
        ),
    )
    parser.add_argument(
        "images",
        nargs="+",
        metavar="IMAGE_OR_MODIFIER",
        help=(
            "Image files (.jpg/.png) optionally followed by a size/count "
            "modifier: small:2, medium:3, large, huge:1, or just a count "
            "like 3 (defaults to medium)."
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
    for path, size, count in entries:
        with Image.open(path) as img:
            pawn = make_pawn(img, size=size)
        for _ in range(count):
            pawns.append(pawn)

    collage = make_collage(pawns)
    collage.save(ns.output, dpi=(DPI, DPI))


if __name__ == "__main__":
    main()
