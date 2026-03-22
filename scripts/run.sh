#!/bin/bash
# Run cross-compilation container for specified architecture

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

show_help() {
    echo "Usage: $0 <architecture> [workspace]"
    echo ""
    echo "Parameters:"
    echo "  architecture  - aarch64, armhf, armel, armv7"
    echo "  workspace     - Directory to mount in container (default: current directory)"
    echo ""
    echo "Examples:"
    echo "  $0 aarch64           # Run aarch64 container with current directory mounted"
    echo "  $0 armhf /my/project # Run armhf container with /my/project mounted"
}

if [ $# -lt 1 ]; then
    show_help
    exit 1
fi

ARCH=$1
WORKSPACE=${2:-$(pwd)}
WORKSPACE=$(cd "$WORKSPACE" && pwd)

IMAGE_TAG="arm-cross:${ARCH}"

# Check if image exists
if ! docker image inspect "$IMAGE_TAG" &> /dev/null; then
    echo "Error: Image $IMAGE_TAG does not exist"
    echo "Please run first: ./scripts/build.sh $ARCH"
    exit 1
fi

echo "Starting container: $IMAGE_TAG"
echo "Workspace: $WORKSPACE"
echo ""

# Run container
docker run -it --rm \
    -v "$WORKSPACE:/workspace" \
    -w /workspace \
    --name "arm-cross-${ARCH}-$(date +%s)" \
    "$IMAGE_TAG"
