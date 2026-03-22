#!/bin/bash
# Build Docker image for specified architecture cross-compilation environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Display help information
show_help() {
    echo "Usage: $0 <architecture> [tag]"
    echo ""
    echo "Supported architectures:"
    echo "  aarch64  - ARM64 / ARMv8-A"
    echo "  armhf    - ARM hard-float (ARMv7+)"
    echo "  armel    - ARM soft-float"
    echo "  armv7    - ARMv7 specific"
    echo ""
    echo "Examples:"
    echo "  $0 aarch64         # Build aarch64 image with latest tag"
    echo "  $0 armhf v1.0      # Build armhf image with v1.0 tag"
}

# Check arguments
if [ $# -lt 1 ]; then
    show_help
    exit 1
fi

ARCH=$1
TAG=${2:-latest}
DOCKERFILE_DIR="$PROJECT_ROOT/dockerfiles/$ARCH"

# Check if architecture directory exists
if [ ! -d "$DOCKERFILE_DIR" ]; then
    echo "Error: Unsupported architecture '$ARCH'"
    echo "Available architectures:"
    for d in "$PROJECT_ROOT"/dockerfiles/*/; do
        echo "  - $(basename "$d")"
    done
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE_DIR/Dockerfile" ]; then
    echo "Error: $DOCKERFILE_DIR/Dockerfile does not exist"
    exit 1
fi

echo "========================================="
echo "Building ARM Cross-Compilation Image"
echo "Architecture: $ARCH"
echo "Tag: $TAG"
echo "========================================="

# Build image
docker build \
    -t "arm-cross:${ARCH}-${TAG}" \
    -t "arm-cross:${ARCH}" \
    -f "$DOCKERFILE_DIR/Dockerfile" \
    "$DOCKERFILE_DIR"

echo ""
echo "✓ Build completed: arm-cross:${ARCH}-${TAG}"
echo ""
echo "Run container:"
echo "  docker run -it --rm -v \$(pwd):/workspace arm-cross:${ARCH}"
