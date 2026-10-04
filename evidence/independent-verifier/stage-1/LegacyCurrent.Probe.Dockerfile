FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /verifier
COPY requirements.py probe.py health.py wire_oracle.py legacy_receipts_current.py /verifier/
ENTRYPOINT ["python", "/verifier/legacy_receipts_current.py"]
