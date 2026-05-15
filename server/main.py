import base64
import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from server.parchment import (
    BACKGROUND_PATHS,
    ParchmentBackground,
    ParchmentFont,
    TextTooLargeError,
    render_parchment,
)

mcp = FastMCP("dnd-tools")


class _SuppressMCPUnionValidation(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.getMessage().startswith("Failed to validate request:")


logging.getLogger().addFilter(_SuppressMCPUnionValidation())


@mcp.tool()
def markdown_to_parchment(
    markdown_text: Annotated[
        str,
        Field(
            description=(
                "Markdown text to render. Supported syntax: "
                "# H1, ## H2, ### H3, **bold**, *italic*, - list item. "
                "For a 600×800 px background with default settings "
                "(font_size=20, margin=80), roughly 150–200 words fit. "
                "A 1000×1400 px background fits roughly 400–600 words. "
                "Headings count as 2–3 body lines each due to their larger size."
            )
        ),
    ],
    background: Annotated[
        ParchmentBackground,
        Field(
            default=ParchmentBackground.ELEGANT_PARCHMENT_WITH_SIDES,
            description=(
                "'elegant_parchment_with_sides' — warm aged parchment with decorative side borders."
            ),
        ),
    ] = ParchmentBackground.ELEGANT_PARCHMENT_WITH_SIDES,
    font: Annotated[
        ParchmentFont,
        Field(
            default=ParchmentFont.CINZEL,
            description=(
                "'cinzel' — classical Roman style, elegant all-caps. "
                "'im_fell_english' — historical English document style with italic support."
            ),
        ),
    ] = ParchmentFont.CINZEL,
    font_size: Annotated[
        int,
        Field(
            default=20,
            ge=12,
            le=48,
            description="Base font size in pixels. Heading sizes scale from this value.",
        ),
    ] = 20,
    margin_x: Annotated[
        int,
        Field(default=80, ge=0, description="Left and right margin in pixels."),
    ] = 80,
    margin_y: Annotated[
        int,
        Field(default=80, ge=0, description="Top and bottom margin in pixels."),
    ] = 80,
) -> str:
    """Render markdown text onto a parchment background image.

    Returns a base64-encoded PNG string on success, or an error message
    (starting with "Error: text_too_large") if the text does not fit.
    """
    try:
        image_bytes = render_parchment(
            markdown_text=markdown_text,
            background_path=BACKGROUND_PATHS[background],
            font=font,
            font_size=font_size,
            margin_x=margin_x,
            margin_y=margin_y,
        )
        return base64.b64encode(image_bytes).decode("utf-8")
    except TextTooLargeError as e:
        return f"Error: text_too_large — {e}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
