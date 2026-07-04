# ═══════════════════════════════════════════════════════════════════════════
#  Credit Risk Model — Optimized Serving Image
#  Base: python:3.10-slim (vs default Ubuntu 20.04 + 150 bloat packages)
#  Build time: ~3-5 min  |  Image size: ~500 MB  (was: 30 min / ~3 GB)
#
#  DevSecOps notes:
#    - Multi-stage build: builder → runtime (no build tools in final image)
#    - Non-root user (uid=1000) for runtime security
#    - No unnecessary OS packages (no X11, LLVM, Mesa, xterm, etc.)
# ═══════════════════════════════════════════════════════════════════════════

# ── Stage 1: Builder ──────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /install

# Install serving dependencies only (pinned versions for reproducibility)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        mlflow==2.19.0 \
        scikit-learn==1.5.2 \
        numpy==1.26.4 \
        pandas==2.2.3 \
        gunicorn==21.2.0 \
        uvicorn==0.30.1

# ── Stage 2: Runtime ──────────────────────────────────────────────────────
FROM python:3.10-slim

LABEL maintainer="Adrian Syah Abidin <adriansyah0904>"
LABEL description="Credit Risk Prediction Model - MLflow Serving"
LABEL version="1.0"

# DevSecOps: create non-root user
RUN groupadd -r mluser && useradd -r -g mluser -u 1000 mluser

WORKDIR /app

# Copy installed packages from builder stage (no pip in final image)
COPY --from=builder /usr/local/lib/python3.10/site-packages \
                    /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin \
                    /usr/local/bin

# Copy the saved model artifact
# (produced by mlflow.sklearn.save_model in modelling.py)
COPY artifacts/credit-risk-model /app/model

# Set ownership to non-root user
RUN chown -R mluser:mluser /app

# Switch to non-root
USER mluser

# Expose serving port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/ping')" || exit 1

# Serve model via MLflow built-in server (no conda, no extra dependencies)
CMD ["mlflow", "models", "serve", \
     "--model-uri", "/app/model", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--no-conda"]
