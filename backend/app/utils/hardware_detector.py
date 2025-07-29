"""
Hardware Detection Utilities

Detects system capabilities for optimal configuration.
"""

import os
import platform
import subprocess
import logging
from typing import Dict, Optional, Tuple

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class HardwareDetector:
    """Detects and reports system hardware capabilities."""
    
    @staticmethod
    def detect_system_info() -> Dict[str, any]:
        """Detect comprehensive system information."""
        
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
        
        # CPU information
        cpu_info = HardwareDetector.detect_cpu()
        info.update(cpu_info)
        
        # Memory information
        memory_info = HardwareDetector.detect_memory()
        info.update(memory_info)
        
        # GPU information
        gpu_info = HardwareDetector.detect_gpu()
        info.update(gpu_info)
        
        # Cloud environment detection
        cloud_info = HardwareDetector.detect_cloud_environment()
        info.update(cloud_info)
        
        return info
    
    @staticmethod
    def detect_cpu() -> Dict[str, any]:
        """Detect CPU information."""
        
        cpu_info = {
            "cpu_count": os.cpu_count(),
            "cpu_count_physical": None,
            "cpu_freq": None,
            "cpu_usage": None
        }
        
        if PSUTIL_AVAILABLE:
            try:
                cpu_info.update({
                    "cpu_count_physical": psutil.cpu_count(logical=False),
                    "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                    "cpu_usage": psutil.cpu_percent(interval=1)
                })
            except Exception as e:
                logger.warning(f"Failed to get detailed CPU info: {e}")
        
        return cpu_info
    
    @staticmethod
    def detect_memory() -> Dict[str, any]:
        """Detect memory information."""
        
        memory_info = {
            "memory_total": None,
            "memory_available": None,
            "memory_percent": None,
            "swap_total": None,
            "swap_used": None
        }
        
        if PSUTIL_AVAILABLE:
            try:
                virtual_memory = psutil.virtual_memory()
                swap_memory = psutil.swap_memory()
                
                memory_info.update({
                    "memory_total": virtual_memory.total,
                    "memory_available": virtual_memory.available,
                    "memory_percent": virtual_memory.percent,
                    "swap_total": swap_memory.total,
                    "swap_used": swap_memory.used
                })
            except Exception as e:
                logger.warning(f"Failed to get memory info: {e}")
        else:
            # Fallback methods for different platforms
            if platform.system() == "Linux":
                try:
                    # Read from /proc/meminfo
                    with open('/proc/meminfo', 'r') as f:
                        meminfo = f.read()
                    
                    for line in meminfo.split('\n'):
                        if 'MemTotal:' in line:
                            memory_info["memory_total"] = int(line.split()[1]) * 1024
                        elif 'MemAvailable:' in line:
                            memory_info["memory_available"] = int(line.split()[1]) * 1024
                except Exception as e:
                    logger.warning(f"Failed to read /proc/meminfo: {e}")
        
        return memory_info
    
    @staticmethod
    def detect_gpu() -> Dict[str, any]:
        """Detect GPU information."""
        
        gpu_info = {
            "gpu_available": False,
            "gpu_count": 0,
            "gpu_devices": [],
            "cuda_available": False,
            "cuda_version": None
        }
        
        # Check CUDA availability with PyTorch
        if TORCH_AVAILABLE:
            try:
                gpu_info["cuda_available"] = torch.cuda.is_available()
                if torch.cuda.is_available():
                    gpu_info["gpu_available"] = True
                    gpu_info["gpu_count"] = torch.cuda.device_count()
                    gpu_info["cuda_version"] = torch.version.cuda
                    
                    # Get device information
                    devices = []
                    for i in range(torch.cuda.device_count()):
                        device_props = torch.cuda.get_device_properties(i)
                        devices.append({
                            "device_id": i,
                            "name": device_props.name,
                            "total_memory": device_props.total_memory,
                            "multi_processor_count": device_props.multi_processor_count,
                            "major": device_props.major,
                            "minor": device_props.minor
                        })
                    
                    gpu_info["gpu_devices"] = devices
            except Exception as e:
                logger.warning(f"Failed to get GPU info via PyTorch: {e}")
        
        # Fallback: Check nvidia-smi
        if not gpu_info["gpu_available"]:
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    gpu_info["gpu_available"] = True
                    lines = result.stdout.strip().split('\n')
                    gpu_info["gpu_count"] = len(lines)
                    
                    devices = []
                    for i, line in enumerate(lines):
                        parts = line.split(', ')
                        if len(parts) >= 2:
                            devices.append({
                                "device_id": i,
                                "name": parts[0].strip(),
                                "total_memory": int(parts[1].strip()) * 1024 * 1024  # Convert MB to bytes
                            })
                    
                    gpu_info["gpu_devices"] = devices
            except Exception as e:
                logger.warning(f"Failed to run nvidia-smi: {e}")
        
        return gpu_info
    
    @staticmethod
    def detect_cloud_environment() -> Dict[str, any]:
        """Detect if running in a cloud environment."""
        
        cloud_info = {
            "cloud_provider": "local",
            "instance_type": None,
            "region": None
        }
        
        # AWS detection
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "2", "http://169.254.169.254/latest/meta-data/instance-id"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0 and result.stdout.strip():
                cloud_info["cloud_provider"] = "aws"
                
                # Get instance type
                try:
                    result = subprocess.run(
                        ["curl", "-s", "--max-time", "2", "http://169.254.169.254/latest/meta-data/instance-type"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    if result.returncode == 0:
                        cloud_info["instance_type"] = result.stdout.strip()
                except Exception:
                    pass
                
                # Get region
                try:
                    result = subprocess.run(
                        ["curl", "-s", "--max-time", "2", "http://169.254.169.254/latest/meta-data/placement/region"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    if result.returncode == 0:
                        cloud_info["region"] = result.stdout.strip()
                except Exception:
                    pass
                
                return cloud_info
        except Exception:
            pass
        
        # Google Cloud detection
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "2", "-H", "Metadata-Flavor: Google", 
                 "http://metadata.google.internal/computeMetadata/v1/instance/machine-type"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0 and result.stdout.strip():
                cloud_info["cloud_provider"] = "gcp"
                cloud_info["instance_type"] = result.stdout.strip().split('/')[-1]
                return cloud_info
        except Exception:
            pass
        
        # Azure detection
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "2", "-H", "Metadata: true",
                 "http://169.254.169.254/metadata/instance?api-version=2021-02-01"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0 and result.stdout.strip():
                cloud_info["cloud_provider"] = "azure"
                return cloud_info
        except Exception:
            pass
        
        return cloud_info
    
    @staticmethod
    def get_optimal_configuration(system_info: Dict[str, any]) -> Dict[str, any]:
        """Get optimal configuration based on detected hardware."""
        
        config = {
            "device": "cpu",
            "batch_size": 4,
            "num_workers": 2,
            "memory_limit": "4GB",
            "enable_gpu": False,
            "concurrent_clones": 2
        }
        
        # GPU configuration
        if system_info.get("gpu_available", False):
            config["device"] = "cuda"
            config["enable_gpu"] = True
            
            # Adjust batch size based on GPU memory
            gpu_devices = system_info.get("gpu_devices", [])
            if gpu_devices:
                max_memory = max(device.get("total_memory", 0) for device in gpu_devices)
                if max_memory > 16 * 1024**3:  # 16GB
                    config["batch_size"] = 32
                elif max_memory > 8 * 1024**3:  # 8GB
                    config["batch_size"] = 16
                else:
                    config["batch_size"] = 8
        
        # CPU configuration
        cpu_count = system_info.get("cpu_count", 4)
        config["num_workers"] = min(cpu_count, 8)
        config["concurrent_clones"] = min(cpu_count // 2, 8)
        
        # Memory configuration
        memory_total = system_info.get("memory_total", 0)
        if memory_total > 0:
            memory_gb = memory_total // (1024**3)
            
            if memory_gb >= 32:
                config["memory_limit"] = "16GB"
                config["batch_size"] = min(config["batch_size"] * 2, 64)
            elif memory_gb >= 16:
                config["memory_limit"] = "8GB"
            elif memory_gb >= 8:
                config["memory_limit"] = "4GB"
            else:
                config["memory_limit"] = "2GB"
                config["batch_size"] = max(config["batch_size"] // 2, 2)
        
        # Cloud-specific optimizations
        cloud_provider = system_info.get("cloud_provider", "local")
        if cloud_provider != "local":
            # Enable more aggressive caching for cloud environments
            config["enable_caching"] = True
            config["cache_size"] = "1GB"
        
        return config
    
    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Format bytes into human readable format."""
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    @staticmethod
    def print_system_report():
        """Print a comprehensive system report."""
        
        print("=" * 60)
        print("SYSTEM HARDWARE REPORT")
        print("=" * 60)
        
        system_info = HardwareDetector.detect_system_info()
        
        print(f"Platform: {system_info['platform']} {system_info['platform_release']}")
        print(f"Architecture: {system_info['architecture']}")
        print(f"Python: {system_info['python_version']}")
        
        print("\nCPU:")
        print(f"  Cores: {system_info['cpu_count']} logical")
        if system_info.get('cpu_count_physical'):
            print(f"  Physical Cores: {system_info['cpu_count_physical']}")
        if system_info.get('cpu_usage'):
            print(f"  Usage: {system_info['cpu_usage']}%")
        
        print("\nMemory:")
        if system_info.get('memory_total'):
            total_gb = system_info['memory_total'] / (1024**3)
            print(f"  Total: {total_gb:.1f} GB")
        if system_info.get('memory_available'):
            available_gb = system_info['memory_available'] / (1024**3)
            print(f"  Available: {available_gb:.1f} GB")
        
        print("\nGPU:")
        if system_info.get('gpu_available'):
            print(f"  CUDA Available: {system_info.get('cuda_available', False)}")
            print(f"  Device Count: {system_info.get('gpu_count', 0)}")
            if system_info.get('cuda_version'):
                print(f"  CUDA Version: {system_info['cuda_version']}")
            
            for device in system_info.get('gpu_devices', []):
                memory_gb = device.get('total_memory', 0) / (1024**3)
                print(f"  Device {device['device_id']}: {device['name']} ({memory_gb:.1f} GB)")
        else:
            print("  No GPU detected")
        
        print("\nCloud Environment:")
        print(f"  Provider: {system_info.get('cloud_provider', 'local')}")
        if system_info.get('instance_type'):
            print(f"  Instance Type: {system_info['instance_type']}")
        
        print("\nOptimal Configuration:")
        config = HardwareDetector.get_optimal_configuration(system_info)
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        print("=" * 60)


if __name__ == "__main__":
    HardwareDetector.print_system_report()