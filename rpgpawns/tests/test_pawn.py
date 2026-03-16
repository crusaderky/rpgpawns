from __future__ import annotations

import pytest
from PIL import Image

from rpgpawns.pawn import (
    A4_HEIGHT_MM,
    A4_WIDTH_MM,
    BORDER_COLOR,
    BORDER_WHITE_RATIO,
    BORDER_WHITE_THRESHOLD,
    BORDER_WIDTH_PX,
    COLLAGE_MARGIN_MM,
    DPI,
    MIN_PADDING_MM,
    PAWN_SPECS,
    BorderSide,
    PawnSize,
    has_white_border,
    make_collage,
    make_pawn,
    mm_to_px,
)

# Default (medium) pawn dimensions for backward-compatible tests
MAX_WIDTH_MM = PAWN_SPECS[PawnSize.MEDIUM][0]
MAX_HEIGHT_MM = PAWN_SPECS[PawnSize.MEDIUM][1]


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


def _compute_scaled_dims(
    input_w: int,
    input_h: int,
    size: PawnSize = PawnSize.MEDIUM,
) -> tuple[int, int]:
    """Compute the expected scaled image dimensions for a given input."""
    max_w_mm, max_h_mm = PAWN_SPECS[size]
    max_w_px = mm_to_px(max_w_mm)
    max_h_px = mm_to_px(max_h_mm)
    scale = min(max_w_px / input_w, max_h_px / input_h)
    new_w = min(round(input_w * scale), max_w_px)
    new_h = min(round(input_h * scale), max_h_px)
    return new_w, new_h


def _expected_total_height(size: PawnSize = PawnSize.MEDIUM) -> int:
    """Expected constant total pawn height in pixels for a given size."""
    max_h_mm = PAWN_SPECS[size][1]
    return (mm_to_px(MIN_PADDING_MM) + mm_to_px(max_h_mm)) * 2


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
    assert result.height == _expected_total_height()


def test_total_height_structure():
    """Total height is constant for a given size, regardless of input aspect ratio."""
    result = make_pawn(_create_test_image(200, 300))
    assert result.height == _expected_total_height()


@pytest.mark.parametrize("size", list(PawnSize))
def test_constant_total_height_across_aspect_ratios(size):
    """All pawns of the same size have identical total height."""
    expected_h = _expected_total_height(size)
    for input_w, input_h in [(4000, 200), (200, 4000), (500, 500)]:
        result = make_pawn(_create_test_image(input_w, input_h), size=size)
        assert result.height == expected_h


def test_extra_padding_for_short_image():
    """A width-constrained image shorter than max_h gets extra padding."""
    # Very wide image: fills width (28mm) but is much shorter than 48mm
    result = make_pawn(_create_test_image(4000, 200))
    _, new_h = _compute_scaled_dims(4000, 200)
    canvas_h = _expected_total_height()
    actual_padding = (canvas_h - new_h * 2) // 2
    min_padding = mm_to_px(MIN_PADDING_MM)
    assert actual_padding > min_padding
    # Verify the extra padding area at top is white (inside border)
    for x in range(BORDER_WIDTH_PX, result.width - BORDER_WIDTH_PX, 10):
        for y in range(BORDER_WIDTH_PX, actual_padding, 10):
            assert result.getpixel((x, y)) == (255, 255, 255)


def test_minimum_padding_for_tall_image():
    """A height-constrained image gets exactly the minimum padding."""
    # Very tall image: fills height (48mm) but narrower than 28mm
    _, new_h = _compute_scaled_dims(200, 4000)
    canvas_h = _expected_total_height()
    actual_padding = (canvas_h - new_h * 2) // 2
    min_padding = mm_to_px(MIN_PADDING_MM)
    assert actual_padding == min_padding


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
    expected_w, expected_h = _compute_scaled_dims(input_w, input_h)
    assert result.width == expected_w
    assert result.height == _expected_total_height()
    original_ratio = input_w / input_h
    output_ratio = expected_w / expected_h
    assert abs(original_ratio - output_ratio) / original_ratio < 0.02


