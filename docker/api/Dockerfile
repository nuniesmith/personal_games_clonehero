###############################
# Stage 1: Builder
###############################
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies for package building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    p7zip-full \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create a Python virtual environment
RUN python -m venv /opt/venv

# Copy dependencies and install them in the virtual environment
COPY requirements.txt /app/requirements.txt
RUN /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

###############################
# Stage 2: Runtime
###############################
FROM python:3.13-slim

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install only necessary runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    p7zip-full \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create a dedicated non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Expose the API port
EXPOSE 8000

# Health Check: Ensure the API is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Switch to non-root user
USER appuser

# Start Gunicorn with Uvicorn workers
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "src.api.main:app"]