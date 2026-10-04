FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /verifier
COPY nesting_probe.py nesting_input.py nesting_requirements.py semantic_probe.py semantic_oracle.py semantic_requirements.py health.py /verifier/
ENTRYPOINT ["python", "/verifier/nesting_probe.py"]
