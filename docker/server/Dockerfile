###############################
# Stage 1: Builder
###############################
FROM ubuntu:22.04 AS builder

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /build

# Install all required build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    ca-certificates \
    libnss3 \
    libx11-6 \
    libxext6 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libglib2.0-0 \
    libglu1-mesa \
    libicu70 \
    icu-devtools \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# (Optional) Install OpenSSL 1.1 if required by the server
RUN echo "deb http://archive.ubuntu.com/ubuntu focal main universe" > /etc/apt/sources.list.d/focal.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends libssl1.1 \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/focal.list

# Download and extract the Clone Hero Server zip file
RUN wget -O server.zip "https://github.com/clonehero-game/releases/releases/download/V1.0.0.4080/CloneHero-standalone_server.zip" \
    && unzip server.zip -d /build/server \
    && rm server.zip

# Configure the Clone Hero Server by creating a config file
RUN echo "[Server]" > /build/server/config.ini && \
    echo "ServerName=Freddy" >> /build/server/config.ini && \
    echo "MaxPlayers=8" >> /build/server/config.ini && \
    echo "AllowGuests=false" >> /build/server/config.ini && \
    echo "Password=Ruby" >> /build/server/config.ini && \
    echo "Host=Freddy" >> /build/server/config.ini && \
    echo "Port=14242" >> /build/server/config.ini && \
    echo "EnableLogging=true" >> /build/server/config.ini

###############################
# Stage 2: Runtime
###############################
FROM ubuntu:22.04

# Prevent interactive prompts during runtime image build
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install only the minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libx11-6 \
    libxext6 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libglib2.0-0 \
    libglu1-mesa \
    libicu70 \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# (Optional) Install OpenSSL 1.1 if required by the server
RUN echo "deb http://archive.ubuntu.com/ubuntu focal main universe" > /etc/apt/sources.list.d/focal.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends libssl1.1 \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/focal.list

# Copy the prepared server files from the builder stage
COPY --from=builder /build/server/ChStandaloneServer-v1.0.0.4080-final /app

# Create a dedicated non-root user and adjust permissions
RUN useradd -m appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Switch to the non-root user for improved security
USER appuser

# Expose the default server port
EXPOSE 14242

# Set environment variables (example: instruct .NET to use installed ICU libraries)
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=0

# Ensure the server binary is executable (if not already)
RUN chmod +x /app/linux-x64/Server

# Default Entrypoint: launch the Clone Hero Server binary
CMD ["/bin/bash", "-c", "tail -f /dev/null"]