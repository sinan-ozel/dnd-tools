![CI/CD](https://github.com/sinanozel/frp-tools/actions/workflows/ci.yaml/badge.svg?branch=main)
![Docker Hub](https://img.shields.io/docker/v/sinanozel/frp-tools?label=Docker%20Hub)
![License](https://img.shields.io/github/license/sinanozel/frp-tools.svg)

# DnD Tools MCP Server

An MCP server with tools related to Fantasy Role Playing games, to assist Dungeon Masters. Built with [FastMCP](https://github.com/jlowin/fastmcp) and running on Docker — no local Python installation required.

## Tools

### `markdown_to_parchment`

Renders markdown text onto a parchment background image and returns a base64-encoded PNG.

**Inputs:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `markdown_text` | string | required | Markdown to render (supports `#` headings, `**bold**`, `*italic*`, `- lists`) |
| `background_image_path` | string | required | Path to the parchment background image inside the container |
| `font` | enum | `cinzel` | `cinzel` — classical Roman style; `im_fell_english` — historical English document style |
| `font_size` | int | `20` | Base font size in px (12–48). Headings scale proportionally. |
| `margin_x` | int | `80` | Left/right margin in pixels |
| `margin_y` | int | `80` | Top/bottom margin in pixels |

Returns an error string if the text is too large to fit within the margins.

**Providing the background image:** mount a directory into the container (see Quickstart) and pass the in-container path, e.g. `/images/parchment.png`.

**Fonts (SIL Open Font License):**
- **Cinzel** — elegant all-caps Roman style, ideal for titles and formal text
- **IM Fell English** — historical English document feel, with an italic variant

## What's Included

- **MCP server** — `server/main.py` using FastMCP with **Streamable HTTP** transport on port 8000
- **Business logic** — `server/parchment.py` (importable independently of MCP)
- **Containerized tooling** — reformat, lint, validate-docs, and test all run via `docker compose`
- **MCP Inspector** — visual browser UI for testing and debugging your tools
- **Automated CI/CD** — GitHub Actions that reformat on branches, lint + test on every push, publish to Docker Hub on main
- **SemVer releases** — stable vs. dev version logic driven by `server/__init__.py`
- **VS Code tasks** — one-click access to every workflow from the Command Palette

---

## Quickstart

### 1. Clone and build

```bash
git clone https://github.com/sinanozel/frp-tools.git
cd frp-tools
```

### 2. Mount your parchment background image

Add a volume mount so the container can read your image. Edit `docker-compose.yaml` (or pass `-v`) to mount the directory containing your background image:

```yaml
volumes:
  - /path/to/your/images:/images:ro
```

Then pass `/images/parchment.png` as `background_image_path` in the tool.

### 3. Run the server

```bash
docker compose up --build
```

The MCP endpoint is at `http://localhost:8000/mcp`.

### 4. Set up Docker Hub secrets in GitHub

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | A Docker Hub access token (not your password) |

### 8. (Optional) Set up GitHub Pages for docs

Go to **Settings → Pages → Deploy from a branch**: `gh-pages`, `/` (root).

---

## MCP Transport

The server uses **Streamable HTTP** transport (the current MCP standard). The endpoint is at:

```
http://localhost:8000/mcp
```

Compatible with all MCP clients that support HTTP transport (Claude Desktop, Claude.ai, Cursor, etc.).

---

## Development

The only requirement is **Docker**.

### Run the tests

```bash
docker compose -f tests/docker-compose.yaml up --build --abort-on-container-exit --exit-code-from test
```

This starts the MCP server, waits for it to be healthy, then runs pytest against it with `pytest-mcp-tools`.

### Lint

```bash
docker compose -f lint/docker-compose.yaml up --build --abort-on-container-exit
```

### Reformat

```bash
docker compose -f reformat/docker-compose.yaml up --build --abort-on-container-exit
```

Reformatting runs `black`, `docformatter`, and `isort` on `server/` and `tests/`, then writes changes back to disk (via volume mount). On non-main branches CI commits these changes automatically.

### Validate docs

```bash
docker compose -f docs-validate/docker-compose.yaml up --build --abort-on-container-exit
```

### Run the MCP Inspector

```bash
docker compose -f inspector/docker-compose.yaml up --build
```

Then open the URL printed in the logs (includes the auth token):
```
http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<token>
```

---

## VS Code Tasks

Open **Terminal → Run Task** (or `Ctrl+Shift+P → Tasks: Run Task`):

| Task | What it does |
|---|---|
| `test` | Runs the full test suite (server + test runner containers) |
| `lint` | Runs ruff against `server/` and `tests/` |
| `reformat` | Formats code with black + docformatter + isort |
| `validate-docs` | Builds MkDocs site with `--strict` |
| `inspector` | Starts the server + MCP Inspector (leaves running in background) |

---

## CI/CD Pipeline

The workflow at [.github/workflows/ci.yaml](.github/workflows/ci.yaml) runs on every push and pull request:

```
push (any branch)
│
├── reformat        ← runs black/isort/docformatter
│   └── (commits reformatted code back, non-main branches only)
│
├── lint            ← ruff check (needs: reformat)
├── test            ← pytest --mcp-tools (needs: reformat)
├── validate-docs   ← mkdocs build --strict
└── detect-changes  ← checks if server/ or README changed
    │
    └── publish (main only, when changed)
        ├── Build & push Docker image to Docker Hub
        │   ├── stable:  <org>/<server>:1.2.3  +  :latest
        │   └── dev:     <org>/<server>:1.2.4.dev202401011200
        ├── Tag stable release in git
        ├── Create GitHub Release
        └── publish-docs (stable + docs exist)
            └── mike deploy to GitHub Pages
```

### Versioning

Version is read from `server/__init__.py`. The logic:

- If `__version__` > last git tag → **stable release** (tags git, pushes `:latest`)
- If `__version__` == last git tag → **dev release** (appends `.devYYYYMMDDHHMM`, no `:latest`)

Bump `__version__` in `server/__init__.py` to trigger a stable release on the next main push.

---

## Project Structure

```
.
├── Dockerfile                   # Builds and runs the MCP server
├── pyproject.toml               # Project metadata, dependencies, tool config
├── server/
│   ├── __init__.py              # __version__ = "x.y.z"
│   └── main.py                  # FastMCP server — add your tools here
├── tests/
│   ├── Dockerfile               # Test runner image
│   ├── docker-compose.yaml      # mcp-server + test-runner services
│   └── test_unit.py             # Placeholder — add your tests here
├── reformat/                    # black + docformatter + isort container
├── lint/                        # ruff container
├── docs-validate/               # mkdocs build container
├── inspector/                   # MCP Inspector + server for visual testing
├── scripts/
│   └── semver_compare.py        # Used by CI to compare versions
└── .github/workflows/ci.yaml    # Full CI/CD pipeline
```
