FROM python:3.12-slim

# OCI build-time arguments — populated by CI from pyproject.toml and git context.
# Default to empty strings so local builds work without --build-arg.
ARG VERSION
ARG BUILD_DATE
ARG GIT_REVISION
ARG TITLE
ARG DESCRIPTION
ARG AUTHORS
ARG LICENSES
ARG SOURCE_URL
ARG DOCS_URL
ARG IMAGE_URL

WORKDIR /app

# wget: fetches fonts at build time.
# libjpeg-dev / libpng-dev / libwebp-dev / zlib1g-dev: Pillow build deps
# (needed when no manylinux wheel matches the build platform).
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget \
        libjpeg-dev \
        libpng-dev \
        libwebp-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY README.md .
COPY server/ ./server/

RUN pip install --no-cache-dir -e "."

# Fonts — both SIL Open Font License 1.1.
# raw.githubusercontent.com blocks wget's default User-Agent; --user-agent overrides that.
# Cinzel is a variable font (one file, wght axis 400-900).
# IM Fell English uses historical filenames — saved under clean names.
# Target: /app/server/fonts/ — where parchment.py resolves by default.
RUN mkdir -p /app/server/fonts && \
    wget --user-agent="Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0" \
        -O "/app/server/fonts/Cinzel[wght].ttf" \
        "https://raw.githubusercontent.com/google/fonts/refs/heads/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf" && \
    wget --user-agent="Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0" \
        -O /app/server/fonts/IMFellEnglish-Regular.ttf \
        "https://raw.githubusercontent.com/google/fonts/refs/heads/main/ofl/imfellenglish/IMFeENrm28P.ttf" && \
    wget --user-agent="Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0" \
        -O /app/server/fonts/IMFellEnglish-Italic.ttf \
        "https://raw.githubusercontent.com/google/fonts/refs/heads/main/ofl/imfellenglish/IMFeENit28P.ttf"

EXPOSE 8000

# https://github.com/opencontainers/image-spec/blob/main/annotations.md
LABEL org.opencontainers.image.title="${TITLE}" \
      org.opencontainers.image.description="${DESCRIPTION}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.authors="${AUTHORS}" \
      org.opencontainers.image.licenses="${LICENSES}" \
      org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.documentation="${DOCS_URL}" \
      org.opencontainers.image.url="${IMAGE_URL}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_REVISION}"

CMD ["python", "server/main.py"]
