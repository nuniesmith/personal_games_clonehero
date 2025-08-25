#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# CONFIGURATION & GLOBAL VARIABLES
###############################################################################

# Debugging
DEBUG=false  # Set to 'true' for verbose mode
[[ "$DEBUG" == "true" ]] && set -x

# Default non-interactive mode to false
NON_INTERACTIVE=false

# Parse command-line options
while getopts "y" opt; do
  case "$opt" in
    y)
      NON_INTERACTIVE=true
      ;;
    *)
      echo "Usage: $(basename "$0") [-y]"
      exit 1
      ;;
  esac
done
shift "$((OPTIND-1))"

# Logging
readonly LOG_DIR="/tmp/utils"
readonly LOG_FILE="${LOG_DIR}/utils.log"

# Sudo password, fallback from environment if provided
password="${SUDO_PASS:-${password:-}}"

# Docker Hub Settings
DOCKERHUB_USERNAME="nuniesmith"
DOCKERHUB_REPOSITORY="clonehero"
PYTHONPATH="/app"

# Docker Compose
COMPOSE_FILE="docker-compose.yml"

# Docker services (build & push)
declare -A services=(
  ["api"]="./docker/api/Dockerfile"
  ["backend"]="./docker/backend/Dockerfile"
  ["frontend"]="./docker/frontend/Dockerfile"
  ["nginx"]="./docker/nginx/Dockerfile"
  ["postgres"]="./docker/postgres/Dockerfile"
  ["server"]="./docker/server/Dockerfile"
  ["sync"]="./docker/sync/Dockerfile"
)

# Global distro detection
DETECTED_DISTRO=""

###############################################################################
# INITIAL SETUP
###############################################################################

# Create logging directory
mkdir -p "$LOG_DIR"
chmod 700 "$LOG_DIR"

# Trap signals
trap 'log_info "Script interrupted."; exit 130' INT
trap 'log_info "Script terminated."; exit 143' TERM

###############################################################################
# LOGGING FUNCTIONS
###############################################################################
log_info() {
    echo "[INFO]  $(date '+%Y-%m-%d %H:%M:%S') - $*"
    echo "[INFO]  $(date '+%Y-%m-%d %H:%M:%S') - $*" >> "$LOG_FILE"
}
log_warn() {
    echo "[WARN]  $(date '+%Y-%m-%d %H:%M:%S') - $*"
    echo "[WARN]  $(date '+%Y-%m-%d %H:%M:%S') - $*" >> "$LOG_FILE"
}
log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $*" >> "$LOG_FILE"
}

# Simple yes/no prompt
confirm() {
    local prompt="$1"
    if [[ "$NON_INTERACTIVE" == true ]]; then
        # Automatically confirm in non-interactive mode
        echo "$prompt [y/N]: y (auto-confirmed)"
        return 0
    else
        read -r -p "$prompt [y/N]: " response
        [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
    fi
}

###############################################################################
# SUDO PASSWORD HANDLING
###############################################################################
validate_sudo_password() {
    local pass="$1"
    echo "$pass" | sudo -kS true 2>/dev/null
}

handle_sudo_password() {
    # If password is provided, validate it
    if [[ -n "${password:-}" ]]; then
        if ! validate_sudo_password "$password"; then
            log_error "Provided sudo password is invalid. Exiting."
            exit 1
        fi
        log_info "Sudo password validated from environment variable."
    else
        # Non-interactive mode without a password → fail fast
        if [[ "$NON_INTERACTIVE" == true ]]; then
            log_error "Sudo password not provided in non-interactive mode. Exiting."
            exit 1
        fi
        
        # Otherwise, prompt for password interactively
        while true; do
            read -s -p "Sudo Password: " password
            echo
            if validate_sudo_password "$password"; then
                log_info "Sudo password validated."
                break
            else
                log_error "Invalid sudo password. Please try again."
            fi
        done
    fi
}

###############################################################################
# LINUX DISTRIBUTION DETECTION
###############################################################################
detect_linux_distribution() {
    log_info "Detecting Linux distribution..."
    if [[ -f /etc/os-release ]]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        DETECTED_DISTRO=$(echo "$ID" | tr '[:upper:]' '[:lower:]')
    else
        log_warn "Could not detect Linux distribution. Defaulting to fedora."
        DETECTED_DISTRO="fedora"
    fi
    log_info "Detected distribution: $DETECTED_DISTRO"
}

###############################################################################
# SYSTEM TOOLS
###############################################################################
install_docker_engine() {
    log_info "Installing Docker Engine..."
    case "$DETECTED_DISTRO" in
        fedora)
            echo "$password" | sudo -S dnf -y install dnf-plugins-core
            cat << 'EOF' | sudo tee /etc/yum.repos.d/docker-ce.repo > /dev/null
[docker-ce-stable]
name=Docker CE Stable - $releasever
baseurl=https://download.docker.com/linux/fedora/$releasever/$basearch/stable
enabled=1
gpgcheck=1
gpgkey=https://download.docker.com/linux/fedora/gpg
EOF
            echo "$password" | sudo -S dnf -y install docker-ce docker-ce-cli docker-buildx-plugin docker-compose-plugin
            echo "$password" | sudo -S systemctl enable docker
            echo "$password" | sudo -S systemctl start docker
            log_info "Docker installed successfully on Fedora."
            ;;
        *)
            log_error "Docker installation not implemented for $DETECTED_DISTRO."
            ;;
    esac
}

