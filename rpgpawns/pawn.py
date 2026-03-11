"""Convert an image to a paper-cut pawn for board games and tabletop RPGs."""

from __future__ import annotations

from collections.abc import Sequence

from PIL import Image, ImageDraw

DPI = 300
MM_PER_INCH = 25.4
MAX_WIDTH_MM = 28.0
MAX_HEIGHT_MM = 48.0
PADDING_MM = 4.0
BORDER_COLOR = (192, 192, 192)
BORDER_WIDTH_PX = 1

A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0
COLLAGE_MARGIN_MM = 10.0
COLLAGE_SPACING_MM = 10.0

# Maximum pawn dimensions as produced by make_pawn
_MAX_PAWN_WIDTH_MM = MAX_WIDTH_MM
_MAX_PAWN_HEIGHT_MM = PADDING_MM * 2 + MAX_HEIGHT_MM * 2

# Grid capacity
COLLAGE_COLS = int(
    (A4_WIDTH_MM - 2 * COLLAGE_MARGIN_MM + COLLAGE_SPACING_MM)
    / (_MAX_PAWN_WIDTH_MM + COLLAGE_SPACING_MM)
)
COLLAGE_ROWS = int(
    (A4_HEIGHT_MM - 2 * COLLAGE_MARGIN_MM + COLLAGE_SPACING_MM)
    / (_MAX_PAWN_HEIGHT_MM + COLLAGE_SPACING_MM)
)
COLLAGE_MAX_PAWNS = COLLAGE_COLS * COLLAGE_ROWS


def mm_to_px(mm: float, dpi: int = DPI) -> int:
    """Convert millimeters to pixels at the given DPI."""
    return round(mm * dpi / MM_PER_INCH)


def make_pawn(input_image: Image.Image) -> Image.Image:
    """Convert an image to a paper-cut pawn image.

    The output image has the following properties:

    - 300 DPI
    - The original image is scaled to fit within 28mm x 48mm, preserving
      aspect ratio
    - The image is duplicated along its top edge, mirrored vertically
    - 4mm of white padding is added at the top and bottom, for a maximum
      total height of 104mm
    - A thin faint grey border is drawn around the entire image

    Parameters
    ----------
    input_image:
        Input PIL Image in any mode and resolution.

    Returns
    -------
    PIL Image in RGB mode at 300 DPI.
    """
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
    max_w_px = mm_to_px(MAX_WIDTH_MM)
    max_h_px = mm_to_px(MAX_HEIGHT_MM)

    # Scale to fit within max dimensions, preserving aspect ratio
    orig_w, orig_h = img.size
    scale = min(max_w_px / orig_w, max_h_px / orig_h)
    new_w = min(round(orig_w * scale), max_w_px)
    new_h = min(round(orig_h * scale), max_h_px)

    scaled = img.resize((new_w, new_h), Image.LANCZOS)

    # Create vertically mirrored copy
    mirrored = scaled.transpose(Image.FLIP_TOP_BOTTOM)

    # Calculate canvas dimensions
    padding_px = mm_to_px(PADDING_MM)
    canvas_w = new_w
    canvas_h = padding_px + new_h + new_h + padding_px

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

    # Set DPI metadata
    canvas.info["dpi"] = (DPI, DPI)

    return canvas


def make_collage(pawns: Sequence[Image.Image]) -> Image.Image:
    """Arrange pawn images on an A4 page.

    Images are placed left-to-right along the short side of the page first,
    then top-to-bottom, in a grid with at least 10mm spacing and 10mm margin.

    Parameters
    ----------
    pawns:
        Pawn images as returned by :func:`make_pawn`. Must contain between
        1 and :data:`~rpgpawns.pawn.COLLAGE_MAX_PAWNS` images (inclusive).

    Returns
    -------
    PIL Image in RGB mode at 300 DPI, sized to A4 (210mm x 297mm).

    Raises
    ------
    ValueError
        If ``pawns`` is empty or contains more than
        :data:`~rpgpawns.pawn.COLLAGE_MAX_PAWNS` images.
    """
    if len(pawns) == 0:
        raise ValueError("pawns must not be empty")
    if len(pawns) > COLLAGE_MAX_PAWNS:
        raise ValueError(
            f"Too many pawns: got {len(pawns)}, maximum is {COLLAGE_MAX_PAWNS}"
        )

    page_w = mm_to_px(A4_WIDTH_MM)
    page_h = mm_to_px(A4_HEIGHT_MM)
    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    spacing_px = mm_to_px(COLLAGE_SPACING_MM)
    cell_w = mm_to_px(_MAX_PAWN_WIDTH_MM)
    cell_h = mm_to_px(_MAX_PAWN_HEIGHT_MM)

    page = Image.new("RGB", (page_w, page_h), (255, 255, 255))

    for i, pawn in enumerate(pawns):
        col = i % COLLAGE_COLS
        row = i // COLLAGE_COLS

        # Top-left corner of the grid cell
        cell_x = margin_px + col * (cell_w + spacing_px)
        cell_y = margin_px + row * (cell_h + spacing_px)

        # Center pawn within the cell
        offset_x = (cell_w - pawn.width) // 2
        offset_y = (cell_h - pawn.height) // 2

        page.paste(pawn, (cell_x + offset_x, cell_y + offset_y))

    page.info["dpi"] = (DPI, DPI)

    return page
