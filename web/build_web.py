"""Build the static web GUI for rpgpawns into dist/rpgpawns.html."""

import base64
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML_TEMPLATE = ROOT / "web" / "template.html"
DIST_DIR = ROOT / "dist"

# Placeholders replaced with wheel data after building
WHEEL_B64_PLACEHOLDER = "__RPGPAWNS_WHEEL_B64__"
WHEEL_NAME_PLACEHOLDER = "__RPGPAWNS_WHEEL_NAME__"


def main() -> None:
    wheels = list(DIST_DIR.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"Expected exactly one wheel, got: {wheels}")
    wheel = wheels[0]
    wheel_b64 = base64.b64encode(wheel.read_bytes()).decode()

    html_tpl = HTML_TEMPLATE.read_text(encoding="utf-8")
    html = html_tpl.replace(WHEEL_B64_PLACEHOLDER, wheel_b64).replace(
        WHEEL_NAME_PLACEHOLDER, wheel.name
    )
    out_path = DIST_DIR / "rpgpawns.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Built: {out_path}")


if __name__ == "__main__":
    main()
