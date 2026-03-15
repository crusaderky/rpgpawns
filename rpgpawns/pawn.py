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
BORDER_WIDTH_MM = BORDER_WIDTH_PX * MM_PER_INCH / DPI
BORDER_WHITE_THRESHOLD = 240
BORDER_WHITE_RATIO = 0.9

A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0
COLLAGE_MARGIN_MM = 5.0
COLLAGE_SPACING_MM = 2.0
AVAIL_WIDTH_MM = A4_WIDTH_MM - 2 * COLLAGE_MARGIN_MM
AVAIL_HEIGHT_MM = A4_HEIGHT_MM - 2 * COLLAGE_MARGIN_MM


class PawnSize(enum.Enum):
    """Pawn size presets.

    Each size defines the maximum width and single-image height for the
    pawn.  See :data:`PAWN_SPECS` for the exact dimensions.
    """

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"


class BorderSide(enum.Enum):
    """Side of the pawn image to test for a white border."""

    LEFT = "left"
    RIGHT = "right"


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


def has_white_border(image: Image.Image, side: BorderSide) -> bool:
    """Test whether the left or right edge of a pawn image is almost white.

    Checks the column of pixels just inside the grey border drawn by
    :func:`make_pawn` (i.e. at *x* = :data:`BORDER_WIDTH_PX` for the left
    side, or *x* = ``width - 1 - BORDER_WIDTH_PX`` for the right side).

    A pixel is considered *almost white* when every RGB channel is at least
    :data:`BORDER_WHITE_THRESHOLD`.  If the fraction of almost-white pixels
    in the column is at least :data:`BORDER_WHITE_RATIO`, the border is
    considered white and the function returns ``True``.

    Parameters
    ----------
    image:
        A pawn image as returned by :func:`make_pawn`.
    side:
        Which edge to test.

    Returns
    -------
    ``True`` if the edge column is almost entirely white.
    """
    if side is BorderSide.LEFT:
        x = BORDER_WIDTH_PX
    else:
        x = image.width - 1 - BORDER_WIDTH_PX

    total = image.height
    white_count = 0
    for y in range(total):
        r, g, b = image.getpixel((x, y))[:3]
        if (
            r >= BORDER_WHITE_THRESHOLD
            and g >= BORDER_WHITE_THRESHOLD
            and b >= BORDER_WHITE_THRESHOLD
        ):
            white_count += 1

    return white_count / total >= BORDER_WHITE_RATIO


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
    - White padding (at least :data:`MIN_PADDING_MM`) is added at the top and
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
    # Padding is at least MIN_PADDING_MM, but increases when the scaled image
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
# Collage layout — row-based packing
# ---------------------------------------------------------------------------


def _render_page(
    placements: Sequence[tuple[Image.Image, float, float]],
) -> Image.Image:
    """Render a list of (pawn, x_mm, y_mm) placements onto a blank A4 page."""
    page_w = mm_to_px(A4_WIDTH_MM)
    page_h = mm_to_px(A4_HEIGHT_MM)
    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    page = Image.new("RGB", (page_w, page_h), (255, 255, 255))

    for pawn, x_mm, y_mm in placements:
        x_px = margin_px + mm_to_px(x_mm)
        y_px = margin_px + mm_to_px(y_mm)
        page.paste(pawn, (x_px, y_px))

    page.info["dpi"] = (DPI, DPI)
    return page


def make_collage(pawns: Sequence[Image.Image]) -> list[Image.Image]:
    """Arrange pawn images on A4 pages.

    Pawns are packed into rows from top to bottom.  Tallest pawns are
    placed first; when the next pawn has a different height a new row is
    started.  Within a row, pawns are placed left to right with
    :data:`COLLAGE_SPACING_MM` between them.  Pawns already include
    built-in top/bottom padding, so no extra vertical gap is added
    between rows.

    When a new row would exceed the available page height, a new vertical
    band is started to the right of the widest row placed so far.

    If the pawns do not fit on a single page, additional pages are
    created automatically.

    Parameters
    ----------
    pawns:
        Pawn images as returned by :func:`make_pawn`.  Must not be empty.

    Returns
    -------
    List of PIL Images in RGB mode at 300 DPI, each sized to A4
    (210 mm x 297 mm).

    Raises
    ------
    ValueError
        If *pawns* is empty.
    """
    if not pawns:
        raise ValueError("pawns must not be empty")

    # Sort pawns tallest-first for grouped row packing
    sorted_pawns = sorted(pawns, key=lambda p: (p.height, p.width), reverse=True)

    band_x = 0.0  # left edge of current band (relative to margin)
    cursor_x = 0.0  # current x position (relative to margin)
    cursor_y = 0.0  # current y position (relative to margin)
    row_h = 0.0  # height of current row
    max_right = 0.0  # rightmost pawn edge across all placements
    prev_in_row: Image.Image | None = None  # last placed pawn in current row

    placements: list[tuple[Image.Image, float, float]] = []
    pages: list[Image.Image] = []

    for pawn in sorted_pawns:
        pw_mm, ph_mm = _pawn_dims_mm(pawn)

        # If height changed from current row, start a new row
        if row_h > 0 and abs(ph_mm - row_h) > 0.01:
            cursor_y += row_h
            cursor_x = band_x
            row_h = 0.0
            prev_in_row = None

        # Add gap from previous pawn in the row: overlap borders when
        # either neighbour has an almost-white edge, otherwise use the
        # standard spacing.
        if prev_in_row is not None:
            if has_white_border(prev_in_row, BorderSide.RIGHT) or has_white_border(
                pawn, BorderSide.LEFT
            ):
                cursor_x -= BORDER_WIDTH_MM
            else:
                cursor_x += COLLAGE_SPACING_MM

        # If doesn't fit horizontally in current row, start a new row
        if prev_in_row is not None and cursor_x + pw_mm > AVAIL_WIDTH_MM:
            cursor_y += row_h - BORDER_WIDTH_MM
            cursor_x = band_x
            row_h = 0.0
            prev_in_row = None

        # If doesn't fit vertically, start a new band
        if cursor_y + ph_mm > AVAIL_HEIGHT_MM:
            band_x = max_right + COLLAGE_SPACING_MM
            cursor_x = band_x
            cursor_y = 0.0
            row_h = 0.0
            prev_in_row = None

        # If doesn't fit on current page, finalize it and start a new page
        if cursor_x + pw_mm > AVAIL_WIDTH_MM or cursor_y + ph_mm > AVAIL_HEIGHT_MM:
            pages.append(_render_page(placements))
            placements = []
            band_x = 0.0
            cursor_x = 0.0
            cursor_y = 0.0
            row_h = 0.0
            max_right = 0.0
            prev_in_row = None

        placements.append((pawn, cursor_x, cursor_y))
        cursor_x += pw_mm
        row_h = max(row_h, ph_mm)
        max_right = max(max_right, cursor_x)
        prev_in_row = pawn

    # Render final page
    pages.append(_render_page(placements))
    return pages
