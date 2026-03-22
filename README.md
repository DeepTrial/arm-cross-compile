# ARM Cross-Compilation Environment Repository

This repository manages Docker images for various ARM architecture cross-compilation environments.

## Supported Architectures

| Architecture | Directory | Description |
|-------------|-----------|-------------|
| aarch64 | `dockerfiles/aarch64/` | ARM64 / ARMv8-A |
| armhf | `dockerfiles/armhf/` | ARM hard-float (ARMv7+) |
| armel | `dockerfiles/armel/` | ARM soft-float |
| armv7 | `dockerfiles/armv7/` | ARMv7 specific |

## Directory Structure

```
.
├── dockerfiles/       # Dockerfiles for each architecture
│   ├── aarch64/
│   ├── armhf/
│   ├── armel/
│   └── armv7/
├── scripts/           # Build and utility scripts
├── configs/           # Configuration files
├── examples/          # Example projects
└── docs/              # Documentation
```

## Quick Start

### Build Image

```bash
# Build aarch64 cross-compilation environment
cd dockerfiles/aarch64
docker build -t arm-cross:aarch64 .

# Or use the script
./scripts/build.sh aarch64
```

### Run Container

```bash
# Run container
docker run -it --rm -v $(pwd):/workspace arm-cross:aarch64
```

## Contributing Guidelines

1. Create a dedicated directory under `dockerfiles/` for each new architecture
2. Dockerfiles should include clear comments
3. Add corresponding build scripts to the `scripts/` directory
