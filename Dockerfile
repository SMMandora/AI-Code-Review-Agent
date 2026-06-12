FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml ./
COPY codereview ./codereview
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
RUN useradd --create-home appuser
WORKDIR /app
COPY --from=build /install /usr/local
COPY scripts ./scripts
USER appuser
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn codereview.web.app:create_app --factory --host 0.0.0.0 --port ${PORT}"]
