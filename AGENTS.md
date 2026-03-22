# ARM Cross-Compilation Environment Repository

## Project Overview

A flexible, configuration-driven system for managing ARM cross-compilation Docker environments. Instead of maintaining static Dockerfiles, this project uses YAML configuration files to generate Dockerfiles dynamically.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Config Files   │────▶│   Generator      │────▶│  Dockerfile     │
│  (YAML)         │     │   (Python)       │     │  (Generated)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌──────────────────┐
                                                │   Verifier       │
                                                │   (Python)       │
                                                └──────────────────┘
```

## Directory Structure

```
.
├── configs/                   # Environment configurations
│   ├── aarch64-toolchain.yaml
│   ├── armhf-toolchain.yaml
│   └── custom-example.yaml
├── generator/                 # Core generation and verification logic
│   ├── generate.py           # Dockerfile generator
│   └── verify.py             # Environment verifier
├── scripts/                   # User-facing scripts
│   ├── build-from-config.sh  # Main build orchestrator
│   ├── list-configs.sh       # Config listing utility
│   ├── build.sh              # Legacy build script
│   └── run.sh                # Container runner
├── templates/                 # Configuration templates
│   └── config-template.yaml
├── dockerfiles/
│   ├── generated/            # Auto-generated Dockerfiles
│   ├── aarch64/              # Legacy static Dockerfiles
│   └── armhf/
└── docs/                      # Additional documentation
```

## Workflow

### 1. Configuration

Users create YAML configuration files defining:
- Base image
- Target architecture
- Toolchain specification
- Required packages (grouped by category)
- Environment variables
- Custom installation steps

### 2. Generation

The `generate.py` script:
- Parses YAML configuration
- Validates required fields
- Generates Dockerfile using templates
- Outputs to `dockerfiles/generated/`

### 3. Build

The `build-from-config.sh` script:
- Calls generator to create Dockerfile
- Runs `docker build`
- Optionally verifies the result

### 4. Verification

The `verify.py` script:
- Checks Dockerfile syntax
- Builds test image
- Verifies toolchain installation
- Tests cross-compilation

## Configuration Format

See `templates/config-template.yaml` for full specification.

Key fields:
- `name`: Unique identifier
- `base_image`: Docker base image
- `architecture`: Target ARM architecture
- `toolchain`: Compiler toolchain specification
- `packages`: Categorized package lists
- `env`: Environment variables
- `custom_steps`: Additional RUN commands

## Usage Patterns

### Standard Build
```bash
./scripts/build-from-config.sh configs/aarch64-toolchain.yaml
```

### Custom Configuration
```bash
cp templates/config-template.yaml configs/my-project.yaml
# Edit my-project.yaml
./scripts/build-from-config.sh configs/my-project.yaml --tag my-project:latest
```

### CI/CD Integration
```bash
# Validate only
./scripts/build-from-config.sh configs/aarch64-toolchain.yaml --validate-only

# Generate without build
python3 generator/generate.py configs/aarch64-toolchain.yaml -o dockerfiles/generated/aarch64/Dockerfile
```

## Maintenance Notes

1. **Adding New Architectures**: Create a config in `configs/`, no code changes needed
2. **Generator Updates**: Maintain backward compatibility with existing configs
3. **Template Changes**: Update `templates/config-template.yaml` when adding features
4. **Testing**: Run verification on all configs before committing changes
