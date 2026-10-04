FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /verifier
COPY requirements.py probe.py health.py supplemental.py reproduce.py calendar_edges.py reproduce_calendar.py race50.py wire_oracle.py legacy_receipts_current.py decimal_requirements.py decimal_probe.py large_minutes.py /verifier/
ENTRYPOINT ["python", "/verifier/probe.py"]
