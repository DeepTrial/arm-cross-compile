#!/bin/bash
# ARM Cross-Compilation Environment Builder
# Usage: 
#   ./build.sh <config.yaml> [image-tag]     # Build image
#   ./build.sh export <image:tag> [dir]      # Export image to tar.gz
#   ./build.sh images [--arch arm64]         # List prebuilt images
#   ./build.sh install <name>                # Install prebuilt image
#   ./build.sh publish <image:tag> [options] # Publish to prebuilt repo
#
# Examples:
#   ./build.sh configs/default.yaml
#   ./build.sh configs/default.yaml my-image:v1.0
#   ./build.sh export debian13-arm64:latest
#   ./build.sh export debian13-arm64:latest ./my-exports
#   ./build.sh images
#   ./build.sh install debian13-a720ae
#   ./build.sh publish debian13-a720ae:latest --name debian13-a720ae

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CMD="${1:-}"

show_help() {
    echo "ARM Cross-Compilation Environment Builder"
    echo ""
    echo "Usage:"
    echo "  $0 <config.yaml> [image-tag]        Build from config"
    echo "  $0 export <image:tag> [directory]   Export image to tar.gz"
    echo "  $0 import <file.tar.gz>             Import image from file"
    echo "  $0 images [--arch arm64/armhf]      List prebuilt images"
    echo "  $0 install <name>                   Install prebuilt image"
    echo "  $0 publish <image:tag> [options]    Publish to prebuilt repo"
    echo ""
    echo "Configs:"
    ls -1 "${SCRIPT_DIR}/configs/"*.yaml 2>/dev/null | xargs -n1 basename | sed 's/^/  - /' || echo "  (none)"
    echo ""
    echo "Examples:"
    echo "  $0 configs/default.yaml"
    echo "  $0 configs/default.yaml my-image:latest"
    echo "  $0 export debian13-arm64:latest"
    echo "  $0 import ./exports/debian13-arm64-latest.tar.gz"
    echo "  $0 images"
    echo "  $0 install debian13-a720ae"
    echo "  $0 publish debian13-a720ae:latest --name debian13-a720ae --gcc 14.2"
}

# No arguments
if [ -z "$CMD" ] || [ "$CMD" = "-h" ] || [ "$CMD" = "--help" ]; then
    show_help
    exit 0
fi

# Handle export command
if [ "$CMD" = "export" ]; then
    IMAGE="${2:-}"
    OUTDIR="${3:-./exports}"
    
    if [ -z "$IMAGE" ]; then
        echo "Usage: $0 export <image:tag> [directory]"
        echo ""
        echo "Examples:"
        echo "  $0 export debian13-arm64:latest"
        echo "  $0 export debian13-arm64:latest ./exports"
        exit 1
    fi
    
    python3 "${SCRIPT_DIR}/cross-toolchain.py" export "$IMAGE" -o "$OUTDIR"
    exit $?
fi

# Handle import command
if [ "$CMD" = "import" ]; then
    FILE="${2:-}"
    
    if [ -z "$FILE" ]; then
        echo "Usage: $0 import <file.tar.gz>"
        echo ""
        echo "Example:"
        echo "  $0 import ./exports/debian13-arm64-latest.tar.gz"
        exit 1
    fi
    
    if [ ! -f "$FILE" ]; then
        echo "Error: File not found: $FILE"
        exit 1
    fi
    
    python3 "${SCRIPT_DIR}/cross-toolchain.py" import "$FILE"
    exit $?
fi

# Handle images command
if [ "$CMD" = "images" ]; then
    shift
    python3 "${SCRIPT_DIR}/cross-toolchain.py" images "$@"
    exit $?
fi

# Handle install command
if [ "$CMD" = "install" ]; then
    NAME="${2:-}"
    
    if [ -z "$NAME" ]; then
        echo "Usage: $0 install <name>"
        echo ""
        echo "Examples:"
        echo "  $0 install debian13-a720ae"
        echo "  $0 install debian13-arm64"
        echo ""
        echo "Available images:"
        python3 "${SCRIPT_DIR}/cross-toolchain.py" images
        exit 1
    fi
    
    python3 "${SCRIPT_DIR}/cross-toolchain.py" install "$NAME"
    exit $?
fi

# Handle publish command
if [ "$CMD" = "publish" ]; then
    shift
    python3 "${SCRIPT_DIR}/cross-toolchain.py" publish "$@"
    exit $?
fi

# Default: build from config
CONFIG="$CMD"
TAG="${2:-}"

if [ ! -f "$CONFIG" ]; then
    echo "Error: Config not found: $CONFIG"
    exit 1
fi

# Install PyYAML if needed
if ! python3 -c "import yaml" 2>/dev/null; then
    pip3 install pyyaml -q 2>/dev/null || pip3 install pyyaml --user -q
fi

# Build with auto-mirror
python3 "${SCRIPT_DIR}/cross-toolchain.py" build "$CONFIG" ${TAG:+-t "$TAG"} --auto-mirror
