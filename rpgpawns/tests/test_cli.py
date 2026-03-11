from __future__ import annotations

import pytest
from PIL import Image

from rpgpawns.cli import main, parse_image_args
from rpgpawns.pawn import PawnSize


def _create_test_image(path, color=(255, 0, 0)):
    """Create a small test image on disk."""
    img = Image.new("RGB", (80, 120), color)
    img.save(str(path))


# ---------------------------------------------------------------------------
# parse_image_args tests
# ---------------------------------------------------------------------------


def test_parse_single_image():
    assert parse_image_args(["foo.jpg"]) == [("foo.jpg", PawnSize.MEDIUM, 1)]


def test_parse_multiple_images():
    assert parse_image_args(["a.jpg", "b.png"]) == [
        ("a.jpg", PawnSize.MEDIUM, 1),
        ("b.png", PawnSize.MEDIUM, 1),
    ]


def test_parse_image_with_count():
    assert parse_image_args(["a.jpg", "3"]) == [("a.jpg", PawnSize.MEDIUM, 3)]


def test_parse_count_only_on_last():
    result = parse_image_args(["a.jpg", "b.png", "2"])
    assert result == [("a.jpg", PawnSize.MEDIUM, 1), ("b.png", PawnSize.MEDIUM, 2)]


def test_parse_mixed():
    result = parse_image_args(["a.jpg", "2", "b.png"])
    assert result == [("a.jpg", PawnSize.MEDIUM, 2), ("b.png", PawnSize.MEDIUM, 1)]


def test_parse_size_only():
    assert parse_image_args(["a.jpg", "large"]) == [("a.jpg", PawnSize.LARGE, 1)]


def test_parse_size_and_count():
    assert parse_image_args(["a.jpg", "small:2"]) == [("a.jpg", PawnSize.SMALL, 2)]


def test_parse_huge():
    assert parse_image_args(["a.jpg", "huge:3"]) == [("a.jpg", PawnSize.HUGE, 3)]


def test_parse_medium_explicit():
    assert parse_image_args(["a.jpg", "medium"]) == [("a.jpg", PawnSize.MEDIUM, 1)]


def test_parse_modifier_overrides():
    """Last modifier for the same image wins."""
    assert parse_image_args(["a.jpg", "small:2", "large:3"]) == [
        ("a.jpg", PawnSize.LARGE, 3)
    ]


def test_parse_modifier_no_preceding_image():
    with pytest.raises(ValueError, match="no preceding image"):
        parse_image_args(["2"])


def test_parse_size_no_preceding_image():
    with pytest.raises(ValueError, match="no preceding image"):
        parse_image_args(["small"])


def test_parse_count_zero():
    with pytest.raises(ValueError, match="at least 1"):
        parse_image_args(["a.jpg", "small:0"])


def test_parse_mixed_sizes():
    result = parse_image_args(["a.jpg", "small:2", "b.png", "large"])
    assert result == [
        ("a.jpg", PawnSize.SMALL, 2),
        ("b.png", PawnSize.LARGE, 1),
    ]


# ---------------------------------------------------------------------------
# main() integration tests
# ---------------------------------------------------------------------------


def test_main_single_image_default_output(tmp_path):
    img_path = tmp_path / "input.png"
    _create_test_image(img_path)
    output_path = tmp_path / "output.pdf"
    main([str(img_path), "-o", str(output_path)])

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_main_default_output_name(tmp_path, monkeypatch):
    img_path = tmp_path / "input.png"
    _create_test_image(img_path)
    monkeypatch.chdir(tmp_path)
    main([str(img_path)])

    default_output = tmp_path / "output.pdf"
    assert default_output.exists()


def test_main_png_output(tmp_path):
    img_path = tmp_path / "input.png"
    _create_test_image(img_path)
    output_path = tmp_path / "output.png"
    main([str(img_path), "-o", str(output_path)])

    assert output_path.exists()
    with Image.open(output_path) as result:
        assert result.format == "PNG"


def test_main_jpg_output(tmp_path):
    img_path = tmp_path / "input.png"
    _create_test_image(img_path)
    output_path = tmp_path / "output.jpg"
    main([str(img_path), "-o", str(output_path)])

    assert output_path.exists()
    with Image.open(output_path) as result:
        assert result.format == "JPEG"


def test_main_count_modifier(tmp_path):
    img_path = tmp_path / "input.png"
    _create_test_image(img_path)
    output_path = tmp_path / "output.pdf"
    main([str(img_path), "3", "-o", str(output_path)])

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_main_size_modifier(tmp_path):
    img_path = tmp_path / "input.png"
    _create_test_image(img_path)
    output_path = tmp_path / "output.pdf"
    main([str(img_path), "large:2", "-o", str(output_path)])

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_main_multiple_images(tmp_path):
    img1 = tmp_path / "a.png"
    img2 = tmp_path / "b.jpg"
    _create_test_image(img1, color=(255, 0, 0))
    _create_test_image(img2, color=(0, 0, 255))
    output_path = tmp_path / "output.pdf"
    main([str(img1), str(img2), "small:2", "-o", str(output_path)])

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_main_no_args_exits():
    with pytest.raises(SystemExit, match="2"):
        main([])
