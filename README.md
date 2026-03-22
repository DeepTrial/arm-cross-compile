# ARM Cross-Compilation Environment Manager

A flexible, configuration-driven tool for managing ARM cross-compilation Docker environments.

## Features

- **Configuration-Driven**: Define environments via YAML configuration files
- **Auto-Generation**: Automatically generate Dockerfiles from configurations
- **Verification**: Built-in verification of generated environments
- **Flexible**: Support custom toolchains, packages, and build steps
- **Extensible**: Easy to add new architectures and configurations

## Quick Start

### 1. List Available Configurations

```bash
./scripts/list-configs.sh
```

### 2. Build from Configuration

```bash
# Build using predefined configuration
./scripts/build-from-config.sh configs/aarch64-toolchain.yaml

# Build with custom tag
./scripts/build-from-config.sh configs/aarch64-toolchain.yaml --tag my-image:v1.0
```

### 3. Run Container

```bash
docker run -it --rm -v $(pwd):/workspace arm-cross:aarch64-toolchain
```

## Directory Structure

```
.
├── configs/                   # Environment configuration files (YAML)
│   ├── aarch64-toolchain.yaml
│   ├── armhf-toolchain.yaml
│   └── custom-example.yaml
├── generator/                 # Dockerfile generator and verifier
│   ├── generate.py           # Generate Dockerfile from config
│   └── verify.py             # Verify Dockerfile and image
├── scripts/                   # Build and utility scripts
│   ├── build-from-config.sh  # Main build script
│   ├── list-configs.sh       # List available configs
│   ├── build.sh              # Legacy script (deprecated)
│   └── run.sh                # Run container
├── templates/                 # Configuration templates
│   └── config-template.yaml  # Template for new configs
├── dockerfiles/               # Generated Dockerfiles
│   └── generated/            # Auto-generated from configs
└── docs/                      # Documentation
```

## Configuration Format

Create a YAML configuration file:

```yaml
name: my-custom-env
base_image: ubuntu:22.04
architecture: aarch64
description: My custom ARM environment

toolchain:
  type: gcc
  prefix: aarch64-linux-gnu
  packages:
    - gcc-aarch64-linux-gnu
    - g++-aarch64-linux-gnu

packages:
  base:
    - build-essential
    - cmake
    - git
  dev:
    - python3
    - gdb-multiarch

env:
  DEBIAN_FRONTEND: noninteractive
  MY_VAR: my_value

custom_steps:
  - echo "Setup complete!"
```

## Commands

### Generate Only

```bash
python3 generator/generate.py configs/aarch64-toolchain.yaml -o output/Dockerfile
```

### Validate Configuration

```bash
./scripts/build-from-config.sh configs/aarch64-toolchain.yaml --validate-only
```

### Build Without Verification

```bash
./scripts/build-from-config.sh configs/aarch64-toolchain.yaml --no-verify
```

### Verify Existing Dockerfile

```bash
python3 generator/verify.py dockerfiles/generated/aarch64-toolchain/Dockerfile \
    --build -t arm-cross:aarch64-toolchain -p aarch64-linux-gnu
```

## Creating Custom Configurations

1. Copy the template:
   ```bash
   cp templates/config-template.yaml configs/my-env.yaml
   ```

2. Edit the configuration file

3. Build:
   ```bash
   ./scripts/build-from-config.sh configs/my-env.yaml
   ```

## Requirements

- Docker
- Python 3.6+
- PyYAML (`pip3 install pyyaml`)

## License

MIT
