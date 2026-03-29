#!/usr/bin/env python3
"""
ARM Cross-Compilation Environment Generator
Simple version-based configuration with automatic mirror selection.

Usage:
  ./cross-toolchain.py generate <config.yaml> -o Dockerfile
  ./cross-toolchain.py build <config.yaml> [-t tag]
"""

import os
import sys
import yaml
import argparse
import subprocess
import socket
from pathlib import Path
from typing import Dict, List, Any, Optional


class MirrorSelector:
    """Auto-select best mirrors based on network environment"""
    
    DOCKER_MIRRORS = [
        ("docker.m.daocloud.io", "DaoCloud"),
        ("docker.1panel.live", "1Panel"),
        ("hub.rat.dev", "Rat"),
    ]
    
    APT_MIRRORS = {
        "debian": [
            ("http://mirrors.aliyun.com/debian", "Aliyun"),
            ("http://mirrors.tuna.tsinghua.edu.cn/debian", "Tsinghua"),
        ],
        "ubuntu": [
            ("http://mirrors.aliyun.com/ubuntu", "Aliyun"),
            ("http://mirrors.tuna.tsinghua.edu.cn/ubuntu", "Tsinghua"),
        ],
    }
    
    @staticmethod
    def check(host: str, port: int = 443, timeout: int = 3) -> bool:
        try:
            socket.setdefaulttimeout(timeout)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.close()
            return True
        except:
            return False
    
    @classmethod
    def select(cls) -> Dict[str, str]:
        print("Detecting mirrors...")
        mirrors = {}
        
        # Docker mirror
        for host, name in cls.DOCKER_MIRRORS:
            if cls.check(host):
                print(f"  [OK] Docker: {name}")
                mirrors['docker'] = host
                break
            print(f"  [FAIL] Docker: {name}")
        
        # APT mirrors
        for distro in ['debian', 'ubuntu']:
            for url, name in cls.APT_MIRRORS[distro]:
                host = url.split('/')[2]
                if cls.check(host, port=80):
                    print(f"  [OK] APT ({distro}): {name}")
                    mirrors[f'apt_{distro}'] = url
                    break
                print(f"  [FAIL] APT ({distro}): {name}")
        
        return mirrors


