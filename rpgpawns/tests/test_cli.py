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
    assert parse_image_args(["a.jpg:3"]) == [("a.jpg", PawnSize.MEDIUM, 3)]


def test_parse_size_only():
    assert parse_image_args(["a.jpg:large"]) == [("a.jpg", PawnSize.LARGE, 1)]


def test_parse_size_and_count():
    assert parse_image_args(["a.jpg:small:2"]) == [("a.jpg", PawnSize.SMALL, 2)]


def test_parse_huge():
    assert parse_image_args(["a.jpg:huge:3"]) == [("a.jpg", PawnSize.HUGE, 3)]


def test_parse_medium_explicit():
    assert parse_image_args(["a.jpg:medium"]) == [("a.jpg", PawnSize.MEDIUM, 1)]


def test_parse_count_zero():
    with pytest.raises(ValueError, match="at least 1"):
        parse_image_args(["a.jpg:small:0"])


def test_parse_unknown_size():
    with pytest.raises(ValueError, match="Unknown size"):
        parse_image_args(["a.jpg:tiny:2"])


def test_parse_mixed_sizes():
    result = parse_image_args(["a.jpg:small:2", "b.png:large"])
    assert result == [
        ("a.jpg", PawnSize.SMALL, 2),
        ("b.png", PawnSize.LARGE, 1),
    ]


def test_parse_multiple_with_counts():
    result = parse_image_args(["a.jpg:2", "b.png:3"])
    assert result == [
        ("a.jpg", PawnSize.MEDIUM, 2),
        ("b.png", PawnSize.MEDIUM, 3),
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
    main([str(img_path) + ":3", "-o", str(output_path)])

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_main_size_modifier(tmp_path):
    img_path = tmp_path / "input.png"
    _create_test_image(img_path)
    output_path = tmp_path / "output.pdf"
    main([str(img_path) + ":large:2", "-o", str(output_path)])

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_main_multiple_images(tmp_path):
    img1 = tmp_path / "a.png"
    img2 = tmp_path / "b.jpg"
    _create_test_image(img1, color=(255, 0, 0))
    _create_test_image(img2, color=(0, 0, 255))
    output_path = tmp_path / "output.pdf"
    main([str(img1), str(img2) + ":small:2", "-o", str(output_path)])

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_main_no_args_exits():
    with pytest.raises(SystemExit, match="2"):
        main([])


def test_main_unknown_size_exits():
    """An unknown size in the image argument causes a parser error exit."""
    with pytest.raises(SystemExit, match="2"):
        main(["foo.jpg:tiny:2"])


def test_main_multi_page_pdf(tmp_path):
    """Many pawns produce a multi-page PDF without error."""
    img_path = tmp_path / "input.png"
    _create_test_image(img_path)
    output_path = tmp_path / "output.pdf"
    # huge:20 should overflow a single page
    main([str(img_path) + ":huge:20", "-o", str(output_path)])

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_main_multi_page_png_exits(tmp_path):
    """Multi-page output to a non-PDF format causes a parser error exit."""
    img_path = tmp_path / "input.png"
    _create_test_image(img_path)
    output_path = tmp_path / "output.png"
    with pytest.raises(SystemExit, match="2"):
        main([str(img_path) + ":huge:20", "-o", str(output_path)])
