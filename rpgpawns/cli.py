"""CLI front-end for rpgpawns."""

from __future__ import annotations

import argparse

from PIL import Image

from rpgpawns.pawn import COLLAGE_MARGIN_MM, DPI, PawnSize, make_collage, make_pawn

_SIZE_NAMES = {s.value for s in PawnSize}


def parse_image_args(
    args: list[str],
) -> list[tuple[str, PawnSize, int]]:
    """Parse image arguments in ``path[:size][:count]`` format.

    Each argument is a single string that encodes the image path and
    optional size and count separated by colons.  Valid forms::

        foo.jpg
        foo.jpg:2
        foo.jpg:medium
        foo.jpg:medium:2

    Parameters
    ----------
    args:
        List of positional arguments.

    Returns
    -------
    List of ``(path, size, count)`` tuples.

    Raises
    ------
    ValueError
        If an argument has a count < 1 or specifies an unknown size name.
    """
    result: list[tuple[str, PawnSize, int]] = []
    for arg in args:
        # Windows paths start with a drive letter like "C:\", which contains a
        # colon that must not be treated as a path/modifier separator.
        if len(arg) >= 2 and arg[1] == ":" and arg[0].isalpha():
            drive, tail_arg = arg[:2], arg[2:]
        else:
            drive, tail_arg = "", arg
        parts = tail_arg.rsplit(":", 2)
        if drive:
            parts[0] = drive + parts[0]

        if len(parts) == 3:
            path, size_str, count_str = parts
        elif len(parts) == 2:
            path = parts[0]
            tail = parts[1]
            if tail.isdigit():
                size_str = None
                count_str = tail
            elif tail.lower() in _SIZE_NAMES:
                size_str = tail
                count_str = None
            else:
                # Not a recognised modifier — treat entire arg as a path
                path = arg
                size_str = None
                count_str = None
        else:
            path = arg
            size_str = None
            count_str = None

        if size_str is not None:
            if size_str.lower() not in _SIZE_NAMES:
                raise ValueError(
                    f"Unknown size '{size_str}' in '{arg}'. "
                    f"Valid sizes: {', '.join(sorted(_SIZE_NAMES))}"
                )
            size = PawnSize(size_str.lower())
        else:
            size = PawnSize.MEDIUM

        if count_str is not None:
            count = int(count_str)
            if count < 1:
                raise ValueError(f"Count must be at least 1, got '{arg}'")
        else:
            count = 1

        result.append((path, size, count))
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
        metavar="IMAGE",
        help=(
            "Image files with optional size and count: "
            "IMAGE[:SIZE][:COUNT]. "
            "Sizes: small, medium (default), large, huge. "
            "Examples: foo.jpg, foo.jpg:2, foo.jpg:large, foo.jpg:large:2."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output.pdf",
        help="Output file path (default: output.pdf).",
    )
    parser.add_argument(
        "-m",
        "--margin",
        type=float,
        default=COLLAGE_MARGIN_MM,
        help=f"Page margin in millimeters (default: {COLLAGE_MARGIN_MM}).",
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

    pages = make_collage(pawns, margin_mm=ns.margin)

    output_lower = ns.output.lower()
    if len(pages) > 1 and not output_lower.endswith(".pdf"):
        parser.error(
            f"Multiple pages generated but output format does not support "
            f"multi-page files: {ns.output}"
        )

    if output_lower.endswith(".pdf"):
        pages[0].save(
            ns.output,
            dpi=(DPI, DPI),
            save_all=True,
            append_images=pages[1:],
        )
    else:
        pages[0].save(ns.output, dpi=(DPI, DPI))


if __name__ == "__main__":
    main()  # pragma: no cover