update_system_packages() {
    log_info "Updating system packages for $DETECTED_DISTRO..."
    case "$DETECTED_DISTRO" in
        ubuntu|debian)
            echo "$password" | sudo -S apt update && echo "$password" | sudo -S apt upgrade -y
            ;;
        fedora|rhel|centos)
            echo "$password" | sudo -S dnf -y upgrade
            ;;
        arch)
            echo "$password" | sudo -S pacman -Syu --noconfirm
            ;;
        *)
            log_warn "System update not implemented for $DETECTED_DISTRO."
            ;;
    esac
    log_info "System packages updated."
}

check_for_updates() {
    log_info "Checking for system updates..."
    case "$DETECTED_DISTRO" in
        fedora)
            if echo "$password" | sudo -S dnf check-update --refresh &>/dev/null; then
                set +e
                echo "$password" | sudo -S dnf check-update --refresh
                RETVAL=$?
                set -e
                if [[ $RETVAL -eq 100 ]]; then
                    log_info "Updates available."
                    if confirm "Apply system updates now?"; then
                        update_system_packages
                    else
                        log_info "Skipping system updates."
                    fi
                else
                    log_info "No updates available."
                fi
            else
                log_warn "Update check failed or no updates found."
            fi
            ;;
        *)
            log_warn "Update checking not implemented for $DETECTED_DISTRO."
            ;;
    esac
}

ensure_dependencies() {
    # This is a simplistic approach, just checking for 'docker'.
    local dependencies=("docker")
    local install_funcs=(install_docker_engine)
    for i in "${!dependencies[@]}"; do
        local dep="${dependencies[$i]}"
        if ! command -v "$dep" &>/dev/null; then
            log_warn "$dep is not installed."
            if confirm "Install $dep?"; then
                "${install_funcs[$i]}"
            else
                log_info "Skipping $dep installation."
            fi
        else
            log_info "$dep is already installed."
        fi
    done
}

###############################################################################
# DOCKER PRUNE / CACHE CLEARS
###############################################################################
docker_tools_mode() {
    local choice="$1"
    case "$choice" in
        0)
            log_info "Clearing Docker caches and resources..."
            echo "$password" | sudo -S docker system prune -af --volumes
            ;;
        1)
            log_info "Pruning unused Docker volumes..."
            echo "$password" | sudo -S docker volume prune -f
            ;;
        2)
            log_info "Pruning unused Docker images..."
            echo "$password" | sudo -S docker image prune -af
            ;;
        3)
            log_info "Pruning unused Docker containers..."
            echo "$password" | sudo -S docker container prune -f
            ;;
        *)
            log_error "Invalid Docker tool option."
            ;;
    esac
}

###############################################################################
# PERMISSIONS FIX FUNCTION
###############################################################################
fix_dir_permissions() {
    log_info "Applying chmod 755 to current directory ($(pwd)) recursively (verbose)..."
    echo "$password" | sudo -S chmod 755 -Rfv .

    log_info "Applying chown $USER:$USER to current directory recursively (verbose)..."
    echo "$password" | sudo -S chown "$USER":"$USER" -Rfv .
}

