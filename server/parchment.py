"""Render markdown text onto a parchment background image."""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = Path(
    os.environ.get("DND_FONTS_DIR", str(Path(__file__).parent / "fonts"))
)

ASSETS_DIR = Path(
    os.environ.get("DND_ASSETS_DIR", str(Path(__file__).parent / "assets" / "images"))
)


class ParchmentFont(str, Enum):
    CINZEL = "cinzel"
    IM_FELL_ENGLISH = "im_fell_english"


class ParchmentBackground(str, Enum):
    ELEGANT_PARCHMENT_WITH_SIDES = "elegant_parchment_with_sides"


BACKGROUND_PATHS: dict[ParchmentBackground, Path] = {
    ParchmentBackground.ELEGANT_PARCHMENT_WITH_SIDES: ASSETS_DIR
    / "OIP.RxJTzmYmm57sGbD4vhP6LwAAAA.webp",
}


FONT_LABEL = {
    ParchmentFont.CINZEL: "Cinzel (classical Roman style, SIL OFL)",
    ParchmentFont.IM_FELL_ENGLISH: "IM Fell English (historical document style, SIL OFL)",
}


class TextTooLargeError(ValueError):
    """Text does not fit within the parchment margins at the given font
    size."""


@dataclass
class _Run:
    text: str
    bold: bool = False
    italic: bool = False


@dataclass
class _Block:
    runs: list[_Run] = field(default_factory=list)
    level: int = 0  # 1=h1, 2=h2, 3=h3, 0=paragraph, -1=list item


# ── Font loading ──────────────────────────────────────────────────────────────


def _font_paths(font: ParchmentFont) -> dict[str, Path]:
    d = FONTS_DIR
    if font == ParchmentFont.CINZEL:
        # Single variable font file; wght axis selects Regular (400) vs Bold (700).
        vf = d / "Cinzel[wght].ttf"
        return {"regular": vf, "bold": vf, "italic": vf}
    return {
        "regular": d / "IMFellEnglish-Regular.ttf",
        "bold": d / "IMFellEnglish-Regular.ttf",  # no bold variant
        "italic": d / "IMFellEnglish-Italic.ttf",
    }


def _load_fonts(
    font: ParchmentFont, base_size: int
) -> dict[str, ImageFont.FreeTypeFont]:
    paths = _font_paths(font)
    is_variable = font == ParchmentFont.CINZEL

    def load(
        key: str, size: int, wght: int | None = None
    ) -> ImageFont.FreeTypeFont:
        fnt = ImageFont.truetype(str(paths[key]), size)
        if is_variable and wght is not None:
            try:
                fnt.set_variation_by_axes([wght])
            except (OSError, AttributeError):
                pass
        return fnt

    return {
        "body": load("regular", base_size, wght=400),
        "bold": load("bold", base_size, wght=700),
        "italic": load("italic", base_size, wght=400),
        "h1": load("bold", int(base_size * 2.0), wght=700),
        "h2": load("bold", int(base_size * 1.5), wght=700),
        "h3": load("bold", int(base_size * 1.2), wght=700),
    }


# ── Markdown parsing ──────────────────────────────────────────────────────────


_INLINE_RE = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*|_(.+?)_")


def _parse_inline(text: str) -> list[_Run]:
    runs: list[_Run] = []
    last = 0
    for m in _INLINE_RE.finditer(text):
        if m.start() > last:
            runs.append(_Run(text[last : m.start()]))
        if m.group(1) is not None:
            runs.append(_Run(m.group(1), bold=True))
        else:
            runs.append(_Run(m.group(2) or m.group(3), italic=True))
        last = m.end()
    if last < len(text):
        runs.append(_Run(text[last:]))
    return runs or [_Run(text)]


def _parse_markdown(text: str) -> list[_Block]:
    blocks: list[_Block] = []
    para_lines: list[str] = []

    def flush():
        combined = " ".join(para_lines).strip()
        if combined:
            blocks.append(_Block(runs=_parse_inline(combined), level=0))
        para_lines.clear()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
        elif line.startswith("### "):
            flush()
            blocks.append(_Block(runs=_parse_inline(line[4:]), level=3))
        elif line.startswith("## "):
            flush()
            blocks.append(_Block(runs=_parse_inline(line[3:]), level=2))
        elif line.startswith("# "):
            flush()
            blocks.append(_Block(runs=_parse_inline(line[2:]), level=1))
        elif line.startswith(("- ", "* ")):
            flush()
            blocks.append(
                _Block(runs=[_Run("• ")] + _parse_inline(line[2:]), level=-1)
            )
        else:
            para_lines.append(line)

    flush()
    return blocks


# ── Layout helpers ────────────────────────────────────────────────────────────


