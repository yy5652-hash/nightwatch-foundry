FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /verifier
COPY opaque_id_probe.py opaque_id_requirements.py semantic_probe.py semantic_oracle.py semantic_requirements.py health.py /verifier/
ENTRYPOINT ["python", "/verifier/opaque_id_probe.py"]
