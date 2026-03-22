# Contributing Guide

Thank you for your interest in contributing to ARM Cross-Compilation Environment!

## Development Workflow

### 1. Fork and Clone

```bash
git clone git@github.com:YOUR_USERNAME/ARM-Cross-Compile.git
cd ARM-Cross-Compile
```

### 2. Create a Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/my-bugfix
```

### 3. Make Changes and Test Locally

```bash
# Test config generation
./cross-toolchain.py generate configs/default.yaml -o /tmp/test.dockerfile

# Build and test image
./build.sh configs/default.yaml test-image:latest

# Verify cross-compilation works
docker run --rm test-image:latest aarch64-linux-gnu-gcc --version
```

### 4. Commit

```bash
git add .
git commit -m "feat: add support for XXX"
```

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `ci:` - CI/CD changes
- `refactor:` - Code refactoring

### 5. Push and Create PR

```bash
git push origin feature/my-feature
```

Then create a Pull Request on GitHub.

## CI/CD Checks

Your PR will trigger the following checks:

| Check | Description |
|-------|-------------|
| `lint` | Python code linting with flake8 |
| `validate-yaml` | Config file validation |
| `generate-dockerfile` | Test Dockerfile generation |
| `build-image` | Build Docker image (main branch only) |

All checks must pass before merging.

## Adding New Configurations

1. Copy `templates/config-template.yaml`:
```bash
cp templates/config-template.yaml configs/my-config.yaml
```

2. Edit the config with your specifications

3. Test locally:
```bash
./build.sh configs/my-config.yaml
```

4. Commit and push

## Publishing Prebuilt Images

Maintainers can publish images to the repository:

```bash
# After building a new image
./build.sh configs/default.yaml my-release:latest

# Publish to images/ directory
./build.sh publish my-release:latest \
    --name my-release \
    --arch arm64 \
    --gcc "14.2" \
    --description "My custom release"

# Commit the new image
git add images/
git commit -m "feat: add my-release prebuilt image"
git push
```

## Release Process

1. Update version references in configs if needed
2. Tag a release:
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```
3. CI will automatically:
   - Build and push to GHCR (`ghcr.io/deeptrial/arm-cross-compile:v1.0.0`)
   - Create GitHub Release with exported image

## Code Style

- Python: Follow PEP 8
- Shell scripts: Use `shellcheck` for validation
- YAML: Use 2-space indentation
- Commit messages: Use conventional commits format

## Questions?

Open an issue on GitHub for:
- Bug reports
- Feature requests
- Questions about usage
