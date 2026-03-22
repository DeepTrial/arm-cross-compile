# ARM64 (AArch64) Cross-Compilation Environment
# Based on Ubuntu 22.04 LTS
FROM ubuntu:22.04

LABEL maintainer="your-email@example.com"
LABEL description="ARM64/AArch64 Cross Compilation Environment"

# Avoid interactive configuration
ENV DEBIAN_FRONTEND=noninteractive

# Install basic tools and dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    ca-certificates \
    python3 \
    python3-pip \
    qemu-user-static \
    binfmt-support \
    crossbuild-essential-arm64 \
    gcc-aarch64-linux-gnu \
    g++-aarch64-linux-gnu \
    libc6-dev-arm64-cross \
    libstdc++-11-dev-arm64-cross \
    gdb-multiarch \
    && rm -rf /var/lib/apt/lists/*

# Set cross-compilation environment variables
ENV CROSS_COMPILE=aarch64-linux-gnu-
ENV CC=aarch64-linux-gnu-gcc
ENV CXX=aarch64-linux-gnu-g++
ENV AR=aarch64-linux-gnu-ar
ENV AS=aarch64-linux-gnu-as
ENV LD=aarch64-linux-gnu-ld
ENV RANLIB=aarch64-linux-gnu-ranlib
ENV STRIP=aarch64-linux-gnu-strip

# Set working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]
