"""
Python OS库和Pathlib库详解与示例

OS库提供了与操作系统交互的功能，包括文件和目录操作、环境变量管理等。
Pathlib库提供了一个面向对象的接口来处理文件系统路径，是Python 3.4+推荐的方式。
"""

import os
from pathlib import Path
import shutil


def organize_files_by_extension(directory):
    """按扩展名组织文件的实用函数"""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"目录不存在: {directory}")
        return

    # 统计各种扩展名
    ext_dict = {}
    for file in dir_path.iterdir():
        if file.is_file():
            ext = file.suffix.lower()
            if ext:
                if ext not in ext_dict:
                    ext_dict[ext] = []
                ext_dict[ext].append(file.name)

    print("文件扩展名统计:")
    for ext, file_list in ext_dict.items():
        print(f"  {ext}: {len(file_list)} 个文件")


def os_basic():
    print("=== OS库基本功能 ===")

    # 获取当前工作目录
    current_dir = os.getcwd()
    print(f"当前工作目录: {current_dir}")

    # 列出目录内容
    files = os.listdir(current_dir)
    print(f"当前目录文件列表: {files[:10]}")  # 只显示前10个

    # 创建新目录
    test_dir = "test_os_directory"
    if not os.path.exists(test_dir):
        os.mkdir(test_dir)
        print(f"创建目录: {test_dir}")

    # 创建多级目录
    nested_dir = os.path.join("parent", "child", "grandchild")
    os.makedirs(nested_dir, exist_ok=True)
    print(f"创建多级目录: {nested_dir}")

    # 路径拼接
    file_path = os.path.join(test_dir, "example.txt")
    print(f"拼接路径: {file_path}")

    # 检查路径是否存在
    exists = os.path.exists(file_path)
    print(f"路径 {file_path} 是否存在: {exists}")

    # 检查是否为文件或目录
    is_file = os.path.isfile(file_path)
    is_dir = os.path.isdir(test_dir)
    print(f"{file_path} 是文件: {is_file}")
    print(f"{test_dir} 是目录: {is_dir}")

    # 获取文件信息
    if os.path.exists(file_path):
        stat_info = os.stat(file_path)
        print(f"文件大小: {stat_info.st_size} 字节")
        print(f"修改时间: {stat_info.st_mtime}")

    # 设置环境变量
    os.environ['MY_VAR'] = 'hello_world'
    print(f"环境变量 MY_VAR: {os.environ.get('MY_VAR')}")

    # 删除测试目录
    shutil.rmtree("parent")
    os.rmdir(test_dir)
    print("清理测试目录完成")


def path_basic():
    print("\n=== Pathlib库基本功能 ===")

    # 创建Path对象
    path_obj = Path("example_folder")
    print(f"Path对象: {path_obj}")

    # 获取当前工作目录
    current_path = Path.cwd()
    print(f"当前工作目录: {current_path}")

    # 获取主目录
    home_path = Path.home()
    print(f"主目录: {home_path}")

    # 路径拼接
    new_path = current_path / "subfolder" / "file.txt"
    print(f"拼接路径: {new_path}")

    # 解析路径组件
    print(f"父目录: {new_path.parent}")
    print(f"文件名: {new_path.name}")
    print(f"文件名(无扩展): {new_path.stem}")
    print(f"扩展名: {new_path.suffix}")

    # 检查路径是否存在
    path_exists = new_path.exists()
    print(f"路径 {new_path} 是否存在: {path_exists}")

    # 检查是否为文件或目录
    is_file_pathlib = new_path.is_file()
    is_dir_pathlib = new_path.is_dir()
    print(f"{new_path} 是文件: {is_file_pathlib}")
    print(f"{new_path} 是目录: {is_dir_pathlib}")

    # 创建目录
    test_path = Path("test_pathlib_directory")
    test_path.mkdir(exist_ok=True)
    print(f"创建目录: {test_path}")

    # 创建嵌套目录
    nested_path = Path("level1/level2/level3")
    nested_path.mkdir(parents=True, exist_ok=True)
    print(f"创建嵌套目录: {nested_path}")

    # 创建文件并写入内容
    file_pathlib = test_path / "sample.txt"
    file_pathlib.write_text("Hello from pathlib!", encoding='utf-8')
    print(f"创建文件: {file_pathlib}")

    # 读取文件内容
    content = file_pathlib.read_text(encoding='utf-8')
    print(f"文件内容: {content}")

    # 遍历目录
    print(f"\n遍历当前目录:")
    for item in Path('.').iterdir():
        if item.is_file():
            print(f"  文件: {item.name}")
        elif item.is_dir():
            print(f"  目录: {item.name}")

    # 查找特定模式的文件
    print(f"\n查找.py文件:")
    py_files = list(Path('.').glob('*.py'))
    for py_file in py_files[:5]:  # 只显示前5个
        print(f"  {py_file.name}")

    # 相对路径转换
    relative_path = new_path.relative_to(current_path)
    print(f"相对于当前目录的路径: {relative_path}")

    # 绝对路径
    absolute_path = Path("relative_path_example").resolve()
    print(f"绝对路径: {absolute_path}")

    # 清理测试目录
    if test_path.exists():
        shutil.rmtree(test_path)
    if nested_path.parent.parent.exists():
        shutil.rmtree("level1")

    print("\n=== OS库与Pathlib库对比 ===")

    print("OS库特点:")
    print("- 函数式接口，使用字符串表示路径")
    print("- 跨平台兼容性好")
    print("- 功能全面，包含大量系统调用")

    print("\nPathlib库特点:")
    print("- 面向对象接口，使用Path对象")
    print("- 更现代，语法更直观")
    print("- 自动处理路径分隔符")
    print("- 提供更多路径操作方法")

    print("\n=== 实际应用示例 ===")

    # 示例使用
    organize_files_by_extension(".")


def main():
    os_basic()

    path_basic()

    print("\n=== 总结 ===")
    print("选择使用哪个库取决于具体场景:")
    print("- 对于简单的路径操作，两个库都可以")
    print("- 对于复杂的路径处理，推荐使用Pathlib")
    print("- 如果需要与旧代码兼容，可能需要使用OS库")
    print("- Pathlib是现代Python推荐的方式")


if __name__ == "__main__":
    main()