class DockerfileGenerator:
    """Generate Dockerfile from YAML configuration"""
    
    OFFICIAL_IMAGES = ['debian', 'ubuntu', 'alpine', 'centos', 'fedora']
    
    def __init__(self, config_path: str):
        self.config = yaml.safe_load(open(config_path))
        self.mirrors = {}
    
    def select_mirrors(self):
        self.mirrors = MirrorSelector.select()
    
    def get_base_image(self) -> str:
        base = self.config['base_image']
        image_name = base.split(':')[0].split('/')[0]
        
        if 'docker' in self.mirrors and image_name in self.OFFICIAL_IMAGES:
            return f"{self.mirrors['docker']}/{base}"
        return base
    
    def get_apt_mirror(self) -> Optional[str]:
        base = self.config['base_image']
        if 'debian' in base:
            return self.mirrors.get('apt_debian')
        elif 'ubuntu' in base:
            return self.mirrors.get('apt_ubuntu')
        return None
    
    def generate_apt_mode(self) -> str:
        """Generate Dockerfile using apt packages (fast)"""
        cfg = self.config
        base = self.get_base_image()
        
        versions = cfg.get('versions', {})
        gcc_ver = versions.get('gcc', '14')
        # Debian apt package names use major version only (e.g., gcc-14, not gcc-14.2)
        gcc_pkg_ver = gcc_ver.split('.')[0]
        cpu = cfg.get('cpu', 'generic')
        
        # CFLAGS for CPU optimization
        cflags = ""
        if cpu and cpu != 'generic':
            cflags = f"-mcpu={cpu} -march=armv8.2-a -O2"
        
        # Handle multi-line description
        description = cfg.get('description', 'ARM Cross-Compilation Environment')
        desc_lines = [f"# {line}" for line in description.strip().split('\n')]
        
        lines = desc_lines + [
            f"FROM {base}",
            "",
            f"LABEL name=\"{cfg['name']}\"",
            f"LABEL arch=\"{cfg['architecture']}\"",
            "",
        ]
        
        # Collect env vars, avoiding duplicates
        env_vars = {}
        if cflags:
            env_vars['CFLAGS'] = f'"{cflags}"'
            env_vars['CXXFLAGS'] = f'"{cflags}"'
        for k, v in cfg.get('env', {}).items():
            if k not in env_vars:
                env_vars[k] = v
        
        # Add ENV directives
        for k, v in env_vars.items():
            lines.append(f"ENV {k}={v}")
        
        # APT mirror
        apt_mirror = self.get_apt_mirror()
        if apt_mirror:
            lines.extend([
                "",
                f"# Using APT mirror: {apt_mirror}",
                f"RUN sed -i 's|http://deb.debian.org/debian|{apt_mirror}|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true",
            ])
        
        # Collect packages
        pkgs = cfg.get('packages', {})
        all_pkgs = []
        for cat in ['base', 'qemu', 'libs']:
            if cat in pkgs:
                all_pkgs.extend(pkgs[cat])
        
        # Add toolchain packages
        all_pkgs.extend([
            f'gcc-{gcc_pkg_ver}-aarch64-linux-gnu',
            f'g++-{gcc_pkg_ver}-aarch64-linux-gnu',
            'libc6-dev-arm64-cross',
            'binutils-aarch64-linux-gnu',
            'gdb-multiarch',
        ])
        
        # Remove duplicates
        seen = set()
        unique = [p for p in all_pkgs if not (p in seen or seen.add(p))]
        
        lines.extend([
            "",
            "RUN apt-get update && apt-get install -y \\",
        ])
        for pkg in unique:
            lines.append(f"    {pkg} \\")
        lines.append("    && rm -rf /var/lib/apt/lists/*")
        
        # Create symlinks
        lines.extend([
            "",
            "# Create gcc/g++ symlinks",
            f"RUN ln -sf /usr/bin/aarch64-linux-gnu-gcc-{gcc_pkg_ver} /usr/bin/aarch64-linux-gnu-gcc && \\",
            f"    ln -sf /usr/bin/aarch64-linux-gnu-g++-{gcc_pkg_ver} /usr/bin/aarch64-linux-gnu-g++",
        ])
        
        # Add fixuid for permission handling
        lines.extend([
            "",
            "# Add fixuid for runtime UID/GID mapping",
            "RUN groupadd -r developer && \\",
            "    useradd -r -g developer -m -d /home/developer -s /bin/bash developer && \\",
            "    mkdir -p /etc/fixuid && \\",
            "    printf 'user: developer\\ngroup: developer\\npaths:\\n  - /workspace\\n  - /home/developer\\n' > /etc/fixuid/config.yml && \\",
            "    ARCH=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/;s/armv7l/arm/') && \\",
            "    curl -fsSL https://github.com/boxboat/fixuid/releases/download/v0.6.0/fixuid-0.6.0-linux-${ARCH}.tar.gz | tar -C /usr/local/bin -xzf - && \\",
            "    chmod 4755 /usr/local/bin/fixuid && \\",
            "    chown -R developer:developer /workspace /home/developer",
        ])
        
        # Verification
        lines.extend([
            "",
            "# Verify installation",
            "RUN echo '=== Cross-Compilation Environment ===' && \\",
            "    aarch64-linux-gnu-gcc --version | head -1 && \\",
            "    gdb-multiarch --version | head -1 && \\",
            "    aarch64-linux-gnu-ld --version | head -1",
        ])
        
        lines.extend([
            "",
            "WORKDIR /workspace",
            'ENTRYPOINT ["fixuid", "-q"]',
            'CMD ["/bin/bash"]',
        ])
        
        return '\n'.join(lines)
    
    def generate(self) -> str:
        versions = self.config.get('versions', {})
        
        if versions.get('from_source'):
            print("Warning: from_source mode not implemented in simplified version")
            print("Use 'from-source.yaml' config or implement custom steps")
            return self.generate_apt_mode()  # Fallback to apt
        
        return self.generate_apt_mode()
    
    def save(self, output: str):
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(self.generate())
        print(f"Generated: {output}")


def cmd_generate(args):
    gen = DockerfileGenerator(args.config)
    if args.auto_mirror:
        gen.select_mirrors()
    
    output = args.output or f"dockerfiles/{Path(args.config).stem}/Dockerfile"
    gen.save(output)
    return 0


def cmd_build(args):
    gen = DockerfileGenerator(args.config)
    if args.auto_mirror:
        gen.select_mirrors()
    
    tag = args.tag or f"arm-cross:{Path(args.config).stem}"
    config_name = Path(args.config).stem
    dockerfile = f"/tmp/Dockerfile.{config_name}"
    dockerdir = f"/tmp/dockerbuild-{config_name}"
    
    gen.save(dockerfile)
    
    # Copy to build dir
    Path(dockerdir).mkdir(parents=True, exist_ok=True)
    Path(dockerfile).rename(Path(dockerdir) / "Dockerfile")
    
    print(f"\nBuilding: {tag}")
    print("=" * 50)
    
    try:
        subprocess.run(['docker', 'build', '-t', tag, dockerdir], check=True)
        print("=" * 50)
        print(f"✓ Build complete: {tag}")
        print(f"  Run: docker run -it --rm -v $(pwd):/workspace {tag}")
        print(f"  Run as current user: docker run -it --rm -u $(id -u):$(id -g) -v $(pwd):/workspace {tag}")
        return 0
    except subprocess.CalledProcessError:
        print("=" * 50)
        print("✗ Build failed")
        return 1


