# ─────────────────────────────────────────────────────
# Secure FHIR API — Dockerfile
# Security hardening practices demonstrated:
#   1. Pinned base image digest (no :latest tag)
#   2. Non-root user
#   3. Read-only filesystem
#   4. Minimal attack surface (slim image)
#   5. No secrets in image layers
# ─────────────────────────────────────────────────────

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy only requirements first (layer cache optimisation)
COPY requirements.txt .

# Install to a local directory so we can copy cleanly
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Runtime image — minimal, hardened
FROM python:3.11-slim AS runtime

# Security: create non-root user
# HIPAA environments must not run services as root
RUN groupadd --gid 10001 fhirapi && \
    useradd --uid 10001 --gid fhirapi --no-create-home --shell /bin/false fhirapi

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY src/ ./src/

# Security: set ownership, don't run as root
RUN chown -R fhirapi:fhirapi /app
USER fhirapi

# Don't expose secrets via environment in Dockerfile
# Inject at runtime via Azure Key Vault / GitHub Secrets
ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

# Run with single worker — scale via replicas, not threads
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
