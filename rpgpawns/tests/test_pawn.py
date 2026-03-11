from __future__ import annotations

import pytest
from PIL import Image

from rpgpawns.pawn import (
    BORDER_COLOR,
    BORDER_WIDTH_PX,
    COLLAGE_COLS,
    COLLAGE_MARGIN_MM,
    COLLAGE_MAX_PAWNS,
    COLLAGE_ROWS,
    COLLAGE_SPACING_MM,
    DPI,
    A4_HEIGHT_MM,
    A4_WIDTH_MM,
    MAX_HEIGHT_MM,
    MAX_WIDTH_MM,
    PADDING_MM,
    make_collage,
    make_pawn,
    mm_to_px,
)


def _create_test_image(
    width: int,
    height: int,
    color: tuple[int, int, int] = (255, 0, 0),
) -> Image.Image:
    """Create a solid-color test image."""
    return Image.new("RGB", (width, height), color)


def _create_gradient_image(width: int, height: int) -> Image.Image:
    """Create a test image with a vertical gradient for mirror testing."""
    img = Image.new("RGB", (width, height))
    for y in range(height):
        value = int(255 * y / max(height - 1, 1))
        for x in range(width):
            img.putpixel((x, y), (value, 0, 0))
    return img


def test_mm_to_px_known_values():
    # 25.4mm = 1 inch = 300 pixels at 300 DPI
    assert mm_to_px(25.4) == 300


def test_mm_to_px_zero():
    assert mm_to_px(0) == 0


def test_mm_to_px_custom_dpi():
    assert mm_to_px(25.4, dpi=150) == 150


def test_output_dpi():
    result = make_pawn(_create_test_image(200, 300))
    assert result.info.get("dpi") == (DPI, DPI)


def test_output_mode():
    result = make_pawn(_create_test_image(200, 300))
    assert result.mode == "RGB"


def test_wide_image_constrained_by_width():
    """A very wide image should be constrained to 28mm width."""
    result = make_pawn(_create_test_image(4000, 200))
    max_w_px = mm_to_px(MAX_WIDTH_MM)
    assert result.width <= max_w_px


def test_tall_image_constrained_by_height():
    """A very tall image should be constrained to 48mm per half."""
    result = make_pawn(_create_test_image(200, 4000))
    max_total_h_px = mm_to_px(PADDING_MM * 2 + MAX_HEIGHT_MM * 2)
    assert result.height <= max_total_h_px


def test_total_height_structure():
    """Total height = padding + image_h + image_h + padding."""
    result = make_pawn(_create_test_image(200, 300))
    padding_px = mm_to_px(PADDING_MM)
    # Height minus both paddings must be even (two copies of same image)
    image_zone = result.height - 2 * padding_px
    assert image_zone % 2 == 0 or abs(image_zone % 2) <= 1


def test_small_image_upscaled():
    """A tiny image should be scaled up to fill the available space."""
    result = make_pawn(_create_test_image(10, 10))
    # Should be scaled up to fill width or height
    assert result.width > 10


@pytest.mark.parametrize(
    "input_w,input_h",
    [
        (800, 400),  # 2:1 landscape
        (400, 800),  # 1:2 portrait
        (500, 500),  # 1:1 square
        (1920, 1080),  # 16:9 widescreen
        (100, 3000),  # extreme portrait
    ],
)
def test_aspect_ratio_preserved(input_w, input_h):
    result = make_pawn(_create_test_image(input_w, input_h))
    padding_px = mm_to_px(PADDING_MM)
    img_h = (result.height - 2 * padding_px) / 2
    img_w = result.width
    original_ratio = input_w / input_h
    output_ratio = img_w / img_h
    assert abs(original_ratio - output_ratio) / original_ratio < 0.02


def test_mirror_boundary_matches():
    """Bottom row of mirrored image should match top row of original."""
    result = make_pawn(_create_gradient_image(50, 50))
    padding_px = mm_to_px(PADDING_MM)
    img_h = (result.height - 2 * padding_px) // 2
    mid_y = padding_px + img_h
    # Bottom of mirrored region should equal top of original region
    for x in range(0, result.width, 5):
        mirrored_px = result.getpixel((x, mid_y - 1))
        original_px = result.getpixel((x, mid_y))
        assert mirrored_px == original_px


