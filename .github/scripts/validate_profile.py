#!/usr/bin/env python3
"""Validate the TFLives Studio organization profile without external dependencies."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "profile" / "README.md"
ASSETS = ROOT / "assets"
DESTINATIONS = (
    "https://www.tflives.com/",
    "https://discord.gg/tflives",
    "https://modrinth.com/organization/tflives",
    "https://builtbybit.com/members/tflives.551539/",
)


class ReadmeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "img":
            self.images.append(data)
        if tag == "a" and data.get("href"):
            self.links.append(data["href"])


def main():
    errors = []
    svg_files = sorted(ASSETS.glob("*.svg"))

    if not svg_files:
        errors.append("No SVG assets were found.")

    for asset in svg_files:
        try:
            tree = ET.parse(asset)
            if not tree.getroot().tag.endswith("svg"):
                errors.append(f"{asset.name}: root is not an SVG element.")
        except ET.ParseError as exc:
            errors.append(f"{asset.name}: invalid SVG XML: {exc}")

    readme = PROFILE.read_text(encoding="utf-8")
    parser = ReadmeParser()
    parser.feed(readme)

    if not parser.images:
        errors.append("No profile images found.")

    for image in parser.images:
        src = image.get("src", "")
        if not src.startswith("../assets/"):
            errors.append(f"Use local relative asset paths; found: {src!r}")
            continue

        target = (PROFILE.parent / src).resolve()
        if not target.is_relative_to(ASSETS.resolve()):
            errors.append(f"Image escapes assets/: {src}")
        elif not target.is_file():
            errors.append(f"Missing referenced image: {src}")
        if not image.get("alt"):
            errors.append(f"Missing alternative text: {src}")

    for destination in DESTINATIONS:
        if destination not in parser.links:
            errors.append(f"Missing official destination: {destination}")

    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        return 1

    print(f"PASS: {len(svg_files)} well-formed SVGs, {len(parser.images)} local images, all official links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
