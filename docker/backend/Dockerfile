###############################
# Stage 1: Builder
###############################
FROM python:3.13-slim AS builder

WORKDIR /app

# Install dependencies for worker tasks (including RAR extraction)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    p7zip-full \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv

# Copy requirements and install them
COPY requirements.txt /app/requirements.txt
RUN /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

###############################
# Stage 2: Runtime
###############################
FROM python:3.13-slim

# Runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    p7zip-full \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated non-root user
RUN useradd -m appuser

# Copy the virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Ensure necessary directories exist
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Expose port for monitoring
EXPOSE 8001

# Health Check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8001/health || exit 1

# Switch to non-root user
USER appuser

# Start the worker
CMD ["/opt/venv/bin/python", "src/backend/worker.py"]