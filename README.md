# ARM Cross-Compilation Environment

[![Build and Test](https://github.com/DeepTrial/ARM-Cross-Compile/actions/workflows/build.yml/badge.svg)](https://github.com/DeepTrial/ARM-Cross-Compile/actions/workflows/build.yml)
[![Validate Configs](https://github.com/DeepTrial/ARM-Cross-Compile/actions/workflows/validate.yml/badge.svg)](https://github.com/DeepTrial/ARM-Cross-Compile/actions/workflows/validate.yml)

Simple tool for building ARM cross-compilation Docker environments with automatic mirror selection.

## Features

- **Version-Based Configuration**: Specify GCC, glibc, binutils, gdb versions in YAML
- **Automatic Mirror Selection**: Detects and uses fastest mirrors (DaoCloud, Aliyun, Tsinghua)
- **Fast Build**: Uses apt packages by default (2-5 minutes)
- **CPU Optimization**: Optional Cortex-A720AE and other CPU-specific optimizations

## Quick Start

```bash
# Build default environment (GCC 14.2, glibc 2.41, binutils 2.44, gdb 16.3)
./build.sh configs/default.yaml

# Build with custom tag
./build.sh configs/default.yaml my-cross-env:latest

# Use the environment
docker run -it --rm -v $(pwd):/workspace my-cross-env:latest
aarch64-linux-gnu-gcc --version  # GCC 14.2.0
```

## Configuration

Create a YAML config file:

```yaml
name: my-env
base_image: debian:trixie-slim
architecture: arm64
description: My ARM64 cross-compile environment

# Version specification
versions:
  gcc: "14.2"
  glibc: "2.41"
  binutils: "2.44"
  gdb: "16.3"
  from_source: false  # Use apt (fast) or build from source (slow)

# CPU optimization (optional)
cpu: cortex-a720  # Options: cortex-a53, cortex-a72, cortex-a76, cortex-a720, etc.

# Additional packages
packages:
  base: [build-essential, make, cmake, git]
  qemu: [qemu-user-static]

env:
  DEBIAN_FRONTEND: noninteractive
```

## Available Configs

| Config | Description | Build Time |
|--------|-------------|------------|
| `configs/default.yaml` | GCC 14.2, optimized for Cortex-A720AE | ~3 minutes |
| `configs/from-source.yaml` | Build toolchain from source | ~60 minutes |

## Project Structure

```
.
├── build.sh                 # Main entry script
├── cross-toolchain.py       # Unified tool: generate, build, export, import
├── configs/                 # Configuration files
│   ├── default.yaml         # Default configuration
│   └── from-source.yaml     # Source build example
├── images/                  # Prebuilt images repository
│   ├── manifest.yaml        # Image registry
│   ├── arm64/              # ARM64 images
│   └── armhf/              # ARMHF images
├── templates/               # Configuration templates
│   └── config-template.yaml
├── exports/                 # Temporary exports (created on demand)
└── README.md
```

## Usage Examples

### Compile for ARM64

```bash
# Start container
docker run -it --rm -v $(pwd):/workspace debian13-arm64:latest

# Compile C code
aarch64-linux-gnu-gcc -o hello hello.c

# Compile with CPU optimization (Cortex-A720AE)
aarch64-linux-gnu-gcc ${CFLAGS} -o hello hello.c

# Check binary
file hello
# Output: ELF 64-bit LSB executable, ARM aarch64, ...
```

### Custom Versions

Edit `configs/default.yaml`:

```yaml
versions:
  gcc: "13.2"      # Change GCC version
  cpu: cortex-a76  # Change target CPU
```

Then rebuild:
```bash
./build.sh configs/default.yaml
```

## Export/Import Images

Export image for offline transfer to other machines:

```bash
# Export to ./exports/ directory (default)
./build.sh export debian13-arm64:latest

# Export to custom directory
./build.sh export debian13-arm64:latest /path/to/exports

# Or use Python tool directly
./cross-toolchain.py export debian13-arm64:latest -o ./exports
```

Import on another machine:

```bash
# Using build.sh wrapper
./build.sh import ./exports/debian13-arm64-latest.tar.gz

# Or using Python tool directly
./cross-toolchain.py import ./exports/debian13-arm64-latest.tar.gz

# Or using docker directly
docker load -i debian13-arm64-latest.tar.gz
```

Transfer to remote machine:

```bash
# 1. Export locally
./build.sh export debian13-arm64:latest

# 2. Copy to remote
scp ./exports/debian13-arm64-latest.tar.gz user@remote:/path/

# 3. Import on remote
ssh user@remote 'cd /path && ./build.sh import debian13-arm64-latest.tar.gz'
```

## Prebuilt Images Repository

Manage and share prebuilt images using the `images/` directory:

### List Available Images

```bash
./build.sh images
# or filter by architecture
./build.sh images --arch arm64
```

Output:
```
================================================================================
Name                 Arch     Size       CPU             Description
================================================================================
debian13-a720ae      arm64    ~389MB     cortex-a720     Debian 13.2 + GCC 14...
debian13-arm64       arm64    ~400MB     generic         Debian 13.2 + GCC 14...
================================================================================
```

### Install Prebuilt Image

```bash
# Quick install from repository
./build.sh install debian13-a720ae

# Or using Python directly
./cross-toolchain.py install debian13-a720ae
```

### Publish Image to Repository

After building a custom image, add it to the prebuilt repository:

```bash
# Publish with metadata
./build.sh publish debian13-a720ae:latest \
    --name debian13-a720ae \
    --arch arm64 \
    --cpu cortex-a720 \
    --gcc "14.2" \
    --glibc "2.41" \
    --description "Debian 13.2 + GCC 14.2 + Cortex-A720AE"

# Or using Python directly
./cross-toolchain.py publish debian13-a720ae:latest \
    --name debian13-a720ae \
    --arch arm64 \
    --gcc "14.2"
```

The image will be:
1. Exported from Docker
2. Compressed and stored in `images/arm64/`
3. Registered in `images/manifest.yaml` with checksum

### Share Repository

The `images/` folder can be:
- Shared via git (with git-lfs for large files)
- Uploaded to a file server (update `base_url` in `manifest.yaml`)
- Distributed via USB drive

```bash
# Archive the entire repository
tar czvf arm-images.tar.gz images/

# Extract on another machine
tar xzvf arm-images.tar.gz
./build.sh images
```

## Mirror Selection

The tool automatically detects and uses the best available mirrors:

- **Docker Hub**: docker.m.daocloud.io, docker.1panel.live
- **APT**: mirrors.aliyun.com, mirrors.tuna.tsinghua.edu.cn

To disable auto-mirror and use defaults:
```bash
./cross-toolchain.py build config.yaml --auto-mirror
```

## Requirements

- Docker
- Python 3 + PyYAML
- Internet connection

## License

MIT
