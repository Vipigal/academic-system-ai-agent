FROM python:3.14.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /srv

COPY pyproject.toml ./
COPY src/api ./src/api

RUN pip install --no-cache-dir --root-user-action=ignore .

USER nobody

EXPOSE 8000

CMD ["uvicorn", "--factory", "api.main:ApiFactory.create", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
