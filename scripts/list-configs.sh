#!/bin/bash
# List available configuration files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/configs"

echo "Available Configuration Files"
echo "=============================="
echo ""

if [ ! -d "$CONFIG_DIR" ]; then
    echo "No configs directory found"
    exit 1
fi

for config in "$CONFIG_DIR"/*.yaml; do
    if [ -f "$config" ]; then
        name=$(basename "$config" .yaml)
        # Try to extract description from YAML
        description=$(grep "^description:" "$config" 2>/dev/null | cut -d':' -f2- | sed 's/^[[:space:]]*//')
        arch=$(grep "^architecture:" "$config" 2>/dev/null | cut -d':' -f2- | sed 's/^[[:space:]]*//')
        
        printf "  %-25s" "$name"
        if [ -n "$arch" ]; then
            printf " [%s]" "$arch"
        fi
        if [ -n "$description" ]; then
            printf " - %s" "$description"
        fi
        echo ""
    fi
done

echo ""
echo "Usage: ./scripts/build-from-config.sh configs/<config-name>.yaml"
