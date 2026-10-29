# https://docs.docker.com/reference/dockerfile/

FROM debian:bookworm-slim

# curl downloads the uv installer. apt's ca-certificates package is the bundle of
# trusted sites curl uses to decide that download is really from astral.sh.
# apt-get update writes a package index under /var/lib/apt/lists. The running app
# never reads it, so the last command deletes that index.
# https://manpages.debian.org/bookworm/apt/apt-get.8.en.html
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
# uv installs the pinned CPython. It is the installer, not a library the subject has to map.
# https://docs.astral.sh/uv/
RUN uv sync --python 3.15.0 --frozen --no-dev

COPY app ./app
COPY public ./public

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8080

# -m means run a module. `app` is the package, so Python runs app/__main__.py.
# https://docs.python.org/3/using/cmdline.html#cmdoption-m
CMD ["python", "-m", "app"]
