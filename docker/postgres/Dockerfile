###############################
# Stage 1: Builder
###############################
FROM postgres:17 AS builder

# Set up environment variables (will be passed from docker-compose.yml)
ENV DB_USER=${DB_USER} \
    DB_PASSWORD=${DB_PASSWORD} \
    DB_NAME=${DB_NAME}

# Create a directory for custom initialization scripts
RUN mkdir -p /docker-entrypoint-initdb.d

# Copy any custom SQL initialization scripts
COPY src/sql/*.sql /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432


###############################
# Stage 2: Runtime
###############################
FROM postgres:17

# Copy initialization files from the builder stage
COPY --from=builder /docker-entrypoint-initdb.d /docker-entrypoint-initdb.d

# Set proper ownership and permissions
RUN mkdir -p /var/lib/postgresql && \
    chown -R postgres:postgres /var/lib/postgresql /docker-entrypoint-initdb.d && \
    chmod -R 700 /var/lib/postgresql

# Switch to non-root user
USER postgres

# Health Check: Ensure the database is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD pg_isready -U "$DB_USER" -d "$DB_NAME" || exit 1

# Default command
CMD ["postgres"]