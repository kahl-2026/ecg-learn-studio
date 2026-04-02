#!/usr/bin/env bash
set -e

# ECG Learn Studio - Automated Setup Script
# Supports: Arch Linux, Debian/Ubuntu, Fedora/RHEL

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
RUST_BIN_PATH=""

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

detect_rust_binary_path() {
    local candidates=(
        "tui-rust/target/release/ecg-learn-tui"
        "tui-rust/target/release/tui-rust"
    )

    local candidate
    for candidate in "${candidates[@]}"; do
        if [ -f "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done

    if [ -d "tui-rust/target/release" ]; then
        candidate=$(find tui-rust/target/release -maxdepth 1 -type f -perm -111 ! -name "*.d" ! -name "build-script-*" | head -n 1)
        if [ -n "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    fi

    return 1
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif [ -f /etc/arch-release ]; then
        OS="arch"
    else
        error "Unable to detect OS. Supported: Arch, Debian/Ubuntu, Fedora/RHEL"
    fi
    
    info "Detected OS: $OS"
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        warn "Running as root. This script will use sudo when needed."
        SUDO=""
    else
        SUDO="sudo"
    fi
}

# Install system dependencies based on OS
install_system_deps() {
    info "Installing system dependencies..."
    
    case $OS in
        arch|manjaro)
            $SUDO pacman -Syu --noconfirm
            $SUDO pacman -S --needed --noconfirm \
                base-devel \
                git \
                curl \
                wget \
                python \
                python-pip \
                python-virtualenv \
                cmake \
                pkg-config \
                openssl
            ;;
            
        debian|ubuntu|linuxmint|pop)
            $SUDO apt-get update
            $SUDO apt-get install -y \
                build-essential \
                git \
                curl \
                wget \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                cmake \
                pkg-config \
                libssl-dev \
                libffi-dev
            ;;
            
        fedora|rhel|centos|rocky|almalinux)
            $SUDO dnf check-update || true
            # Try dnf5 syntax first, fall back to dnf4
            if dnf --version 2>/dev/null | grep -q "dnf5"; then
                $SUDO dnf install -y @development-tools
            else
                $SUDO dnf groupinstall -y "Development Tools" || $SUDO dnf group install -y "Development Tools"
            fi
            $SUDO dnf install -y \
                git \
                curl \
                wget \
                python3 \
                python3-pip \
                python3-devel \
                cmake \
                pkg-config \
                openssl-devel \
                libffi-devel \
                gcc \
                gcc-c++ \
                make
            ;;
            
        *)
            error "Unsupported OS: $OS. Please install dependencies manually."
            ;;
    esac
    
    info "System dependencies installed successfully"
}

# Install Rust toolchain
install_rust() {
    if command -v rustc &> /dev/null; then
        RUST_VERSION=$(rustc --version | awk '{print $2}')
        info "Rust is already installed (version $RUST_VERSION)"
        read -p "Do you want to update Rust? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rustup update
        fi
    else
        info "Installing Rust toolchain..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
        source "$HOME/.cargo/env"
        info "Rust installed successfully"
    fi
    
    # Ensure cargo is in PATH
    if ! command -v cargo &> /dev/null; then
        export PATH="$HOME/.cargo/bin:$PATH"
        echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    fi
    
    # Verify Rust installation
    rustc --version
    cargo --version
}

