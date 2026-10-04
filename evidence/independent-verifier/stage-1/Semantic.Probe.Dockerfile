FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /verifier
COPY semantic_probe.py semantic_oracle.py semantic_requirements.py health.py /verifier/
ENTRYPOINT ["python", "/verifier/semantic_probe.py"]
