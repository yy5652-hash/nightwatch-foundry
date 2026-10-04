FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /verifier
COPY decoder_probe.py decoder_oracle.py decoder_requirements.py semantic_oracle.py health.py /verifier/
ENTRYPOINT ["python", "/verifier/decoder_probe.py"]