# Install Python dependencies
install_python_deps() {
    info "Installing Python dependencies..."
    
    # Get Python version
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 9 ]; then
        warn "Python 3.9+ is recommended. You have Python $PYTHON_VERSION"
    else
        info "Python version: $PYTHON_VERSION"
    fi
    
    # Upgrade packaging tools conservatively.
    # IMPORTANT: torch currently requires setuptools<82 in this project.
    python3 -m pip install --upgrade pip wheel
    
    # Check if dependencies are already installed (by package metadata, not import name)
    if [ -f "ml-python/requirements.txt" ]; then
        info "Checking installed Python packages..."
        MISSING_DEPS=0
        TMP_REQ_CHECK=$(mktemp)
        
        while IFS= read -r line; do
            # Skip empty lines and comments
            [[ -z "$line" || "$line" =~ ^# ]] && continue

            if python3 -c "import importlib.metadata as m; import packaging.requirements as r; req=r.Requirement('$line'); v=m.version(req.name); raise SystemExit(0 if ((not req.specifier) or (v in req.specifier)) else 1)" 2>/dev/null; then
                PKG_NAME=$(echo "$line" | sed 's/[<>=!].*//' | xargs)
                info "  ✓ $PKG_NAME already installed"
            else
                PKG_NAME=$(echo "$line" | sed 's/[<>=!].*//' | xargs)
                info "  ✗ $PKG_NAME missing/incompatible"
                echo "$line" >> "$TMP_REQ_CHECK"
                MISSING_DEPS=1
            fi
        done < ml-python/requirements.txt
        
        if [ $MISSING_DEPS -eq 0 ]; then
            info "All Python dependencies already installed!"
        else
            info "Installing missing Python packages..."
            python3 -m pip install -r "$TMP_REQ_CHECK"
        fi

        rm -f "$TMP_REQ_CHECK"
    else
        error "ml-python/requirements.txt not found!"
    fi
    
    info "Python dependencies installed successfully"
}

# Build Rust TUI
build_rust_tui() {
    info "Building Rust TUI application..."
    
    cd tui-rust
    cargo build --release
    cd ..

    RUST_BIN_PATH=$(detect_rust_binary_path || true)
    info "Rust TUI built successfully"
    if [ -n "$RUST_BIN_PATH" ]; then
        info "Binary location: $RUST_BIN_PATH"
    else
        warn "Could not auto-detect Rust binary in tui-rust/target/release"
    fi
}

# Create convenience symlinks
create_symlinks() {
    info "Creating convenience symlinks..."
    
    # Create bin directory if it doesn't exist
    mkdir -p bin
    
    if [ -z "$RUST_BIN_PATH" ]; then
        RUST_BIN_PATH=$(detect_rust_binary_path || true)
    fi

    # Symlink to Rust binary
    if [ -n "$RUST_BIN_PATH" ] && [ -f "$RUST_BIN_PATH" ]; then
        ln -sf "../$RUST_BIN_PATH" bin/ecg-learn-studio
        info "Created symlink: bin/ecg-learn-studio"
    else
        warn "Skipping symlink: Rust binary not found"
    fi
}

# Setup datasets directory
setup_datasets() {
    info "Setting up datasets directory..."
    
    mkdir -p datasets/{synthetic,mit-bih,ptb-xl}
    
    info "Datasets directory structure created"
    info "Run 'make sample-data' to generate synthetic ECG data"
}

# Print next steps
print_next_steps() {
    echo
    info "=================================="
    info "Setup completed successfully! 🎉"
    info "=================================="
    echo
    echo "Next steps:"
    echo "  1. Generate sample data:"
    echo "     make sample-data"
    echo
    echo "  2. Run the application:"
    echo "     make run"
    echo "     OR"
    echo "     ./bin/ecg-learn-studio"
    echo
    echo "  3. Explore features:"
    echo "     - Press 'H' for Home"
    echo "     - Press 'L' for Lessons"
    echo "     - Press 'E' for Signal Explorer"
    echo "     - Press 'T' for Train Model"
    echo "     - Press '?' for Help"
    echo
    echo "For more information, see README.md"
    echo
}

# Main setup function
main() {
    echo "========================================"
    echo "  ECG Learn Studio - Setup Script"
    echo "========================================"
    echo
    
    # Check prerequisites
    detect_os
    check_root
    
    # Install dependencies
    install_system_deps
    install_rust
    install_python_deps
    
    # Build application
    build_rust_tui
    
    # Setup environment
    create_symlinks
    setup_datasets
    
    # Done
    print_next_steps
}

# Run main function
main