def cmd_export(args):
    """Export Docker image to tar.gz file for offline transfer"""
    image = args.image
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse image name for filename
    image_name = image.replace(':', '-').replace('/', '-')
    tar_path = output_dir / f"{image_name}.tar"
    gz_path = output_dir / f"{image_name}.tar.gz"
    
    # Check if image exists
    result = subprocess.run(['docker', 'images', '-q', image], 
                          capture_output=True, text=True)
    if not result.stdout.strip():
        print(f"Error: Image '{image}' not found!")
        print("Available images:")
        subprocess.run(['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}'])
        return 1
    
    print(f"=== Export Docker Image ===")
    print(f"Image: {image}")
    print(f"Output: {gz_path}")
    print()
    
    # Export to tar
    print(f"[1/3] Exporting image...")
    try:
        subprocess.run(['docker', 'save', image, '-o', str(tar_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"✗ Export failed: {e}")
        return 1
    
    # Compress
    print(f"[2/3] Compressing...")
    try:
        # Use pigz if available (multi-threaded), fallback to gzip
        if subprocess.run(['which', 'pigz'], capture_output=True).returncode == 0:
            with open(tar_path, 'rb') as f_in:
                subprocess.run(['pigz', '-c'], stdin=f_in, stdout=open(gz_path, 'wb'), check=True)
            print(f"  Used: pigz (multi-threaded)")
        else:
            with open(tar_path, 'rb') as f_in:
                subprocess.run(['gzip', '-c'], stdin=f_in, stdout=open(gz_path, 'wb'), check=True)
            print(f"  Used: gzip")
    except subprocess.CalledProcessError as e:
        print(f"✗ Compression failed: {e}")
        tar_path.unlink(missing_ok=True)
        return 1
    
    # Clean up tar file
    print(f"[3/3] Cleaning up...")
    tar_path.unlink(missing_ok=True)
    
    # Get file size
    size = gz_path.stat().st_size
    size_mb = size / (1024 * 1024)
    
    print()
    print(f"✓ Export complete!")
    print(f"  File: {gz_path}")
    print(f"  Size: {size_mb:.1f} MB")
    print()
    print(f"To import on another machine:")
    print(f"  ./cross-toolchain.py import {gz_path}")
    print(f"  # or")
    print(f"  docker load -i {gz_path.name}")
    
    return 0


def cmd_import(args):
    """Import Docker image from tar.gz file"""
    input_file = Path(args.file)
    
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        return 1
    
    size_mb = input_file.stat().st_size / (1024 * 1024)
    
    print(f"=== Import Docker Image ===")
    print(f"File: {input_file}")
    print(f"Size: {size_mb:.1f} MB")
    print()
    
    # Check file type and decompress if needed
    if input_file.suffix == '.gz' or str(input_file).endswith('.tar.gz'):
        print(f"[1/2] Decompressing...")
        tar_path = Path('/tmp') / input_file.stem
        try:
            with open(input_file, 'rb') as f_in:
                result = subprocess.run(['gunzip', '-c'], stdin=f_in, 
                                      stdout=open(tar_path, 'wb'), check=True)
        except subprocess.CalledProcessError as e:
            print(f"✗ Decompression failed: {e}")
            return 1
    else:
        tar_path = input_file
        print(f"[1/2] Using tar directly...")
    
    # Load image
    print(f"[2/2] Loading image into Docker...")
    try:
        subprocess.run(['docker', 'load', '-i', str(tar_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"✗ Import failed: {e}")
        if tar_path != input_file:
            tar_path.unlink(missing_ok=True)
        return 1
    
    # Clean up temp file
    if tar_path != input_file:
        tar_path.unlink(missing_ok=True)
    
    print()
    print(f"✓ Import complete!")
    # Extract image name from filename (e.g., debian13-a720ae-latest -> debian13-a720ae:latest)
    image_name = input_file.stem.replace('-latest', '').replace('-', ':', 1)
    print(f"  Verify: docker images | grep {image_name}")
    
    return 0


class ImageManager:
    """Manage prebuilt images repository"""
    
    MANIFEST_FILE = 'images/manifest.yaml'
    IMAGES_DIR = 'images'
    
    def __init__(self):
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        if os.path.exists(self.MANIFEST_FILE):
            return yaml.safe_load(open(self.MANIFEST_FILE)) or {}
        return {'images': {}}
    
    def _save_manifest(self):
        Path(self.MANIFEST_FILE).parent.mkdir(parents=True, exist_ok=True)
        yaml.dump(self.manifest, open(self.MANIFEST_FILE, 'w'), 
                  default_flow_style=False, sort_keys=False)
    
    def list_images(self, arch: Optional[str] = None) -> List[Dict]:
        """List available prebuilt images"""
        images = []
        for name, info in self.manifest.get('images', {}).items():
            if arch and info.get('arch') != arch:
                continue
            images.append({
                'name': name,
                **info
            })
        return images
    
    def add_image(self, name: str, arch: str, file_path: str, 
                  versions: Dict, cpu: str = 'generic', description: str = ''):
        """Add a new prebuilt image to manifest"""
        file_obj = Path(file_path)
        if not file_obj.exists():
            print(f"Error: File not found: {file_path}")
            return False
        
        # Move to images directory
        target_dir = Path(self.IMAGES_DIR) / arch
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / file_obj.name
        
        # Copy file
        import shutil
        shutil.copy2(file_path, target_file)
        
        # Calculate checksum
        import hashlib
        sha256 = hashlib.sha256()
        with open(target_file, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        
        # Update manifest
        size_mb = target_file.stat().st_size / (1024 * 1024)
        from datetime import datetime
        
        self.manifest['images'][name] = {
            'name': name,
            'tag': 'latest',
            'arch': arch,
            'description': description or f"Prebuilt {name}",
            'size': f"~{size_mb:.0f}MB",
            'versions': versions,
            'cpu': cpu,
            'file': str(target_file.relative_to(self.IMAGES_DIR)),
            'checksum': f"sha256:{sha256.hexdigest()}",
            'created': datetime.now().strftime('%Y-%m-%d'),
        }
        
        self._save_manifest()
        print(f"✓ Added {name} to prebuilt images")
        print(f"  File: {target_file}")
        print(f"  Size: {size_mb:.1f} MB")
        return True
    
    def install_image(self, name: str) -> bool:
        """Install a prebuilt image from manifest"""
        if name not in self.manifest.get('images', {}):
            print(f"Error: Image '{name}' not found in manifest")
            print(f"Run './cross-toolchain.py images' to list available images")
            return False
        
        info = self.manifest['images'][name]
        image_file = Path(self.IMAGES_DIR) / info['file']
        
        if not image_file.exists():
            print(f"Error: Image file not found: {image_file}")
            print(f"The image may need to be downloaded from: {self.manifest.get('repository', {}).get('base_url', 'N/A')}")
            return False
        
        print(f"Installing {name}...")
        result = subprocess.run(['docker', 'load', '-i', str(image_file)])
        return result.returncode == 0
    
    def get_image_path(self, name: str) -> Optional[Path]:
        """Get path to image file"""
        if name not in self.manifest.get('images', {}):
            return None
        info = self.manifest['images'][name]
        path = Path(self.IMAGES_DIR) / info['file']
        return path if path.exists() else None


def cmd_images(args):
    """List available prebuilt images"""
    manager = ImageManager()
    images = manager.list_images(arch=args.arch)
    
    if not images:
        print("No prebuilt images available.")
        print(f"Add images to '{ImageManager.IMAGES_DIR}/' directory")
        return 0
    
    print("=" * 80)
    print(f"{'Name':<20} {'Arch':<8} {'Size':<10} {'CPU':<15} {'Description'}")
    print("=" * 80)
    
    for img in images:
        name = img['name']
        arch = img.get('arch', 'unknown')
        size = img.get('size', 'unknown')
        cpu = img.get('cpu', 'generic')
        desc = img.get('description', '')[:35]
        print(f"{name:<20} {arch:<8} {size:<10} {cpu:<15} {desc}")
    
    print("=" * 80)
    print(f"\nTotal: {len(images)} image(s)")
    print("\nTo install: ./cross-toolchain.py install <name>")
    print("To add:     ./cross-toolchain.py publish <image:tag> --name <name>")
    return 0


def cmd_install(args):
    """Install a prebuilt image"""
    manager = ImageManager()
    return 0 if manager.install_image(args.name) else 1


def cmd_publish(args):
    """Publish a built image to prebuilt repository"""
    manager = ImageManager()
    
    # Check if docker image exists
    result = subprocess.run(['docker', 'images', '-q', args.image], 
                          capture_output=True, text=True)
    if not result.stdout.strip():
        print(f"Error: Docker image '{args.image}' not found")
        return 1
    
    # Parse image info
    image_parts = args.image.split(':')
    image_name = image_parts[0]
    image_tag = image_parts[1] if len(image_parts) > 1 else 'latest'
    
    # Use provided name or derive from image
    publish_name = args.name or image_name.replace('/', '-')
    
    # Determine arch from config or default
    arch = args.arch or 'arm64'
    
    # Export first
    print(f"Publishing {args.image} as '{publish_name}'...")
    
    temp_dir = Path('/tmp') / f"publish-{publish_name}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    tar_file = temp_dir / f"{publish_name}-{image_tag}.tar"
    gz_file = temp_dir / f"{publish_name}-{image_tag}.tar.gz"
    
    # Export
    print("[1/3] Exporting from Docker...")
    subprocess.run(['docker', 'save', args.image, '-o', str(tar_file)], check=True)
    
    # Compress
    print("[2/3] Compressing...")
    with open(tar_file, 'rb') as f_in:
        if subprocess.run(['which', 'pigz'], capture_output=True).returncode == 0:
            subprocess.run(['pigz', '-c'], stdin=f_in, stdout=open(gz_file, 'wb'), check=True)
        else:
            subprocess.run(['gzip', '-c'], stdin=f_in, stdout=open(gz_file, 'wb'), check=True)
    
    tar_file.unlink(missing_ok=True)
    
    # Add to manifest
    print("[3/3] Adding to manifest...")
    versions = {}
    if args.gcc:
        versions['gcc'] = args.gcc
    if args.glibc:
        versions['glibc'] = args.glibc
    
    manager.add_image(
        name=publish_name,
        arch=arch,
        file_path=str(gz_file),
        versions=versions,
        cpu=args.cpu or 'generic',
        description=args.description or f"Prebuilt {publish_name}"
    )
    
    # Cleanup
    gz_file.unlink(missing_ok=True)
    temp_dir.rmdir()
    
    print(f"\n✓ Published {publish_name}")
    print(f"  Install with: ./cross-toolchain.py install {publish_name}")
    return 0


def main():
    parser = argparse.ArgumentParser(description='ARM Cross-Compilation Tool')
    sub = parser.add_subparsers(dest='cmd', required=True)
    
    # generate
    g = sub.add_parser('generate', help='Generate Dockerfile')
    g.add_argument('config', help='YAML config file')
    g.add_argument('-o', '--output', help='Output path')
    g.add_argument('--auto-mirror', action='store_true', help='Auto-select mirrors')
    g.set_defaults(func=cmd_generate)
    
    # build
    b = sub.add_parser('build', help='Generate and build')
    b.add_argument('config', help='YAML config file')
    b.add_argument('-t', '--tag', help='Image tag')
    b.add_argument('--auto-mirror', action='store_true', help='Auto-select mirrors')
    b.set_defaults(func=cmd_build)
    
    # export
    e = sub.add_parser('export', help='Export image to tar.gz')
    e.add_argument('image', help='Image name:tag (e.g., debian13-arm64:latest)')
    e.add_argument('-o', '--output', default='./exports', help='Output directory')
    e.set_defaults(func=cmd_export)
    
    # import
    i = sub.add_parser('import', help='Import image from tar.gz')
    i.add_argument('file', help='Path to tar.gz file')
    i.set_defaults(func=cmd_import)
    
    # images - list prebuilt images
    img = sub.add_parser('images', help='List available prebuilt images')
    img.add_argument('--arch', help='Filter by architecture (arm64/armhf)')
    img.set_defaults(func=cmd_images)
    
    # install - install prebuilt image
    inst = sub.add_parser('install', help='Install a prebuilt image')
    inst.add_argument('name', help='Image name from manifest')
    inst.set_defaults(func=cmd_install)
    
    # publish - add image to prebuilt repository
    pub = sub.add_parser('publish', help='Publish image to prebuilt repository')
    pub.add_argument('image', help='Docker image name:tag')
    pub.add_argument('--name', help='Name in manifest (default: image name)')
    pub.add_argument('--arch', default='arm64', help='Architecture (default: arm64)')
    pub.add_argument('--cpu', default='generic', help='CPU optimization (default: generic)')
    pub.add_argument('--gcc', help='GCC version')
    pub.add_argument('--glibc', help='glibc version')
    pub.add_argument('--description', help='Image description')
    pub.set_defaults(func=cmd_publish)
    
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == '__main__':
    main()
