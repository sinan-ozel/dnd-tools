# frp-tools

An MCP server with tools related to Fantasy Role Playing games, to assist DMs.

## Tools

### `markdown_to_parchment`

Renders markdown text onto a parchment background image and returns a base64-encoded PNG.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `markdown_text` | string | required | Markdown to render. Supports `# H1`, `## H2`, `### H3`, `**bold**`, `*italic*`, `- list`. At default settings, a 600×800 px background fits ~150–200 words. |
| `background_image_path` | string | required | Absolute path to the parchment background image inside the container (PNG, JPEG, or WebP). |
| `font` | string | `cinzel` | `cinzel` — classical Roman style. `im_fell_english` — historical English document style with italic support. |
| `font_size` | integer | `20` | Base font size in pixels (12–48). Heading sizes scale from this value. |
| `margin_x` | integer | `80` | Left and right margin in pixels. |
| `margin_y` | integer | `80` | Top and bottom margin in pixels. |

**Returns:** Base64-encoded PNG string on success, or an error string starting with `Error: text_too_large` if the text does not fit.

## Quickstart

```yaml
services:
  frp-tools:
    image: sinanozel/frp-tools:latest
    ports:
      - "8000:8000"
    volumes:
      - /path/to/your/images:/images
```

The MCP endpoint is available at `http://localhost:8000/mcp`.

## Fonts

Both fonts are licensed under the [SIL Open Font License 1.1](https://scripts.sil.org/OFL):

- **Cinzel** — classical Roman style, downloaded from [Google Fonts](https://fonts.google.com/specimen/Cinzel)
- **IM Fell English** — historical English document style, downloaded from [Google Fonts](https://fonts.google.com/specimen/IM+Fell+English)
