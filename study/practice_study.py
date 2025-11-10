# 简单的装饰器
import functools
import time

from study.decorator_study import log_decorator, timer_decorator
from typing import Generator


@log_decorator
@timer_decorator
def add(a: int, b: int) -> int:
    return a + b


def log_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f'开始调用函数 {func.__name__}')
        result = func(*args, **kwargs)
        print(f'函数 {func.__name__} 调用结束')
        print(f'函数调用结果: {result}')

    return wrapper


def time_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f'函数 {func.__name__} 执行时间: {end_time - start_time:.6f} 秒')
        return result

    return wrapper


def generate_practice():
    even_list = (i for i in range(20) if i != 0 and i & 1 == 0)
    print("偶数：", end=" ")
    for even in even_list:
        print(f"{even}", end=" ")

    even_squares_list = (i ** 2 for i in range(20) if i != 0 and i & 1 == 0)
    print("\n偶数平方：", end=" ")
    for even_square in even_squares_list:
        print(f"{even_square}", end=" ")


def read_large_file() -> Generator[str, None, None]:
    """一个逐行读取文件的生成器"""
    with open("long_txt.txt", 'r', encoding="utf-8") as f:
        for file_line in f:
            # yield将暂停函数执行，并返回当前行的值
            yield file_line.strip()


if __name__ == '__main__':
    # add(1, b=2)

    # generate_practice()
    """
    •数据集太大，无法舒适地放入内存。
    •序列是无限的。
    •计算每个元素的成本很高，而你可能不需要访问所有元素。
    •你想创建一个高效的数据处理管道。
    •你想用更简洁的代码来实现自定义的迭代逻辑。
    
    生成器的核心设计就是为了避免预先知道大小和存储所有内容。
    当你选择使用生成器时，通常意味着你关心的是逐个处理元素，而不是集合的整体属性（如长度）。
    """
    large_file_line = read_large_file()
    for line in large_file_line:
        print(line)
