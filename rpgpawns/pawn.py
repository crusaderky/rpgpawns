"""Convert an image to a paper-cut pawn for board games and tabletop RPGs."""

from __future__ import annotations

import enum
import math
from collections.abc import Sequence

from PIL import Image, ImageDraw

DPI = 300
MM_PER_INCH = 25.4
PADDING_MM = 11.0
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


def _pawn_total_height_mm(size: PawnSize) -> float:
    """Total pawn height: padding + image + mirrored_image + padding."""
    _, h = PAWN_SPECS[size]
    return PADDING_MM * 2 + h * 2


# ---------------------------------------------------------------------------
# Collage slot system
# ---------------------------------------------------------------------------

# Valid sub-pawn arrangements in each slot type: (sub_size, grid_cols, grid_rows)
_SLOT_ARRANGEMENTS: dict[PawnSize, list[tuple[PawnSize, int, int]]] = {
    PawnSize.HUGE: [
        (PawnSize.HUGE, 1, 1),
        (PawnSize.MEDIUM, 2, 2),
        (PawnSize.SMALL, 3, 3),
    ],
    PawnSize.LARGE: [
        (PawnSize.LARGE, 1, 1),
        (PawnSize.SMALL, 2, 2),
    ],
    PawnSize.MEDIUM: [
        (PawnSize.MEDIUM, 1, 1),
        (PawnSize.SMALL, 1, 1),
    ],
    PawnSize.SMALL: [
        (PawnSize.SMALL, 1, 1),
    ],
}

# Quick lookup: (slot_type, sub_size) -> (grid_cols, grid_rows)
_GRID_LAYOUT: dict[tuple[PawnSize, PawnSize], tuple[int, int]] = {
    (slot_type, sub_size): (nc, nr)
    for slot_type, arrangements in _SLOT_ARRANGEMENTS.items()
    for sub_size, nc, nr in arrangements
}


def _build_row_specs() -> dict[PawnSize, tuple[float, float, int]]:
    """Compute (slot_width_mm, slot_height_mm, slots_per_row) for each row type.

    Slot dimensions are the maximum extent needed across all valid
    sub-pawn arrangements, ensuring at least ``COLLAGE_SPACING_MM``
    between sub-pawns.
    """
    sp = COLLAGE_SPACING_MM
    avail_w = A4_WIDTH_MM - 2 * COLLAGE_MARGIN_MM

    specs: dict[PawnSize, tuple[float, float, int]] = {}
    for size, arrangements in _SLOT_ARRANGEMENTS.items():
        slot_w = max(
            PAWN_SPECS[sub][0] * nc + sp * (nc - 1) for sub, nc, _ in arrangements
        )
        slot_h = max(
            _pawn_total_height_mm(sub) * nr + sp * (nr - 1)
            for sub, _, nr in arrangements
        )
        n_slots = int((avail_w + sp) / (slot_w + sp))
        specs[size] = (slot_w, slot_h, n_slots)

    return specs


_ROW_SPECS = _build_row_specs()


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
    - 4 mm of white padding is added at the top and bottom
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

    # Set DPI and pawn size metadata
    canvas.info["dpi"] = (DPI, DPI)
    canvas.info["pawn_size"] = size

    return canvas


# ---------------------------------------------------------------------------
# Collage layout
# ---------------------------------------------------------------------------


def _plan_rows(
    n_huge: int, n_large: int, n_medium: int, n_small: int
) -> list[tuple[PawnSize, list[tuple[PawnSize, int]]]]:
    """Plan row-by-row layout, filling unused slots with smaller pawns.

    Returns a list of ``(row_type, slots)`` where each slot is
    ``(sub_pawn_size, count)``.
    """
    rows: list[tuple[PawnSize, list[tuple[PawnSize, int]]]] = []

    # --- Huge rows (2 slots each) ---
    huge_placed = 0
    for _ in range(math.ceil(n_huge / 2) if n_huge else 0):
        slots: list[tuple[PawnSize, int]] = []
        for _ in range(_ROW_SPECS[PawnSize.HUGE][2]):
            if huge_placed < n_huge:
                slots.append((PawnSize.HUGE, 1))
                huge_placed += 1
            elif n_medium > 0:
                take = min(n_medium, 4)
                slots.append((PawnSize.MEDIUM, take))
                n_medium -= take
            elif n_small > 0:
                take = min(n_small, 9)
                slots.append((PawnSize.SMALL, take))
                n_small -= take
        rows.append((PawnSize.HUGE, slots))

    # --- Large rows (3 slots each) ---
    large_placed = 0
    for _ in range(math.ceil(n_large / 3) if n_large else 0):
        slots = []
        for _ in range(_ROW_SPECS[PawnSize.LARGE][2]):
            if large_placed < n_large:
                slots.append((PawnSize.LARGE, 1))
                large_placed += 1
            elif n_small > 0:
                take = min(n_small, 4)
                slots.append((PawnSize.SMALL, take))
                n_small -= take
        rows.append((PawnSize.LARGE, slots))

    # --- Medium rows (5 slots each) ---
    medium_placed = 0
    for _ in range(math.ceil(n_medium / 5) if n_medium else 0):
        slots = []
        for _ in range(_ROW_SPECS[PawnSize.MEDIUM][2]):
            if medium_placed < n_medium:
                slots.append((PawnSize.MEDIUM, 1))
                medium_placed += 1
            elif n_small > 0:
                slots.append((PawnSize.SMALL, 1))
                n_small -= 1
        rows.append((PawnSize.MEDIUM, slots))

    # --- Small rows (6 slots each) ---
    while n_small > 0:
        take = min(n_small, _ROW_SPECS[PawnSize.SMALL][2])
        slots = [(PawnSize.SMALL, 1) for _ in range(take)]
        n_small -= take
        rows.append((PawnSize.SMALL, slots))

    return rows


