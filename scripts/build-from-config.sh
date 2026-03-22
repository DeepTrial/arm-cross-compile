#!/bin/bash
# Build ARM cross-compilation environment from configuration file
# Usage: ./scripts/build-from-config.sh <config-file> [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
GENERATOR="$PROJECT_ROOT/generator/generate.py"
VERIFIER="$PROJECT_ROOT/generator/verify.py"

show_help() {
    echo "Build ARM cross-compilation environment from configuration"
    echo ""
    echo "Usage: $0 <config-file> [options]"
    echo ""
    echo "Arguments:"
    echo "  config-file    Path to YAML configuration file"
    echo ""
    echo "Options:"
    echo "  -t, --tag TAG      Image tag (default: auto-generated from config name)"
    echo "  -o, --output PATH  Output Dockerfile path (default: auto-generated)"
    echo "  --no-verify        Skip verification after build"
    echo "  --validate-only    Only validate config, do not build"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 configs/aarch64-toolchain.yaml"
    echo "  $0 configs/custom-env.yaml --tag my-image:v1.0"
    echo "  $0 configs/aarch64-toolchain.yaml --validate-only"
}

# Parse arguments
CONFIG_FILE=""
TAG=""
OUTPUT=""
NO_VERIFY=false
VALIDATE_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        --no-verify)
            NO_VERIFY=true
            shift
            ;;
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        -*)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            if [ -z "$CONFIG_FILE" ]; then
                CONFIG_FILE="$1"
            else
                echo "Unexpected argument: $1"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate config file
if [ -z "$CONFIG_FILE" ]; then
    echo "Error: Configuration file is required"
    show_help
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

CONFIG_FILE="$(cd "$(dirname "$CONFIG_FILE")" && pwd)/$(basename "$CONFIG_FILE")"

# Extract config name for default tag
CONFIG_NAME=$(basename "$CONFIG_FILE" .yaml)

# Set defaults
if [ -z "$TAG" ]; then
    TAG="arm-cross:${CONFIG_NAME}"
fi

if [ -z "$OUTPUT" ]; then
    OUTPUT="$PROJECT_ROOT/dockerfiles/generated/${CONFIG_NAME}/Dockerfile"
fi

echo "========================================="
echo "ARM Cross-Compilation Environment Builder"
echo "========================================="
echo "Config:    $CONFIG_FILE"
echo "Tag:       $TAG"
echo "Output:    $OUTPUT"
echo ""

# Check Python dependencies
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "Installing required Python package: PyYAML"
    pip3 install pyyaml
fi

# Step 1: Validate and generate
if [ "$VALIDATE_ONLY" = true ]; then
    echo "Validating configuration..."
    python3 "$GENERATOR" "$CONFIG_FILE" --validate-only
    exit $?
fi

echo "Step 1: Generating Dockerfile..."
python3 "$GENERATOR" "$CONFIG_FILE" -o "$OUTPUT"

if [ $? -ne 0 ]; then
    echo "Error: Failed to generate Dockerfile"
    exit 1
fi

echo ""
echo "Step 2: Building image..."
docker build -t "$TAG" -f "$OUTPUT" "$(dirname "$OUTPUT")"

if [ $? -ne 0 ]; then
    echo "Error: Failed to build image"
    exit 1
fi

echo ""
echo "Build successful: $TAG"

# Step 3: Verification
if [ "$NO_VERIFY" = false ]; then
    echo ""
    echo "Step 3: Verifying environment..."
    
    # Extract prefix from config if available
    PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE')).get('toolchain', {}).get('prefix', ''))")
    
    if [ -n "$PREFIX" ]; then
        python3 "$VERIFIER" "$OUTPUT" --build -t "$TAG" -p "$PREFIX"
    else
        echo "Warning: No toolchain prefix found in config, skipping toolchain verification"
        python3 "$VERIFIER" "$OUTPUT" --build -t "$TAG"
    fi
fi

echo ""
echo "========================================="
echo "All done! Image: $TAG"
echo "========================================="
echo ""
echo "To run the container:"
echo "  docker run -it --rm -v \$(pwd):/workspace $TAG"
