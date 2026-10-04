FROM python:3.12-slim-bookworm

# IANA rules are present in the single image, including at offline runtime.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY server.py core.py ./
COPY web ./web
RUN python -c "import ast,pathlib; [ast.parse(p.read_text()) for p in pathlib.Path('.').glob('*.py')]"
USER 65532:65532
EXPOSE 8080
CMD ["python", "server.py"]
