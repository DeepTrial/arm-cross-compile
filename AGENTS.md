# ARM Cross-Compilation Environment Repository

## Project Overview

This repository manages Docker images for various ARM architecture cross-compilation environments, enabling unified management and rapid deployment of compilation environments for different architectures.

## Project Structure

```
.
├── dockerfiles/           # Dockerfiles for each architecture
│   ├── aarch64/          # ARM64 / ARMv8-A
│   │   └── Dockerfile
│   ├── armhf/            # ARM hard-float (ARMv7+)
│   │   └── Dockerfile
│   ├── armel/            # ARM soft-float (to be added)
│   └── armv7/            # ARMv7 specific (to be added)
├── scripts/               # Build and utility scripts
│   ├── build.sh          # Build image for specified architecture
│   └── run.sh            # Run container for specified architecture
├── configs/               # Configuration files
├── examples/              # Example projects
├── docs/                  # Documentation
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation

```

## Usage

### Build Image

```bash
./scripts/build.sh <architecture> [tag]
```

### Run Container

```bash
./scripts/run.sh <architecture> [workspace]
```

## Maintenance Notes

1. Create corresponding directory under `dockerfiles/` when adding new architectures
2. Maintain backward compatibility when updating scripts
3. Commit promptly after testing
