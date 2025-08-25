###############################
# Stage 1: Builder
###############################
FROM python:3.13-slim AS builder

WORKDIR /app

# Install necessary system dependencies (e.g., curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a Python virtual environment
RUN python -m venv /opt/venv

# Copy requirements and install dependencies into the virtual environment
COPY requirements.txt /app/
RUN /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the complete application code
#COPY . /app

###############################
# Stage 2: Runtime
###############################
FROM python:3.13-slim

# Set environment variables for runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated non-root user before setting ownership
RUN useradd -m appuser

# Copy the virtual environment and application code from the builder stage
COPY --from=builder /opt/venv /opt/venv
#COPY --from=builder /app /app

# Ensure the necessary directory structure exists
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Expose Streamlit's default port
EXPOSE 8501

# Health Check: Ensure the Streamlit service is responsive on port 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/ || exit 1

# Switch to the non-root user
USER appuser

# Set the working directory for running the application
WORKDIR /app

# Ensure the frontend starts correctly
CMD ["/opt/venv/bin/streamlit", "run", "src/frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]