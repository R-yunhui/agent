# 获取当前系统的硬件信息
import psutil
import platform
import socket
import datetime


def get_detailed_system_info():
    """获取详细的系统信息"""
    try:
        # 系统基本信息
        # CPU信息
        info = {'system': {
            'os': platform.system(),
            'os_version': platform.release(),
            'os_full_version': platform.version(),
            'hostname': socket.gethostname(),
            'ip_address': socket.gethostbyname(socket.gethostname()),
            'python_version': platform.python_version(),
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, 'cpu': {
            'logical_cores': psutil.cpu_count(logical=True),
            'physical_cores': psutil.cpu_count(logical=False),
            'usage_percent': psutil.cpu_percent(interval=1),
            'per_core_usage': psutil.cpu_percent(interval=0.1, percpu=True),
            'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else None
        }}

        # 内存信息
        memory = psutil.virtual_memory()
        info['memory'] = {
            'total_gb': memory.total / (1024 ** 3),
            'available_gb': memory.available / (1024 ** 3),
            'used_gb': memory.used / (1024 ** 3),
            'free_gb': memory.free / (1024 ** 3),
            'usage_percent': memory.percent,
            'active_gb': memory.active / (1024 ** 3) if hasattr(memory, 'active') else None,
            'inactive_gb': memory.inactive / (1024 ** 3) if hasattr(memory, 'inactive') else None
        }

        # 磁盘信息
        info['disk'] = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                info['disk'].append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total_gb': usage.total / (1024 ** 3),
                    'used_gb': usage.used / (1024 ** 3),
                    'free_gb': usage.free / (1024 ** 3),
                    'usage_percent': usage.percent
                })
            except PermissionError:
                continue

        # 网络信息
        info['network'] = {}
        net_io = psutil.net_io_counters()
        info['network']['bytes_sent'] = net_io.bytes_sent
        info['network']['bytes_recv'] = net_io.bytes_recv
        info['network']['packets_sent'] = net_io.packets_sent
        info['network']['packets_recv'] = net_io.packets_recv

        # 打印信息
        print("=" * 50)
        print("系统信息概览")
        print("=" * 50)

        print(f"主机名: {info['system']['hostname']}")
        print(f"IP地址: {info['system']['ip_address']}")
        print(f"操作系统: {info['system']['os']} {info['system']['os_version']}")
        print(f"Python版本: {info['system']['python_version']}")
        print(f"时间戳: {info['system']['timestamp']}")

        print("\nCPU信息:")
        print(f"  逻辑核心数: {info['cpu']['logical_cores']}")
        print(f"  物理核心数: {info['cpu']['physical_cores']}")
        print(f"  CPU使用率: {info['cpu']['usage_percent']}%")
        if info['cpu']['cpu_freq']:
            print(f"  CPU频率: {info['cpu']['cpu_freq']:.2f} MHz")

        print("\n内存信息:")
        print(f"  总内存: {info['memory']['total_gb']:.2f} GB")
        print(f"  可用内存: {info['memory']['available_gb']:.2f} GB")
        print(f"  已用内存: {info['memory']['used_gb']:.2f} GB")
        print(f"  内存使用率: {info['memory']['usage_percent']}%")

        return info

    except Exception as e:
        print(f"获取详细系统信息失败: {e}")
        return None


if __name__ == "__main__":
    # 安装psutil（如果尚未安装）
    try:
        import psutil
    except ImportError:
        print("正在安装psutil库...")
        import subprocess
        import sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil

    get_detailed_system_info()