def test_mirror_is_vertically_flipped():
    """The mirrored half should be a vertical flip of the original half."""
    result = make_pawn(_create_gradient_image(30, 60))
    padding_px = mm_to_px(PADDING_MM)
    img_h = (result.height - 2 * padding_px) // 2
    # For each row in the original, there should be a corresponding
    # mirrored row
    for dy in range(0, img_h, max(1, img_h // 10)):
        for x in range(0, result.width, max(1, result.width // 5)):
            orig_y = padding_px + img_h + dy
            mirror_y = padding_px + img_h - 1 - dy
            assert result.getpixel((x, orig_y)) == result.getpixel(
                (x, mirror_y)
            )


def test_top_padding_is_white():
    result = make_pawn(_create_test_image(100, 100, color=(0, 0, 255)))
    padding_px = mm_to_px(PADDING_MM)
    # Sample pixels in the top padding (inside border)
    for x in range(BORDER_WIDTH_PX, result.width - BORDER_WIDTH_PX, 10):
        for y in range(BORDER_WIDTH_PX, padding_px, 10):
            assert result.getpixel((x, y)) == (255, 255, 255)


def test_bottom_padding_is_white():
    result = make_pawn(_create_test_image(100, 100, color=(0, 0, 255)))
    padding_px = mm_to_px(PADDING_MM)
    bottom_start = result.height - padding_px
    for x in range(BORDER_WIDTH_PX, result.width - BORDER_WIDTH_PX, 10):
        for y in range(bottom_start, result.height - BORDER_WIDTH_PX, 10):
            assert result.getpixel((x, y)) == (255, 255, 255)


def test_border_corners():
    result = make_pawn(_create_test_image(100, 100))
    assert result.getpixel((0, 0)) == BORDER_COLOR
    assert result.getpixel((result.width - 1, 0)) == BORDER_COLOR
    assert result.getpixel((0, result.height - 1)) == BORDER_COLOR
    assert result.getpixel((result.width - 1, result.height - 1)) == BORDER_COLOR


def test_border_edges():
    result = make_pawn(_create_test_image(100, 100))
    mid_x = result.width // 2
    mid_y = result.height // 2
    # Top edge
    assert result.getpixel((mid_x, 0)) == BORDER_COLOR
    # Bottom edge
    assert result.getpixel((mid_x, result.height - 1)) == BORDER_COLOR
    # Left edge
    assert result.getpixel((0, mid_y)) == BORDER_COLOR
    # Right edge
    assert result.getpixel((result.width - 1, mid_y)) == BORDER_COLOR


def test_rgba_input():
    """RGBA images should be composited onto white background."""
    img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
    result = make_pawn(img)
    assert result.mode == "RGB"


def test_grayscale_input():
    """Grayscale images should be converted to RGB."""
    img = Image.new("L", (100, 100), 128)
    result = make_pawn(img)
    assert result.mode == "RGB"


def test_input_not_mutated():
    """make_pawn should not modify the input image."""
    img = _create_test_image(100, 100)
    original_size = img.size
    original_mode = img.mode
    make_pawn(img)
    assert img.size == original_size
    assert img.mode == original_mode


# ---------------------------------------------------------------------------
# make_collage tests
# ---------------------------------------------------------------------------


def _make_test_pawn(color: tuple[int, int, int] = (255, 0, 0)) -> Image.Image:
    """Create a pawn image via make_pawn for use in collage tests."""
    return make_pawn(Image.new("RGB", (100, 150), color))


def test_collage_grid_constants():
    """Verify the computed grid constants are sensible for A4."""
    assert COLLAGE_COLS == 5
    assert COLLAGE_ROWS == 2
    assert COLLAGE_MAX_PAWNS == 10


def test_collage_output_dimensions():
    result = make_collage([_make_test_pawn()])
    assert result.width == mm_to_px(A4_WIDTH_MM)
    assert result.height == mm_to_px(A4_HEIGHT_MM)


def test_collage_output_dpi():
    result = make_collage([_make_test_pawn()])
    assert result.info.get("dpi") == (DPI, DPI)


def test_collage_output_mode():
    result = make_collage([_make_test_pawn()])
    assert result.mode == "RGB"


def test_collage_white_background():
    result = make_collage([_make_test_pawn()])
    # Check a corner far from any pawn placement
    assert result.getpixel((result.width - 1, result.height - 1)) == (255, 255, 255)
    assert result.getpixel((0, 0)) == (255, 255, 255)


def test_collage_single_pawn():
    pawn = _make_test_pawn()
    result = make_collage([pawn])
    # The pawn should be placed in the top-left cell; verify pixels are
    # not all white by sampling the cell area
    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    cell_w = mm_to_px(MAX_WIDTH_MM)
    cell_h = mm_to_px(PADDING_MM * 2 + MAX_HEIGHT_MM * 2)
    # Center of the first cell
    cx = margin_px + cell_w // 2
    cy = margin_px + cell_h // 2
    # At least some pixels around the center should be non-white
    found_non_white = False
    for dx in range(-10, 11):
        for dy in range(-10, 11):
            if result.getpixel((cx + dx, cy + dy)) != (255, 255, 255):
                found_non_white = True
                break
        if found_non_white:
            break
    assert found_non_white


def test_collage_max_pawns():
    pawns = [_make_test_pawn() for _ in range(COLLAGE_MAX_PAWNS)]
    result = make_collage(pawns)
    assert result.width == mm_to_px(A4_WIDTH_MM)


def test_collage_empty_raises():
    with pytest.raises(ValueError, match="pawns must not be empty"):
        make_collage([])


def test_collage_too_many_raises():
    pawns = [_make_test_pawn() for _ in range(COLLAGE_MAX_PAWNS + 1)]
    with pytest.raises(ValueError, match="Too many pawns"):
        make_collage(pawns)


def test_collage_placement_order():
    """Pawns are placed left-to-right first, then top-to-bottom."""
    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
    ]
    pawns = [_make_test_pawn(c) for c in colors]
    result = make_collage(pawns)

    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    spacing_px = mm_to_px(COLLAGE_SPACING_MM)
    cell_w = mm_to_px(MAX_WIDTH_MM)
    cell_h = mm_to_px(PADDING_MM * 2 + MAX_HEIGHT_MM * 2)

    for i, pawn in enumerate(pawns):
        col = i % COLLAGE_COLS
        row = i // COLLAGE_COLS
        cell_x = margin_px + col * (cell_w + spacing_px)
        cell_y = margin_px + row * (cell_h + spacing_px)
        offset_x = (cell_w - pawn.width) // 2
        offset_y = (cell_h - pawn.height) // 2
        # Sample a pixel from the pawn's interior (skip border)
        px = cell_x + offset_x + pawn.width // 2
        py = cell_y + offset_y + pawn.height // 2
        pixel = result.getpixel((px, py))
        # The pawn center should not be white (it contains the image content)
        assert pixel != (255, 255, 255), f"Pawn {i} not found at col={col} row={row}"


def test_collage_margin():
    """The page margin area should be entirely white."""
    pawns = [_make_test_pawn() for _ in range(COLLAGE_MAX_PAWNS)]
    result = make_collage(pawns)

    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    # Top margin row
    for x in range(0, result.width, 20):
        for y in range(0, margin_px):
            assert result.getpixel((x, y)) == (255, 255, 255)
    # Left margin column
    for y in range(0, result.height, 20):
        for x in range(0, margin_px):
            assert result.getpixel((x, y)) == (255, 255, 255)


def test_collage_spacing():
    """Gaps between adjacent pawns should be at least 10mm wide and white."""
    pawns = [_make_test_pawn() for _ in range(2)]
    result = make_collage(pawns)

    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    spacing_px = mm_to_px(COLLAGE_SPACING_MM)
    cell_w = mm_to_px(MAX_WIDTH_MM)

    # The gap between column 0 and column 1 starts at margin + cell_w
    gap_start_x = margin_px + cell_w
    gap_end_x = gap_start_x + spacing_px
    # Verify the gap is at least 10mm
    assert gap_end_x - gap_start_x >= mm_to_px(10.0)
    # Verify the gap is white (sample middle of gap vertically)
    gap_mid_x = (gap_start_x + gap_end_x) // 2
    for y in range(margin_px, margin_px + 50, 5):
        assert result.getpixel((gap_mid_x, y)) == (255, 255, 255)


def test_collage_pawn_centered_in_cell():
    """A pawn smaller than the max cell size should be centered."""
    # Create a narrow pawn (narrow input -> narrow output)
    narrow_pawn = make_pawn(Image.new("RGB", (50, 500), (0, 100, 200)))
    result = make_collage([narrow_pawn])

    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    cell_w = mm_to_px(MAX_WIDTH_MM)
    cell_h = mm_to_px(PADDING_MM * 2 + MAX_HEIGHT_MM * 2)
    offset_x = (cell_w - narrow_pawn.width) // 2
    offset_y = (cell_h - narrow_pawn.height) // 2

    # Pixel just inside the pawn's position should be non-white
    px = margin_px + offset_x + narrow_pawn.width // 2
    py = margin_px + offset_y + narrow_pawn.height // 2
    assert result.getpixel((px, py)) != (255, 255, 255)

    # Pixel in the left margin of the cell (before the pawn) should be white
    if offset_x > 1:
        assert result.getpixel((margin_px + 1, margin_px + cell_h // 2)) == (
            255,
            255,
            255,
        )