def _corner_positions(
    n_cols: int, n_rows: int, slot_w: int, slot_h: int, pawn_w: int, pawn_h: int
) -> list[tuple[int, int]]:
    """Compute corner-aligned grid positions within a slot (in pixels).

    For a 1x1 grid the pawn is centered.  For larger grids, outer pawns
    are pushed to the edges of the slot.
    """
    if n_cols <= 1:
        xs = [(slot_w - pawn_w) // 2]
    else:
        xs = [i * (slot_w - pawn_w) // (n_cols - 1) for i in range(n_cols)]

    if n_rows <= 1:
        ys = [(slot_h - pawn_h) // 2]
    else:
        ys = [i * (slot_h - pawn_h) // (n_rows - 1) for i in range(n_rows)]

    return [(x, y) for y in ys for x in xs]


def make_collage(pawns: Sequence[Image.Image]) -> Image.Image:
    """Arrange pawn images on an A4 page.

    Pawns are laid out in rows from the top of the page.  Larger pawns get
    rows first; unused slots in a row are filled with smaller pawns when
    possible.  Within an oversized slot, sub-pawns are corner-aligned.

    Parameters
    ----------
    pawns:
        Pawn images as returned by :func:`make_pawn`.  Must not be empty.

    Returns
    -------
    PIL Image in RGB mode at 300 DPI, sized to A4 (210 mm × 297 mm).

    Raises
    ------
    ValueError
        If *pawns* is empty or too many pawns to fit on a single page.
    """
    if not pawns:
        raise ValueError("pawns must not be empty")

    # Count by size
    counts: dict[PawnSize, int] = {s: 0 for s in PawnSize}
    for p in pawns:
        counts[p.info.get("pawn_size", PawnSize.MEDIUM)] += 1

    # Plan layout
    rows = _plan_rows(
        counts[PawnSize.HUGE],
        counts[PawnSize.LARGE],
        counts[PawnSize.MEDIUM],
        counts[PawnSize.SMALL],
    )

    # Check total height
    avail_h = A4_HEIGHT_MM - 2 * COLLAGE_MARGIN_MM
    if rows:
        total_h = sum(_ROW_SPECS[rt][1] for rt, _ in rows)
        total_h += (len(rows) - 1) * COLLAGE_SPACING_MM
        if total_h > avail_h:
            raise ValueError(
                f"Too many pawns to fit on a single A4 page "
                f"(need {total_h:.0f} mm, have {avail_h:.0f} mm available)"
            )

    # Build pawn queues by size
    queues: dict[PawnSize, list[Image.Image]] = {s: [] for s in PawnSize}
    for p in pawns:
        queues[p.info.get("pawn_size", PawnSize.MEDIUM)].append(p)

    page_w = mm_to_px(A4_WIDTH_MM)
    page_h = mm_to_px(A4_HEIGHT_MM)
    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    spacing_px = mm_to_px(COLLAGE_SPACING_MM)
    page = Image.new("RGB", (page_w, page_h), (255, 255, 255))

    y_px = margin_px
    for row_type, slot_list in rows:
        slot_w_mm, slot_h_mm, _ = _ROW_SPECS[row_type]
        slot_w_px = mm_to_px(slot_w_mm)
        slot_h_px = mm_to_px(slot_h_mm)

        x_px = margin_px
        for sub_size, count in slot_list:
            sub_pawns = [queues[sub_size].pop(0) for _ in range(count)]
            n_cols, n_rows = _GRID_LAYOUT[(row_type, sub_size)]
            positions = _corner_positions(
                n_cols,
                n_rows,
                slot_w_px,
                slot_h_px,
                sub_pawns[0].width,
                sub_pawns[0].height,
            )
            for i, sub_pawn in enumerate(sub_pawns):
                px, py = positions[i]
                page.paste(sub_pawn, (x_px + px, y_px + py))

            x_px += slot_w_px + spacing_px

        y_px += slot_h_px + spacing_px

    page.info["dpi"] = (DPI, DPI)
    return page