def _pick_font(run: _Run, block: _Block, fonts: dict) -> ImageFont.FreeTypeFont:
    if block.level == 1:
        return fonts["h1"]
    if block.level == 2:
        return fonts["h2"]
    if block.level == 3:
        return fonts["h3"]
    if run.bold:
        return fonts["bold"]
    if run.italic:
        return fonts["italic"]
    return fonts["body"]


def _text_w(
    draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont
) -> int:
    bb = draw.textbbox((0, 0), text, font=fnt)
    return bb[2] - bb[0]


def _line_h(draw: ImageDraw.ImageDraw, fnt: ImageFont.FreeTypeFont) -> int:
    bb = draw.textbbox((0, 0), "Ag", font=fnt)
    return int((bb[3] - bb[1]) * 1.3)


def _wrap_block(
    block: _Block,
    fonts: dict,
    draw: ImageDraw.ImageDraw,
    text_width: int,
) -> list[list[tuple[str, ImageFont.FreeTypeFont]]]:
    """Word-wrap a block's runs into display lines of (word, font) pairs."""
    words: list[tuple[str, ImageFont.FreeTypeFont]] = []
    for run in block.runs:
        fnt = _pick_font(run, block, fonts)
        for i, word in enumerate(run.text.split()):
            if word:
                words.append((word, fnt))

    lines: list[list[tuple[str, ImageFont.FreeTypeFont]]] = []
    current: list[tuple[str, ImageFont.FreeTypeFont]] = []
    current_w = 0

    for word, fnt in words:
        w = _text_w(draw, word, fnt)
        space_w = _text_w(draw, " ", fnt)
        needed = w if not current else space_w + w

        if current and current_w + needed > text_width:
            lines.append(current)
            current = [(word, fnt)]
            current_w = w
        else:
            current.append((word, fnt))
            current_w += needed

    if current:
        lines.append(current)
    return lines


def _block_spacing(block: _Block, base_size: int) -> int:
    """Vertical space added after a block."""
    if block.level == 1:
        return int(base_size * 1.4)
    if block.level == 2:
        return int(base_size * 1.1)
    if block.level == 3:
        return int(base_size * 0.9)
    if block.level == -1:
        return int(base_size * 0.3)
    return int(base_size * 0.7)


# ── Public API ────────────────────────────────────────────────────────────────


def render_parchment(
    markdown_text: str,
    background_path: str | Path,
    font: ParchmentFont = ParchmentFont.CINZEL,
    font_size: int = 20,
    margin_x: int = 80,
    margin_y: int = 80,
    text_color: tuple[int, int, int] = (50, 25, 5),
) -> bytes:
    """Render markdown onto a parchment background image.

    Returns PNG bytes. Raises TextTooLargeError if the text overflows the
    available area (image height minus top/bottom margins).
    """
    img = Image.open(background_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    img_w, img_h = img.size

    fonts = _load_fonts(font, font_size)
    text_w = img_w - 2 * margin_x
    available_h = img_h - 2 * margin_y

    blocks = _parse_markdown(markdown_text)

    # Pre-calculate total height needed before drawing anything.
    total_h = 0
    wrapped_blocks: list[list[list[tuple[str, ImageFont.FreeTypeFont]]]] = []
    for block in blocks:
        lines = _wrap_block(block, fonts, draw, text_w)
        wrapped_blocks.append(lines)
        # Dominant font for height calculation
        dominant = _pick_font(
            block.runs[0] if block.runs else _Run(""), block, fonts
        )
        lh = _line_h(draw, dominant)
        total_h += lh * len(lines) + _block_spacing(block, font_size)

    if total_h > available_h:
        raise TextTooLargeError(
            f"Text needs {total_h}px but only {available_h}px is available "
            f"(image height {img_h}px minus {margin_y}px top/bottom margins). "
            "Reduce text, use a smaller font_size, or use a larger background image."
        )

    y = margin_y
    for block, lines in zip(blocks, wrapped_blocks):
        dominant = _pick_font(
            block.runs[0] if block.runs else _Run(""), block, fonts
        )
        lh = _line_h(draw, dominant)
        is_heading = block.level in (1, 2, 3)

        for line in lines:
            line_w = sum(_text_w(draw, w, f) for w, f in line) + _text_w(
                draw, " ", dominant
            ) * (len(line) - 1)
            x = (img_w - line_w) // 2 if is_heading else margin_x

            for i, (word, fnt) in enumerate(line):
                if i > 0:
                    draw.text((x, y), " ", font=dominant, fill=text_color)
                    x += _text_w(draw, " ", dominant)
                draw.text((x, y), word, font=fnt, fill=text_color)
                x += _text_w(draw, word, fnt)
            y += lh

        y += _block_spacing(block, font_size)

    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()