def test_mirror_boundary_matches():
    """Bottom row of mirrored image should match top row of original."""
    input_w, input_h = 50, 50
    result = make_pawn(_create_gradient_image(input_w, input_h))
    _, new_h = _compute_scaled_dims(input_w, input_h)
    canvas_h = _expected_total_height()
    padding_px = (canvas_h - new_h * 2) // 2
    mid_y = padding_px + new_h
    # Bottom of mirrored region should equal top of original region
    for x in range(0, result.width, 5):
        mirrored_px = result.getpixel((x, mid_y - 1))
        original_px = result.getpixel((x, mid_y))
        assert mirrored_px == original_px


def test_mirror_is_vertically_flipped():
    """The mirrored half should be a vertical flip of the original half."""
    input_w, input_h = 30, 60
    result = make_pawn(_create_gradient_image(input_w, input_h))
    _, new_h = _compute_scaled_dims(input_w, input_h)
    canvas_h = _expected_total_height()
    padding_px = (canvas_h - new_h * 2) // 2
    # For each row in the original, there should be a corresponding
    # mirrored row
    for dy in range(0, new_h, max(1, new_h // 10)):
        for x in range(0, result.width, max(1, result.width // 5)):
            orig_y = padding_px + new_h + dy
            mirror_y = padding_px + new_h - 1 - dy
            assert result.getpixel((x, orig_y)) == result.getpixel((x, mirror_y))


def test_top_padding_is_white():
    result = make_pawn(_create_test_image(100, 100, color=(0, 0, 255)))
    padding_px = mm_to_px(MIN_PADDING_MM)
    # Sample pixels in the top padding (inside border)
    for x in range(BORDER_WIDTH_PX, result.width - BORDER_WIDTH_PX, 10):
        for y in range(BORDER_WIDTH_PX, padding_px, 10):
            assert result.getpixel((x, y)) == (255, 255, 255)


def test_bottom_padding_is_white():
    result = make_pawn(_create_test_image(100, 100, color=(0, 0, 255)))
    padding_px = mm_to_px(MIN_PADDING_MM)
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
# has_white_border tests
# ---------------------------------------------------------------------------


def test_has_white_border_all_white():
    """All white image returns True for both sides."""
    img = Image.new("RGB", (10, 100), (255, 255, 255))
    assert has_white_border(img, BorderSide.LEFT) is True
    assert has_white_border(img, BorderSide.RIGHT) is True


def test_has_white_border_all_black():
    """All black image returns False for both sides."""
    img = Image.new("RGB", (10, 100), (0, 0, 0))
    assert has_white_border(img, BorderSide.LEFT) is False
    assert has_white_border(img, BorderSide.RIGHT) is False


def test_has_white_border_checks_left_column():
    """LEFT checks column at x=BORDER_WIDTH_PX, not at x=0."""
    img = Image.new("RGB", (10, 100), (0, 0, 0))
    # Make column x=BORDER_WIDTH_PX all white
    for y in range(100):
        img.putpixel((BORDER_WIDTH_PX, y), (255, 255, 255))
    assert has_white_border(img, BorderSide.LEFT) is True
    # RIGHT column is still black
    assert has_white_border(img, BorderSide.RIGHT) is False


def test_has_white_border_checks_right_column():
    """RIGHT checks column at x=width-1-BORDER_WIDTH_PX."""
    img = Image.new("RGB", (10, 100), (0, 0, 0))
    x_right = img.width - 1 - BORDER_WIDTH_PX
    for y in range(100):
        img.putpixel((x_right, y), (255, 255, 255))
    assert has_white_border(img, BorderSide.RIGHT) is True
    # LEFT column is still black
    assert has_white_border(img, BorderSide.LEFT) is False


def test_has_white_border_ignores_outermost_column():
    """The outermost column (x=0 / x=width-1) is ignored."""
    img = Image.new("RGB", (10, 100), (0, 0, 0))
    # Make x=0 all white — should NOT affect LEFT result
    for y in range(100):
        img.putpixel((0, y), (255, 255, 255))
    assert has_white_border(img, BorderSide.LEFT) is False


def test_has_white_border_threshold_exact():
    """Pixels at exactly BORDER_WHITE_THRESHOLD are considered white."""
    t = BORDER_WHITE_THRESHOLD
    img = Image.new("RGB", (10, 100), (t, t, t))
    assert has_white_border(img, BorderSide.LEFT) is True


def test_has_white_border_below_threshold():
    """Pixels one below BORDER_WHITE_THRESHOLD are not white."""
    t = BORDER_WHITE_THRESHOLD - 1
    img = Image.new("RGB", (10, 100), (t, t, t))
    assert has_white_border(img, BorderSide.LEFT) is False


def test_has_white_border_single_channel_below():
    """If any single RGB channel is below threshold, the pixel is non-white."""
    t = BORDER_WHITE_THRESHOLD
    img = Image.new("RGB", (10, 100), (t, t, t - 1))
    assert has_white_border(img, BorderSide.LEFT) is False


def test_has_white_border_ratio_boundary():
    """Exactly BORDER_WHITE_RATIO of white pixels returns True."""
    h = 100
    n_white = int(h * BORDER_WHITE_RATIO)  # 90
    img = Image.new("RGB", (10, h), (0, 0, 0))
    for y in range(n_white):
        img.putpixel((BORDER_WIDTH_PX, y), (255, 255, 255))
    assert has_white_border(img, BorderSide.LEFT) is True


def test_has_white_border_ratio_just_below():
    """One fewer white pixel than the ratio requires returns False."""
    h = 100
    n_white = int(h * BORDER_WHITE_RATIO) - 1  # 89
    img = Image.new("RGB", (10, h), (0, 0, 0))
    for y in range(n_white):
        img.putpixel((BORDER_WIDTH_PX, y), (255, 255, 255))
    assert has_white_border(img, BorderSide.LEFT) is False


def test_has_white_border_pawn_white_source():
    """A pawn made from a white image has white borders on both sides."""
    pawn = make_pawn(Image.new("RGB", (100, 150), (255, 255, 255)))
    assert has_white_border(pawn, BorderSide.LEFT) is True
    assert has_white_border(pawn, BorderSide.RIGHT) is True


def test_has_white_border_pawn_colored_source():
    """A pawn from a tall colored image has non-white borders."""
    # 100x150 red image fills enough height that the red edge pixels
    # exceed the (1 - BORDER_WHITE_RATIO) tolerance.
    pawn = make_pawn(Image.new("RGB", (100, 150), (255, 0, 0)))
    assert has_white_border(pawn, BorderSide.LEFT) is False
    assert has_white_border(pawn, BorderSide.RIGHT) is False


@pytest.mark.parametrize("side", list(BorderSide))
def test_has_white_border_both_enum_values(side):
    """has_white_border accepts both BorderSide enum members."""
    img = Image.new("RGB", (10, 50), (255, 255, 255))
    assert has_white_border(img, side) is True


# ---------------------------------------------------------------------------
# make_collage tests
# ---------------------------------------------------------------------------


def _make_test_pawn(
    color: tuple[int, int, int] = (255, 0, 0),
    size: PawnSize = PawnSize.MEDIUM,
) -> Image.Image:
    """Create a pawn image via make_pawn for use in collage tests."""
    return make_pawn(Image.new("RGB", (100, 150), color), size=size)


def test_collage_output_dimensions():
    pages = make_collage([_make_test_pawn()])
    assert len(pages) == 1
    assert pages[0].width == mm_to_px(A4_WIDTH_MM)
    assert pages[0].height == mm_to_px(A4_HEIGHT_MM)


def test_collage_white_border_overlap():
    """Adjacent white-bordered pawns overlap by BORDER_WIDTH_PX instead of spacing."""
    pawn = make_pawn(Image.new("RGB", (100, 150), (255, 255, 255)))
    pages = make_collage([pawn, pawn])
    result = pages[0]

    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    # With overlap: pawn2 starts pawn.width - BORDER_WIDTH_PX pixels from
    # pawn1's start (the borders merge into a single grey line).
    pawn2_x = margin_px + pawn.width - BORDER_WIDTH_PX
    pawn2_right = pawn2_x + pawn.width - 1
    mid_y = margin_px + pawn.height // 2

    # Pawn2's right border at the expected overlap position
    assert result.getpixel((pawn2_right, mid_y)) == BORDER_COLOR
    # One pixel past pawn2 is white background
    assert result.getpixel((pawn2_right + 1, mid_y)) == (255, 255, 255)


def test_collage_output_dpi():
    pages = make_collage([_make_test_pawn()])
    assert pages[0].info.get("dpi") == (DPI, DPI)


def test_collage_output_mode():
    pages = make_collage([_make_test_pawn()])
    assert pages[0].mode == "RGB"


def test_collage_white_background():
    pages = make_collage([_make_test_pawn()])
    result = pages[0]
    # Check a corner far from any pawn placement
    assert result.getpixel((result.width - 1, result.height - 1)) == (255, 255, 255)
    assert result.getpixel((0, 0)) == (255, 255, 255)


def test_collage_single_pawn():
    pawn = _make_test_pawn()
    pages = make_collage([pawn])
    result = pages[0]
    # The pawn should be placed somewhere on the page; verify non-white pixels exist
    # in the region where the pawn should be (top-left area)
    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    found_non_white = False
    # Scan a generous area from the top-left
    for x in range(margin_px, margin_px + pawn.width):
        for y in range(margin_px, margin_px + pawn.height):
            if result.getpixel((x, y)) != (255, 255, 255):
                found_non_white = True
                break
        if found_non_white:
            break
    assert found_non_white


def test_collage_many_medium_pawns():
    """Several medium pawns should fit on a page without error."""
    pawns = [_make_test_pawn() for _ in range(5)]
    pages = make_collage(pawns)
    assert pages[0].width == mm_to_px(A4_WIDTH_MM)


def test_collage_empty_raises():
    with pytest.raises(ValueError, match="pawns must not be empty"):
        make_collage([])


def test_collage_many_pawns_multi_page():
    """Enough pawns should produce multiple pages instead of raising."""
    pawns = [_make_test_pawn(size=PawnSize.HUGE) for _ in range(20)]
    pages = make_collage(pawns)
    assert len(pages) > 1
    for page in pages:
        assert page.width == mm_to_px(A4_WIDTH_MM)
        assert page.height == mm_to_px(A4_HEIGHT_MM)
        assert page.info.get("dpi") == (DPI, DPI)


def test_collage_margin():
    """The page margin area should be entirely white."""
    pawns = [_make_test_pawn() for _ in range(5)]
    pages = make_collage(pawns)
    result = pages[0]

    margin_px = mm_to_px(COLLAGE_MARGIN_MM)
    # Top margin row
    for x in range(0, result.width, 20):
        for y in range(margin_px):
            assert result.getpixel((x, y)) == (255, 255, 255)
    # Left margin column
    for y in range(0, result.height, 20):
        for x in range(margin_px):
            assert result.getpixel((x, y)) == (255, 255, 255)


def test_collage_mixed_sizes():
    """A collage with different pawn sizes should render without error."""
    pawns = [
        _make_test_pawn(size=PawnSize.HUGE),
        _make_test_pawn(size=PawnSize.LARGE),
        _make_test_pawn(size=PawnSize.MEDIUM),
        _make_test_pawn(size=PawnSize.SMALL),
    ]
    pages = make_collage(pawns)
    assert pages[0].width == mm_to_px(A4_WIDTH_MM)
    assert pages[0].height == mm_to_px(A4_HEIGHT_MM)


@pytest.mark.parametrize("size", list(PawnSize))
def test_collage_single_size(size):
    """A collage with a single pawn of each size should work."""
    pawn = _make_test_pawn(size=size)
    pages = make_collage([pawn])
    assert pages[0].width == mm_to_px(A4_WIDTH_MM)


@pytest.mark.parametrize("size", list(PawnSize))
def test_make_pawn_size(size):
    """make_pawn respects the size parameter."""
    max_w_mm, _max_h_mm = PAWN_SPECS[size]
    result = make_pawn(_create_test_image(4000, 4000), size=size)
    assert result.width <= mm_to_px(max_w_mm)
    assert result.height == _expected_total_height(size)


def test_make_pawn_stores_size_metadata():
    """make_pawn stores the pawn size in image info."""
    for size in PawnSize:
        result = make_pawn(_create_test_image(100, 100), size=size)
        assert result.info["pawn_size"] is size


def test_collage_small_in_large_slot():
    """4 small pawns fit in a single row."""
    pawns = [_make_test_pawn(size=PawnSize.SMALL) for _ in range(4)]
    pages = make_collage(pawns)
    assert pages[0].width == mm_to_px(A4_WIDTH_MM)


def test_collage_medium_in_huge_slot():
    """4 medium pawns fit in a single row."""
    pawns = [_make_test_pawn(size=PawnSize.MEDIUM) for _ in range(4)]
    pages = make_collage(pawns)
    assert pages[0].width == mm_to_px(A4_WIDTH_MM)


def test_collage_returns_list():
    """make_collage always returns a list, even for a single page."""
    pages = make_collage([_make_test_pawn()])
    assert isinstance(pages, list)
    assert len(pages) == 1


def test_collage_multi_page_all_pages_valid():
    """Each page in a multi-page collage is a valid A4 RGB image."""
    pawns = [_make_test_pawn(size=PawnSize.HUGE) for _ in range(20)]
    pages = make_collage(pawns)
    for page in pages:
        assert isinstance(page, Image.Image)
        assert page.mode == "RGB"
        assert page.width == mm_to_px(A4_WIDTH_MM)
        assert page.height == mm_to_px(A4_HEIGHT_MM)
        assert page.info.get("dpi") == (DPI, DPI)


def test_collage_multi_page_has_content():
    """Every page in a multi-page collage has non-white pixels (pawns)."""
    pawns = [_make_test_pawn(size=PawnSize.HUGE) for _ in range(20)]
    pages = make_collage(pawns)
    assert len(pages) > 1
    for page in pages:
        found_non_white = False
        for x in range(0, page.width, 50):
            for y in range(0, page.height, 50):
                if page.getpixel((x, y)) != (255, 255, 255):
                    found_non_white = True
                    break
            if found_non_white:
                break
        assert found_non_white


def test_collage_custom_margin():
    """make_collage respects custom margin parameter."""
    pawns = [_make_test_pawn() for _ in range(5)]
    margin_mm = 10.0
    pages = make_collage(pawns, margin_mm=margin_mm)
    result = pages[0]

    margin_px = mm_to_px(margin_mm)
    # Top margin row should be white
    for x in range(0, result.width, 20):
        for y in range(margin_px):
            assert result.getpixel((x, y)) == (255, 255, 255)
    # Left margin column should be white
    for y in range(0, result.height, 20):
        for x in range(margin_px):
            assert result.getpixel((x, y)) == (255, 255, 255)


def test_collage_default_margin():
    """make_collage uses COLLAGE_MARGIN_MM as default."""
    pawns = [_make_test_pawn() for _ in range(5)]
    pages_default = make_collage(pawns)
    pages_explicit = make_collage(pawns, margin_mm=COLLAGE_MARGIN_MM)
    # Both should produce the same result
    assert pages_default[0].size == pages_explicit[0].size


def test_collage_zero_margin():
    """make_collage works with zero margin."""
    pawns = [_make_test_pawn() for _ in range(2)]
    pages = make_collage(pawns, margin_mm=0.0)
    result = pages[0]

    assert result.width == mm_to_px(A4_WIDTH_MM)
    assert result.height == mm_to_px(A4_HEIGHT_MM)
    # With zero margin, pawns should be placed at the very edge
    # Check that there's non-white content near the edges
    found_non_white_near_edge = False
    for x in range(20):
        for y in range(50):
            if result.getpixel((x, y)) != (255, 255, 255):
                found_non_white_near_edge = True
                break
        if found_non_white_near_edge:
            break
    assert found_non_white_near_edge


def test_collage_large_margin():
    """make_collage works with large margin values."""
    pawns = [_make_test_pawn(size=PawnSize.SMALL)]
    margin_mm = 50.0
    pages = make_collage(pawns, margin_mm=margin_mm)
    result = pages[0]

    margin_px = mm_to_px(margin_mm)
    # Verify the larger margin area is white
    for x in range(0, result.width, 50):
        for y in range(margin_px):
            assert result.getpixel((x, y)) == (255, 255, 255)
