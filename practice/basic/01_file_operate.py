"""
文件操作相关练习
"""
from pathlib import Path


def copy_file(source_file_dir: str, target_file_dir: str) -> int | None:
    """
    复制文件
    :param source_file_dir: 源文件路径
    :param target_file_dir: 目标文件路径
    :return: 复制文件数量
    """
    if not source_file_dir or not target_file_dir:
        print("源文件路径或目标文件路径不能为空！")

    source_file_path = Path(source_file_dir)
    target_file_path = Path(target_file_dir)
    if not Path.is_dir(source_file_path):
        print("源文件路径不存在！")
        return None

    if not Path.exists(target_file_path):
        print("目标文件路径不存在！创建新的")
        Path.mkdir(target_file_path, exist_ok=True)

    return None


def main():
    copy_file("", "")


if __name__ == "__main__":
    main()
