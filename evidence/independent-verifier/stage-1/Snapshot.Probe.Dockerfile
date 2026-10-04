FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /verifier
COPY snapshot_probe.py snapshot_oracle.py snapshot_requirements.py semantic_probe.py semantic_oracle.py semantic_requirements.py health.py /verifier/
ENTRYPOINT ["python", "/verifier/snapshot_probe.py"]
