# Prebuilt ARM Cross-Compilation Images

This directory contains prebuilt Docker images for ARM cross-compilation environments.

## Quick Start

### List Available Images

```bash
../build.sh images
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

### Install a Prebuilt Image

```bash
# Install debian13-a720ae
../build.sh install debian13-a720ae

# Verify installation
docker run --rm debian13-a720ae:latest aarch64-linux-gnu-gcc --version
```

## Available Images

### debian13-a720ae
- **Base**: Debian 13.2 (trixie-slim)
- **GCC**: 14.2
- **glibc**: 2.41
- **binutils**: 2.44
- **gdb**: 16.3
- **CPU**: Cortex-A720AE optimized
- **Size**: ~389MB

**Usage:**
```bash
docker run -it --rm -v $(pwd):/workspace debian13-a720ae:latest
aarch64-linux-gnu-gcc ${CFLAGS} -o app app.c
```

### debian13-arm64 (placeholder)
- **Base**: Debian 13.2
- **GCC**: 14.2
- **CPU**: Generic ARM64
- **Size**: ~400MB

### ubuntu2204-arm64 (placeholder)
- **Base**: Ubuntu 22.04
- **GCC**: 11.4
- **CPU**: Generic ARM64
- **Size**: ~450MB

## Directory Structure

```
images/
├── README.md              # This file
├── manifest.yaml          # Image registry with metadata
├── arm64/                # ARM64 architecture images
│   └── debian13-a720ae-latest.tar.gz
└── armhf/                # ARMHF architecture images (empty)
```

## Using Images Without the Build Script

If you don't have the build script available, you can use Docker directly:

```bash
# Load the image
docker load -i arm64/debian13-a720ae-latest.tar.gz

# Verify
docker images | grep debian13-a720ae

# Use the image
docker run -it --rm -v $(pwd):/workspace debian13-a720ae:latest
```

## Adding Your Own Images

### Method 1: Using the Publish Command (Recommended)

```bash
# Build your custom image
../build.sh ../configs/my-custom.yaml my-image:latest

# Publish to this repository
../build.sh publish my-image:latest \
    --name my-custom-image \
    --arch arm64 \
    --cpu cortex-a76 \
    --gcc "13.2" \
    --description "My custom ARM64 build environment"
```

### Method 2: Manual Steps

1. Export your Docker image:
```bash
docker save my-image:latest | pigz > arm64/my-custom-image-latest.tar.gz
```

2. Calculate SHA256 checksum:
```bash
sha256sum arm64/my-custom-image-latest.tar.gz
```

3. Edit `manifest.yaml` and add your image:
```yaml
images:
  my-custom-image:
    name: my-custom-image
    tag: latest
    arch: arm64
    description: My custom build environment
    size: ~400MB
    versions:
      gcc: "13.2"
    cpu: cortex-a76
    file: arm64/my-custom-image-latest.tar.gz
    checksum: sha256:YOUR_CHECKSUM_HERE
    created: '2024-03-22'
```

## Sharing This Repository

### Via Git (with Git LFS)

Since these images are large binary files, use Git LFS:

```bash
# Install git-lfs
git lfs install

# Track image files
git lfs track "images/**/*.tar.gz"

# Add and commit
git add images/
git commit -m "Add ARM cross-compilation images"
git push
```

### Via Archive

```bash
# Create archive (exclude this README from git tracking)
tar czvf arm-cross-images.tar.gz --exclude='.git' images/

# Extract on target machine
tar xzvf arm-cross-images.tar.gz
cd images && ../build.sh install debian13-a720ae
```

### Via Network Share

1. Mount or copy this directory to a network share
2. Users can install directly from the share:
```bash
/mnt/shared/images/build.sh install debian13-a720ae
```

## Manifest Format

The `manifest.yaml` file tracks all available images:

```yaml
repository:
  name: arm-cross-compiler
  description: ARM Cross-Compilation Docker Images
  base_url: https://your-repo.example.com/images  # For future HTTP download

images:
  <image-key>:
    name: <name>
    tag: <tag>
    arch: arm64|armhf
    description: <description>
    size: <size>
    versions:
      gcc: <version>
      glibc: <version>
      binutils: <version>
      gdb: <version>
    cpu: <cpu-optimization>
    file: <relative-path-to-tar.gz>
    checksum: sha256:<hash>
    created: 'YYYY-MM-DD'
```

## Troubleshooting

### Image file not found
```bash
# Check if file exists
ls -la arm64/debian13-a720ae-latest.tar.gz

# If missing, download or rebuild
../build.sh ../configs/default.yaml debian13-a720ae
../build.sh publish debian13-a720ae:latest --name debian13-a720ae
```

### Checksum mismatch
The image file may be corrupted. Re-download or rebuild the image.

### Docker load fails
```bash
# Check file integrity
gunzip -t arm64/debian13-a720ae-latest.tar.gz

# Try decompression first
gunzip -c arm64/debian13-a720ae-latest.tar.gz > /tmp/image.tar
docker load -i /tmp/image.tar
```

## License

Same as the main project (MIT).
