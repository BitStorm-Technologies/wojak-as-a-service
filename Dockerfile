FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY classifier.py bot.py wojak_index.json ./
COPY wojack_source_images ./wojack_source_images

CMD ["uv", "run", "--no-sync", "python", "bot.py"]
