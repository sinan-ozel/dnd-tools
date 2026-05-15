import base64
import struct

import pytest
from fastmcp import Client

pytestmark = pytest.mark.anyio

# Dimensions of elegant_parchment_with_sides (read from VP8X header of the source WebP).
_BACKGROUND_W, _BACKGROUND_H = 474, 609

_SHORT_MD = """\
# The Dragon's Hoard

Deep in the mountain lies a trove of ancient gold, jealously guarded.
"""

# Enough paragraphs to overflow any reasonable parchment at default settings.
_LONG_MD = "# Ancient Lore\n\n" + (
    "The realm stretches beyond the horizon. " * 200
)


def _png_dimensions(b64: str) -> tuple[int, int]:
    raw = base64.b64decode(b64)
    width, height = struct.unpack(">II", raw[16:24])
    return width, height


async def test_tool_is_listed(mcp_url):
    async with Client(mcp_url) as client:
        tools = await client.list_tools()
    names = [t.name for t in tools]
    assert "markdown_to_parchment" in names


async def test_large_text_returns_error(mcp_tools):
    result = await mcp_tools(
        "markdown_to_parchment",
        markdown_text=_LONG_MD,
        background="elegant_parchment_with_sides",
    )
    text = result.get("result", result.get("text", ""))
    assert text.startswith(
        "Error: text_too_large"
    ), f"expected a text_too_large error, got: {text[:200]}"


async def test_proper_text_returns_same_size_image(mcp_tools):
    result = await mcp_tools(
        "markdown_to_parchment",
        markdown_text=_SHORT_MD,
        background="elegant_parchment_with_sides",
    )
    b64 = result.get("result", result.get("text", ""))
    assert not b64.startswith("Error:"), f"unexpected error: {b64[:200]}"

    out_w, out_h = _png_dimensions(b64)
    assert (out_w, out_h) == (
        _BACKGROUND_W,
        _BACKGROUND_H,
    ), f"output size {out_w}×{out_h} != background size {_BACKGROUND_W}×{_BACKGROUND_H}"
