"""Convert an image to a paper-cut pawn for board games and tabletop RPGs."""

from __future__ import annotations

import enum
from collections.abc import Sequence

from PIL import Image, ImageDraw

DPI = 300
MM_PER_INCH = 25.4
MIN_PADDING_MM = 10.0
BORDER_COLOR = (192, 192, 192)
BORDER_WIDTH_PX = 1

A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0
COLLAGE_MARGIN_MM = 10.0
COLLAGE_SPACING_MM = 10.0


class PawnSize(enum.Enum):
    """Pawn size presets.

    Each size defines the maximum width and single-image height for the
    pawn.  See :data:`PAWN_SPECS` for the exact dimensions.
    """

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"


PAWN_SPECS: dict[PawnSize, tuple[float, float]] = {
    PawnSize.SMALL: (20.0, 28.0),
    PawnSize.MEDIUM: (28.0, 48.0),
    PawnSize.LARGE: (48.0, 63.0),
    PawnSize.HUGE: (75.0, 99.0),
}
"""Maximum width and single-image height (mm) for each :class:`PawnSize`."""


def _pawn_dims_mm(pawn: Image.Image) -> tuple[float, float]:
    """Return (width_mm, height_mm) of a pawn image."""
    return (
        pawn.width * MM_PER_INCH / DPI,
        pawn.height * MM_PER_INCH / DPI,
    )


def mm_to_px(mm: float, dpi: int = DPI) -> int:
    """Convert millimeters to pixels at the given DPI."""
    return round(mm * dpi / MM_PER_INCH)


def make_pawn(
    input_image: Image.Image,
    size: PawnSize = PawnSize.MEDIUM,
) -> Image.Image:
    """Convert an image to a paper-cut pawn image.

    The output image has the following properties:

    - 300 DPI
    - The original image is scaled to fit within the dimensions specified by
      *size* (see :data:`PAWN_SPECS`), preserving aspect ratio
    - The image is duplicated along its top edge, mirrored vertically
    - White padding (at least :data:`PADDING_MM`) is added at the top and
      bottom so that all pawns of the same *size* have identical total height
    - A thin faint grey border is drawn around the entire image

    Parameters
    ----------
    input_image:
        Input PIL Image in any mode and resolution.
    size:
        Pawn size preset.  Defaults to :attr:`PawnSize.MEDIUM`.

    Returns
    -------
    PIL Image in RGB mode at 300 DPI.
    """
    max_w_mm, max_h_mm = PAWN_SPECS[size]

    # Composite onto white background for images with transparency
    if input_image.mode == "RGBA":
        background = Image.new("RGB", input_image.size, (255, 255, 255))
        background.paste(input_image, mask=input_image.split()[3])
        img = background
    elif input_image.mode != "RGB":
        img = input_image.convert("RGB")
    else:
        img = input_image.copy()

    # Calculate target pixel dimensions
    max_w_px = mm_to_px(max_w_mm)
    max_h_px = mm_to_px(max_h_mm)

    # Scale to fit within max dimensions, preserving aspect ratio
    orig_w, orig_h = img.size
    scale = min(max_w_px / orig_w, max_h_px / orig_h)
    new_w = min(round(orig_w * scale), max_w_px)
    new_h = min(round(orig_h * scale), max_h_px)

    scaled = img.resize((new_w, new_h), Image.LANCZOS)

    # Create vertically mirrored copy
    mirrored = scaled.transpose(Image.FLIP_TOP_BOTTOM)

    # Calculate canvas dimensions.
    # Padding is at least PADDING_MM, but increases when the scaled image
    # doesn't fill max_h so that all pawns of the same size share the same
    # total height: (min_padding + max_h) * 2.
    min_padding_px = mm_to_px(MIN_PADDING_MM)
    canvas_w = new_w
    canvas_h = (min_padding_px + max_h_px) * 2
    padding_px = (canvas_h - new_h * 2) // 2

    # Create white canvas and paste images
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    canvas.paste(mirrored, (0, padding_px))
    canvas.paste(scaled, (0, padding_px + new_h))

    # Draw thin faint grey border
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(
        [0, 0, canvas_w - 1, canvas_h - 1],
        outline=BORDER_COLOR,
        width=BORDER_WIDTH_PX,
    )

    # Set DPI and pawn size metadata
    canvas.info["dpi"] = (DPI, DPI)
    canvas.info["pawn_size"] = size

    return canvas


# ---------------------------------------------------------------------------
# Collage layout — column-based packing
# ---------------------------------------------------------------------------


def make_collage(pawns: Sequence[Image.Image]) -> Image.Image:
    """Arrange pawn images on an A4 page.

    Pawns are packed into columns from left to right.  Tallest pawns are
    placed first; shorter pawns are stacked below taller ones in the same
    column when they fit.  Pawns already include built-in top/bottom
    padding, so no extra vertical gap is added within a column.

    Parameters
    ----------
    pawns:
        Pawn images as returned by :func:`make_pawn`.  Must not be empty.

    Returns
    -------
    PIL Image in RGB mode at 300 DPI, sized to A4 (210 mm x 297 mm).

    Raises
    ------
    ValueError
        If *pawns* is empty or too many pawns to fit on a single page.
    """
    if not pawns:
        raise ValueError("pawns must not be empty")

    avail_w_mm = A4_WIDTH_MM - 2 * COLLAGE_MARGIN_MM
    avail_h_mm = A4_HEIGHT_MM - 2 * COLLAGE_MARGIN_MM
    sp = COLLAGE_SPACING_MM

    # Sort pawns tallest-first for greedy column packing
    sorted_pawns = sorted(pawns, key=lambda p: (p.height, p.width), reverse=True)

    # Each column: [col_width_mm, col_height_mm, [(pawn, y_offset_mm)]]
    columns: list[list] = []  # mutable sub-lists for in-place updates

    for pawn in sorted_pawns:
        pw_mm, ph_mm = _pawn_dims_mm(pawn)

        # Find the best existing column (least remaining space that still fits)
        best_idx = -1
        best_remaining = float("inf")
        for i, col in enumerate(columns):
            col_w, col_h = col[0], col[1]
            if col_w >= pw_mm and col_h + ph_mm <= avail_h_mm:
                remaining = avail_h_mm - col_h - ph_mm
                if remaining < best_remaining:
                    best_idx = i
                    best_remaining = remaining

        if best_idx >= 0:
            col = columns[best_idx]
            col[2].append((pawn, col[1]))
            col[1] += ph_mm
        else:
            # Start a new column
            total_w = sum(c[0] for c in columns)
            if columns:
                total_w += len(columns) * sp
            if total_w + (sp if columns else 0) + pw_mm > avail_w_mm:
                raise ValueError("Too many pawns to fit on a single A4 page")
            columns.append([pw_mm, ph_mm, [(pawn, 0.0)]])

    # Render
    page_w = mm_to_px(A4_WIDTH_MM)
    page_h = mm_to_px(A4_HEIGHT_MM)
    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    spacing_px = mm_to_px(COLLAGE_SPACING_MM)
    page = Image.new("RGB", (page_w, page_h), (255, 255, 255))

    x_px = margin_px
    for col_w_mm, _col_h_mm, entries in columns:
        col_w_px = mm_to_px(col_w_mm)
        for pawn, y_mm in entries:
            offset_x = (col_w_px - pawn.width) // 2
            y_px = margin_px + mm_to_px(y_mm)
            page.paste(pawn, (x_px + offset_x, y_px))
        x_px += col_w_px + spacing_px

    page.info["dpi"] = (DPI, DPI)
    return page
