# ARM hard-float (armhf) Cross-Compilation Environment
# Based on Ubuntu 22.04 LTS
FROM ubuntu:22.04

LABEL maintainer="your-email@example.com"
LABEL description="ARM HF (ARMv7+) Cross Compilation Environment"

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
    crossbuild-essential-armhf \
    gcc-arm-linux-gnueabihf \
    g++-arm-linux-gnueabihf \
    libc6-dev-armhf-cross \
    libstdc++-11-dev-armhf-cross \
    gdb-multiarch \
    && rm -rf /var/lib/apt/lists/*

# Set cross-compilation environment variables
ENV CROSS_COMPILE=arm-linux-gnueabihf-
ENV CC=arm-linux-gnueabihf-gcc
ENV CXX=arm-linux-gnueabihf-g++
ENV AR=arm-linux-gnueabihf-ar
ENV AS=arm-linux-gnueabihf-as
ENV LD=arm-linux-gnueabihf-ld
ENV RANLIB=arm-linux-gnueabihf-ranlib
ENV STRIP=arm-linux-gnueabihf-strip

WORKDIR /workspace

CMD ["/bin/bash"]
