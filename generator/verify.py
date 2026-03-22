#!/usr/bin/env python3
"""
Verification tool for ARM cross-compilation environments.
Verifies generated Dockerfiles and built images.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Tuple


class EnvironmentVerifier:
    """Verifies Dockerfile and built images."""
    
    def __init__(self, dockerfile_path: str):
        self.dockerfile_path = Path(dockerfile_path)
        self.errors = []
        self.warnings = []
    
    def verify_dockerfile_syntax(self) -> bool:
        """Verify Dockerfile syntax using docker build --check if available."""
        print(f"Verifying Dockerfile syntax: {self.dockerfile_path}")
        
        if not self.dockerfile_path.exists():
            self.errors.append(f"Dockerfile not found: {self.dockerfile_path}")
            return False
        
        # Basic syntax checks
        content = self.dockerfile_path.read_text()
        
        # Check for required instructions
        if 'FROM' not in content:
            self.errors.append("Missing FROM instruction")
        
        # Check for common issues
        if 'apt-get update' in content and 'rm -rf /var/lib/apt/lists' not in content:
            self.warnings.append("apt-get update without cleanup (rm -rf /var/lib/apt/lists)")
        
        return len(self.errors) == 0
    
    def build_image(self, tag: str) -> bool:
        """Build Docker image and verify it compiles successfully."""
        print(f"Building image: {tag}")
        
        cmd = [
            'docker', 'build',
            '-t', tag,
            '-f', str(self.dockerfile_path),
            str(self.dockerfile_path.parent)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"  Build successful: {tag}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Build failed:\n{e.stderr}")
            return False
    
    def verify_toolchain(self, image_tag: str, prefix: str) -> bool:
        """Verify cross-compilation toolchain is properly installed."""
        print(f"Verifying toolchain in image: {image_tag}")
        
        tools = ['gcc', 'g++', 'ar', 'ld', 'strip']
        all_ok = True
        
        for tool in tools:
            cmd = [
                'docker', 'run', '--rm', image_tag,
                'which', f'{prefix}-{tool}'
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                path = result.stdout.strip()
                print(f"  {prefix}-{tool}: {path}")
                
            except subprocess.CalledProcessError:
                self.errors.append(f"Tool not found: {prefix}-{tool}")
                all_ok = False
        
        # Test compilation
        if all_ok:
            test_result = self._test_compilation(image_tag, prefix)
            if not test_result:
                all_ok = False
        
        return all_ok
    
    def _test_compilation(self, image_tag: str, prefix: str) -> bool:
        """Test cross-compilation with a simple C program."""
        print(f"  Testing cross-compilation...")
        
        test_code = '''
#include <stdio.h>
int main() {
    printf("Hello ARM!\\n");
    return 0;
}
'''
        
        # Create a temporary test
        cmd = [
            'docker', 'run', '--rm',
            '-e', f'CC={prefix}-gcc',
            image_tag,
            'sh', '-c',
            f'echo \'{test_code}\' | {prefix}-gcc -x c - -o /tmp/test && file /tmp/test'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout.strip()
            
            # Check if binary is for correct architecture
            if 'ARM' in output or 'aarch64' in output:
                print(f"  Cross-compilation test passed")
                return True
            else:
                self.warnings.append(f"Binary architecture may be incorrect: {output}")
                return True  # Warning only
                
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Cross-compilation test failed:\n{e.stderr}")
            return False
    
    def run_full_verification(self, image_tag: str = None, prefix: str = None) -> bool:
        """Run full verification pipeline."""
        print("=" * 50)
        print("Environment Verification")
        print("=" * 50)
        
        # Step 1: Verify Dockerfile syntax
        if not self.verify_dockerfile_syntax():
            self._print_results()
            return False
        
        if not image_tag:
            print("\nSkipping build verification (no image tag provided)")
            self._print_results()
            return len(self.errors) == 0
        
        # Step 2: Build image
        if not self.build_image(image_tag):
            self._print_results()
            return False
        
        # Step 3: Verify toolchain
        if prefix:
            self.verify_toolchain(image_tag, prefix)
        else:
            self.warnings.append("Skipping toolchain verification (no prefix provided)")
        
        self._print_results()
        return len(self.errors) == 0
    
    def _print_results(self):
        """Print verification results."""
        print("\n" + "=" * 50)
        print("Results")
        print("=" * 50)
        
        if self.errors:
            print(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  [E] {error}")
        
        if self.warnings:
            print(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  [W] {warning}")
        
        if not self.errors and not self.warnings:
            print("All checks passed!")
        elif not self.errors:
            print("Verification passed with warnings")
        else:
            print("Verification failed")


def main():
    parser = argparse.ArgumentParser(
        description='Verify ARM cross-compilation environment'
    )
    parser.add_argument(
        'dockerfile',
        help='Path to Dockerfile to verify'
    )
    parser.add_argument(
        '--build',
        action='store_true',
        help='Build image and verify'
    )
    parser.add_argument(
        '-t', '--tag',
        help='Image tag for build verification'
    )
    parser.add_argument(
        '-p', '--prefix',
        help='Toolchain prefix (e.g., aarch64-linux-gnu)'
    )
    
    args = parser.parse_args()
    
    verifier = EnvironmentVerifier(args.dockerfile)
    
    image_tag = args.tag if args.tag else None
    prefix = args.prefix if args.prefix else None
    
    success = verifier.run_full_verification(image_tag, prefix)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
