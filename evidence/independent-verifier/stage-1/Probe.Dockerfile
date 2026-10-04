FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /verifier
COPY requirements.py probe.py health.py supplemental.py reproduce.py calendar_edges.py reproduce_calendar.py race50.py /verifier/
ENTRYPOINT ["python", "/verifier/probe.py"]
