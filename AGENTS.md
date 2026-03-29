# ARM Cross-Compilation Environment Repository

## Overview

Simple ARM cross-compilation Docker environment builder with automatic mirror selection.

## Architecture

```
configs/*.yaml ──▶ cross-toolchain.py ──▶ Dockerfile ──▶ docker build ──▶ Image
                     (generator + verifier)
```

## Directory Structure

```
.
├── build.sh                 # Main entry point (wrapper script)
├── cross-toolchain.py       # Unified generator + verifier tool
├── configs/                 # Environment configurations
│   ├── default.yaml         # Recommended apt-based config
│   └── from-source.yaml     # Advanced source-build example
├── templates/               # Templates
│   └── config-template.yaml # Configuration template
├── docs/                    # Documentation
└── AGENTS.md                # This file
```

## Key Files

### cross-toolchain.py
Unified tool with three subcommands:
- `generate`: Create Dockerfile from YAML config
- `verify`: Validate Dockerfile and test cross-compilation
- `build`: Full pipeline (generate + build + verify)

Features:
- Automatic mirror selection (Docker, APT, GNU)
- Version specification via YAML
- CPU optimization support (Cortex-A720AE, etc.)

### Configurations

**configs/default.yaml** (Recommended):
- Uses apt packages for fast builds (~3 minutes)
- GCC 14.2, glibc 2.41, binutils 2.44, gdb 16.3
- Cortex-A720AE optimization

**configs/from-source.yaml** (Advanced):
- Builds toolchain from source (~60 minutes)
- Not recommended due to complexity
- Provided as reference only

## Workflow

### Build Workflow

```
configs/*.yaml ──▶ cross-toolchain.py ──▶ docker build ──▶ Image
                      (with mirrors)
```

1. User runs: `./build.sh configs/default.yaml`
2. `cross-toolchain.py` selects fastest mirrors
3. Generates Dockerfile with version replacements
4. Builds Docker image
5. Verifies cross-compilation works

### Export Workflow (Offline Transfer)

```
Build Phase                     Transfer Phase                    Import Phase
───────────                     ─────────────                     ────────────
./build.sh                      scp/rsync/zipdrive               ./build.sh
configs/default.yaml    ──▶    debian13-arm64.tar.gz    ──▶    import
                              (500-800MB)                       Target machine
```

### Prebuilt Repository Workflow

```
Docker Image ──▶ ./build.sh publish ──▶ images/arm64/*.tar.gz
                                         images/manifest.yaml
                                                    │
              ┌─────────────────────────────────────┘
              ▼
        ./build.sh images    (list)
        ./build.sh install   (install)
```

## Configuration Format

See `templates/config-template.yaml` for full specification.

Key fields:
- `name`: Environment identifier
- `base_image`: Docker base image
- `versions`: Tool versions (gcc, glibc, binutils, gdb)
- `cpu`: CPU optimization target
- `packages`: Categorized apt packages
- `env`: Environment variables
- `custom_steps`: Additional RUN commands

## Prebuilt Images Repository

The `images/` directory provides a managed repository for prebuilt cross-compilation environments.

### Repository Structure

```
images/
├── manifest.yaml          # Central registry
├── arm64/                # ARM64 images
│   └── debian13-a720ae-latest.tar.gz
└── armhf/                # ARMHF images
```

### Manifest Format

```yaml
images:
  debian13-a720ae:
    name: debian13-a720ae
    arch: arm64
    versions:
      gcc: "14.2"
      glibc: "2.41"
    cpu: cortex-a720
    file: arm64/debian13-a720ae-latest.tar.gz
    checksum: sha256:...
```

### Publishing Images

Use `publish` command to add images with proper metadata:

```bash
./cross-toolchain.py publish <docker-image>:<tag> \
    --name <manifest-name> \
    --arch arm64 \
    --cpu cortex-a720 \
    --gcc "14.2"
```

This:
1. Exports Docker image to tar
2. Compresses with pigz/gzip
3. Moves to `images/<arch>/`
4. Updates `manifest.yaml` with checksum

### Distributing Repository

**Via Git (with LFS):**
```bash
# Setup git-lfs for large files
git lfs track "images/**/*.tar.gz"
git add images/
git commit -m "Add prebuilt images"
```

**Via File Server:**
1. Upload `images/` to server
2. Update `repository.base_url` in `manifest.yaml`
3. Users download individual images as needed

## Maintenance Guidelines

1. **Adding configs**: Copy template, edit values
2. **Mirror updates**: Modify `MirrorSelector` class in `cross-toolchain.py`
3. **Version updates**: Change `versions` in config files
4. **Publishing images**: Use `publish` command for proper metadata
5. **Testing**: Run `build.sh` on each config before committing

## Lessons Learned

### Source Compilation Abandoned
Tried building GCC+glibc+binutils+gdb from source via Canadian Cross:
- Failed 20+ times due to circular dependencies
- Complex header paths, libgcc linking errors
- Network timeouts during builds

**Conclusion**: Use apt packages for reliability.

**Alternative**: For true source builds, users should use crosstool-ng instead.

## Usage

```bash
# Build default environment
./build.sh configs/default.yaml

# Custom tag
./build.sh configs/default.yaml my-env:latest

# Direct Python usage
./cross-toolchain.py generate configs/default.yaml -o Dockerfile
./cross-toolchain.py build configs/default.yaml -t my-env:latest

# Export/Import for offline transfer
./cross-toolchain.py export my-env:latest -o ./exports
./cross-toolchain.py import ./exports/my-env-latest.tar.gz
```

### Fixuid (Permission Handling)

All generated images include [fixuid](https://github.com/boxboat/fixuid) to automatically map container UIDs/GIDs to the host user at runtime. This avoids file permission issues when running with `-u $(id -u):$(id -g)`.

```bash
# Run as current user — fixuid will automatically adjust permissions
docker run -it --rm -u $(id -u):$(id -g) -v $(pwd):/workspace arm-cross:default
```
