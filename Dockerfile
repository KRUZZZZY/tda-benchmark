# TDA Pipeline Benchmark — pinned build environment
# Reproduces the exact environment the dissertation results were produced
# under (Python 3.12.3; giotto-tda 0.6.2 is load-bearing for the fragility
# and runtime findings — see REPRODUCING.md).
FROM python:3.12.3-slim

# giotto-tda 0.6.2 and gudhi compile from source on this base image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Smoke check that the pinned stack imports and the framework loads.
RUN python -c "import giotto, ripser, gudhi, sklearn; print('pinned stack OK')"
RUN python tests/run_smoke.py

CMD ["bash"]
