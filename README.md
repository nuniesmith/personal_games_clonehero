# Clone Hero Dockerized Setup & Content Manager

This repository provides a **fully containerized** environment for running a Clone Hero dedicated server, managing custom content, and synchronizing files across multiple devices. It includes:

- **Clone Hero Standalone Server** (multiplayer server)
- **Clone Hero Content Manager API** (FastAPI backend for content management)
- **Clone Hero Content Manager Frontend** (Streamlit UI)
- **PostgreSQL** (database for storing metadata)
- **Syncthing** (file synchronization)
- **NGINX** (reverse proxy for routing external requests)

The goal is to provide an all-in-one solution for hosting multiplayer sessions, managing songs, backgrounds, highways, and color profiles, and automatically syncing content across devices.

---

## Table of Contents

1. [Overview of Services](#overview-of-services)
2. [Features](#features)
3. [Directory Structure](#directory-structure)
4. [Setup & Installation](#setup--installation)
5. [Accessing Services](#accessing-services)
6. [Managing Content](#managing-content)
7. [API Endpoints](#api-endpoints)
8. [Logging](#logging)
9. [Troubleshooting](#troubleshooting)
10. [Future Improvements](#future-improvements)
11. [License](#license)

---

## Overview of Services

### 1. NGINX Reverse Proxy
- **Purpose**: Routes incoming requests to the appropriate service (Clone Hero server, API, frontend, Syncthing, and backend).
- **Port**: 80 (HTTP) redirected to HTTPS.
- **Configuration**: Located at `nginx/nginx.conf`.

### 2. Clone Hero Standalone Server
- **Purpose**: Dedicated server for Clone Hero multiplayer sessions.
- **Port**: 14242 (Multiplayer connections)
- **Note**: Currently running in sleep mode for maintenance; adjust the command as needed.

### 3. Content Manager API (FastAPI)
- **Purpose**: Handles content uploads, organization, and metadata storage for songs, backgrounds, highways, and color profiles.
- **Database**: Uses PostgreSQL to store content metadata.
- **Port**: 8000 (API access)

### 4. Content Manager Frontend (Streamlit)
- **Purpose**: Provides a web UI for managing Clone Hero content.
- **Port**: 8501 (Streamlit UI)

### 5. Syncthing
- **Purpose**: Automatically synchronizes custom songs and other assets across devices.
- **Ports**:
  - **8384**: Web UI
  - **22000/TCP** and **21027/UDP**: Synchronization traffic

### 6. Backend Service
- **Purpose**: Processes data or background tasks (e.g., file processing, queuing, etc.).
- **Port**: 8001 (exposed internally)
- **Command**: Runs a worker process (`python worker.py`)
- **Health Check**: Ensures the backend is responsive via an HTTP endpoint.

---

## Features

1. **Multiplayer Server**  
   - Run a dedicated server for Clone Hero multiplayer sessions.

2. **Content Management**  
   - **Upload** and **organize** songs, backgrounds, highways, and color profiles.
   - **Metadata Storage** using PostgreSQL.

3. **Frontend UI**  
   - Manage content through a user-friendly Streamlit interface.

4. **File Synchronization**  
   - Use Syncthing to sync your custom content across multiple devices.

5. **Backend Processing**  
   - Handle background tasks or data processing through a dedicated backend service.

6. **NGINX Reverse Proxy**  
   - Route and secure all external requests with SSL and security headers.

7. **Logging & Health Checks**  
   - Built-in logging and health checks ensure service stability and ease of troubleshooting.

---

## Directory Structure

Below is a sample directory structure; adjust as needed for your organization:

```
.
├── docker-compose.yml         # Primary Docker Compose configuration
├── nginx/
│   └── nginx.conf             # NGINX reverse proxy configuration
├── docker/
│   ├── server/                # Docker setup for the Clone Hero Standalone Server
│   ├── api/                   # Docker setup for the FastAPI backend (Content Manager API)
│   ├── frontend/              # Docker setup for the Streamlit frontend
│   ├── backend/               # Docker setup for the backend worker service
│   └── syncthing/             # Docker setup for Syncthing
├── data/
│   ├── clonehero_content/     # Persistent volume for storing songs and assets
│   └── sync_config/           # Configuration for Syncthing
├── src/
│   ├── main.py                # FastAPI entry point
│   ├── worker.py              # Backend worker script
│   ├── app.py                 # Streamlit entry point
│   ├── routes/                # FastAPI routes (upload, content management)
│   ├── pages/                 # Streamlit pages (songs, backgrounds, highways, colors)
│   ├── services/              # Logic for interacting with files and database
│   ├── database.py            # Database connection setup
│   └── utils.py               # Shared utility functions
└── ...
```

---

## Setup & Installation

### 1. Prerequisites

- **Docker Engine** installed on your system.

> **Note**: Refer to the official [Docker documentation](https://docs.docker.com/get-docker/) for installation instructions.

### 2. Clone the Repository

```bash
git clone https://github.com/nuniesmith/clonehero.git
cd clonehero
```

### 3. (Optional) Adjust Environment Variables

- Copy the example environment file and edit as needed:

  ```bash
  cp .env.example .env
  ```

- Update credentials (e.g., PostgreSQL user/password), service ports, etc.

### 4. Build & Run

Run the following command to build and start all services in the background:

```bash
docker compose up -d --build
```

### 5. Verify Services

Check if containers are running:

```bash
docker ps
```

---

## Accessing Services

| **Service**                | **URL / Port**                                 |
|----------------------------|------------------------------------------------|
| **Frontend (Streamlit)**   | [http://localhost:8501](http://localhost:8501) |
| **API (FastAPI)**          | [http://localhost:8000](http://localhost:8000) |
| **Backend Worker**         | Internal: port 8001 (for health checks and processing) |
| **Clone Hero Server**      | Port `14242` (Multiplayer)                     |
| **Syncthing (Web UI)**     | [http://localhost:8384](http://localhost:8384) |

---

## Managing Content

### 1. Frontend (Streamlit)

- **Song Management**: View, upload, and delete songs.
- **Backgrounds & Highways**: Upload and manage custom backgrounds or highways.
- **Color Profiles**: Upload and organize `.ini` color profiles.

Access the Streamlit UI at:

```
http://localhost:8501
```

### 2. Content Folder

- Uploaded songs and assets are stored in the `data/clonehero_content` directory (mounted as a Docker volume) for persistence.

### 3. Syncthing

- Use the Syncthing UI to sync your songs and assets across multiple devices:
  
  ```
  http://localhost:8384
  ```

---

## API Endpoints

Some key FastAPI endpoints include:

- **`POST /upload_content/`**  
  Upload songs, highways, backgrounds, or color profiles.
  
- **`GET /songs/`**  
  List all songs in the system.
  
- **`POST /songs/upload/`**  
  Upload a song file (e.g., `.zip` or `.rar`).
  
- **`POST /songs/download/`**  
  Download and extract a song from a specified URL.

Access the auto-generated API docs (if enabled) at:

```
http://localhost:8000/docs
```

---

## Logging

### Container Logs

To view combined logs for all running services:

```bash
docker compose logs -f
```

### File-Based Logs

Depending on your configuration, logs might also be stored inside containers or mapped volumes. For example:

- `app.log` — FastAPI logs  
- `streamlit_app.log` — Streamlit logs  

Check your Docker volume mounts or service configurations for specific log paths.

---

## Troubleshooting

1. **Check Logs**  
   ```bash
   docker compose logs -f
   ```
   Review logs for errors or issues.

2. **Rebuild from Scratch**  
   ```bash
   docker compose build --no-cache
   ```
   Useful if old cache layers are causing issues.

3. **Restart a Specific Service**  
   ```bash
   docker compose restart <service-name>
   ```
   Example:  
   ```bash
   docker compose restart content
   ```

4. **Remove Unused Docker Assets**  
   ```bash
   docker system prune -a
   ```
   Clears unused images, containers, and other Docker artifacts.

5. **Verify Docker Networks & Volumes**  
   Ensure containers are connected to the `clonehero_network` and that volume mounts are configured correctly.

---

## Future Improvements

1. **HTTPS (SSL/TLS)**  
   - Integrate Let’s Encrypt for secure external access via NGINX.

2. **Authentication & Authorization**  
   - Implement user logins for the API and frontend.

3. **Monitoring & Metrics**  
   - Integrate Prometheus and Grafana for detailed logging and performance metrics.

4. **Scalability**  
   - Consider Docker Swarm or Kubernetes for scaling services as needed.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

**Happy shredding!**  
If you have any questions or suggestions, feel free to [open an issue](https://github.com/nuniesmith/clonehero/issues) or submit a pull request.