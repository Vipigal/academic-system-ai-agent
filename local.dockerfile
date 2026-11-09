FROM ghcr.io/astral-sh/uv:0.13.7 AS uv

FROM python:3.14.10-slim-trixie

COPY --from=uv /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PATH="/srv/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

USER 10001:10001

EXPOSE 8000

# O código não entra na imagem: o Compose monta src/api e o --app-dir src faz o import vir da cópia montada.
CMD ["uvicorn", "--factory", "api.bootstrap.app:ApiFactory.create", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--reload", "--reload-dir", "src/api"]
