FROM python:3.12-slim
RUN pip install --no-cache-dir playwright==1.63.0 && playwright install --with-deps chromium
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/*
WORKDIR /verifier
COPY stage-2/*.py /verifier/stage-2/
COPY stage-1/*.py /verifier/stage-1/
WORKDIR /verifier/stage-2
ENTRYPOINT ["python", "browser.py"]

COPY stage-3/*.py /verifier/stage-3/
