###############################
# Stage 1: Builder
###############################
FROM syncthing/syncthing:latest AS builder

# Set working directory
WORKDIR /var/syncthing

###############################
# Stage 2: Runtime
###############################
FROM syncthing/syncthing:latest

# Set working directory
WORKDIR /var/syncthing

# Create a non-root user and set permissions
RUN addgroup -S syncthinguser && \
    adduser -S -G syncthinguser syncthinguser && \
    mkdir -p /var/syncthing/config && \
    chown -R syncthinguser:syncthinguser /var/syncthing && \
    chmod -R 755 /var/syncthing

# Switch to non-root user
USER syncthinguser

# Set up runtime environment
ENV STGUIADDRESS="0.0.0.0:8384"
ENV STNORESTART=1

# Expose necessary ports
EXPOSE 8384 22000/tcp 21027/udp

# Health Check: Ensure Syncthing UI is accessible
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8384 || exit 1

# Ensure syncthing starts correctly as a non-root user
ENTRYPOINT ["syncthing", "-home=/var/syncthing/config"]