###############################################################################
# BUILD & PUSH DOCKER IMAGES
###############################################################################
build_and_push_images() {
  log_info "Building and pushing Docker images..."

  for service in "${!services[@]}"; do
    local dockerfile=${services[$service]}
    local service_sanitized
    service_sanitized="$(echo "$service" | tr ' ' '_')"  # <-- Fixed here

    log_info "----------------------------------------"
    log_info "Building image for service: $service"
    log_info "Using Dockerfile: $dockerfile"

    if ! docker build \
      --build-arg PYTHONPATH="$PYTHONPATH" \
      -t "$DOCKERHUB_USERNAME/$DOCKERHUB_REPOSITORY:$service_sanitized" \
      -f "$dockerfile" .; then
      log_error "Failed to build $service image. Skipping push."
      continue
    fi

    log_info "Successfully built $service image."
    if docker push "$DOCKERHUB_USERNAME/$DOCKERHUB_REPOSITORY:$service_sanitized"; then
      log_info "Successfully pushed $service image to Docker Hub."
    else
      log_error "Failed to push $service image to Docker Hub."
    fi
    log_info "----------------------------------------"
  done
}

###############################################################################
# DOCKER COMPOSE FUNCTIONS
###############################################################################
update_images() {
  log_info "Checking for new images via docker compose pull..."
  local updates_available=false

  if docker compose -f "$COMPOSE_FILE" pull; then
    updates_available=true
    log_info "Successfully pulled the latest images."
  else
    log_warn "Pulling images failed. Attempting to build images locally."
    if docker compose -f "$COMPOSE_FILE" build; then
      updates_available=true
      log_info "Successfully built all images locally."
    else
      log_error "Failed to pull or build images."
      exit 1
    fi
  fi
  echo "$updates_available"
}

start_services() {
  log_info "Stopping any running containers and starting services..."
  docker compose -f "$COMPOSE_FILE" down --remove-orphans
  docker compose -f "$COMPOSE_FILE" up -d --build
  log_info "All services are up and running."
}

docker_compose_start() {
  log_info "Starting the update and launch process for Docker services..."

  if [[ ! -f "$COMPOSE_FILE" ]]; then
    log_error "Docker Compose file '$COMPOSE_FILE' not found."
    exit 1
  fi

  local updates_available
  updates_available=$(update_images)
  if [[ "$updates_available" == "true" ]]; then
    log_info "New images detected. Rebuilding and restarting services."
    start_services
  else
    log_info "No updates found. Restarting services normally."
    start_services
  fi
  log_info "Docker services are running."
}

# NEW FUNCTION: Stop Docker Compose Services
docker_compose_down() {
  log_info "Stopping and removing Docker Compose services..."
  docker compose -f "$COMPOSE_FILE" down --remove-orphans
  log_info "Docker Compose services stopped and removed."
}

###############################################################################
# MAIN MENU
###############################################################################
display_main_menu() {
    echo "========================="
    echo "        Main Menu        "
    echo "========================="
    echo "[0] Start Docker Compose Services"
    echo "[1] Stop Docker Compose Services"
    echo "-------------------------"
    echo "[2] Build & Push Docker Images"
    echo "-------------------------"
    echo "[3] Update System Packages"
    echo "-------------------------"
    echo "[4] Fix Directory Permissions"
    echo "-------------------------"
    echo "[5] Install Docker Engine"
    echo "[6] Clear Docker Caches"
    echo "[7] Prune Docker Volumes"
    echo "[8] Prune Docker Images"
    echo "[9] Prune Docker Containers"
    echo "-------------------------"
    echo "[q] Quit"
    echo "========================="
}

main() {
    # Prompt for sudo password
    handle_sudo_password
    detect_linux_distribution
    ensure_dependencies
    check_for_updates

    while true; do
        display_main_menu
        if [[ "$NON_INTERACTIVE" == true ]]; then
            # In non-interactive mode, you might automatically pick an option or exit.
            # Adjust this behavior as needed. For now, we'll just exit.
            log_info "Non-interactive mode: skipping menu. Exiting."
            exit 0
        fi
    

        read -p "Select an option [0-9/q]: " choice
        case "$choice" in
            0) docker_compose_start ;;
            1) docker_compose_down ;;
            2) build_and_push_images ;;
            3) update_system_packages ;;
            4) fix_dir_permissions ;;
            5) install_docker_engine ;;
            6) docker_tools_mode 0 ;;
            7) docker_tools_mode 1 ;;
            8) docker_tools_mode 2 ;;
            9) docker_tools_mode 3 ;;
            q)
                log_info "Exiting script."
                exit 0
                ;;
            *)
                log_error "Invalid choice. Please select 0-9 or 'q' to quit."
                ;;
        esac
    done
}

# Start the script
main "$@"