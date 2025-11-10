# Python 生成器和迭代器学习
"""
生成器和迭代器学习指南

对于Java开发者的理解：
- 迭代器类似于Java的Iterator接口
- 生成器类似于Java的Stream API，但更加强大
- yield关键字类似于Java的yield关键字（Java 14+）
- 生成器可以暂停和恢复执行，这是Java没有的特性
"""

import itertools
from typing import Iterator, Generator, List, Any, Optional
from collections.abc import Iterable


# ==================== 1. 迭代器基础 ====================

class NumberIterator:
    """数字迭代器 - 演示迭代器协议"""
    
    def __init__(self, start: int, end: int, step: int = 1):
        self.start = start
        self.end = end
        self.step = step
        self.current = start
    
    def __iter__(self):
        """返回迭代器自身"""
        return self
    
    def __next__(self):
        """返回下一个元素"""
        if self.current >= self.end:
            raise StopIteration
        value = self.current
        self.current += self.step
        return value


def iterator_basic_demo():
    """迭代器基础演示"""
    print("=" * 50)
    print("1. 迭代器基础演示")
    print("=" * 50)
    
    # 使用自定义迭代器
    numbers = NumberIterator(1, 6, 2)  # 1, 3, 5
    
    print("使用for循环:")
    for num in numbers:
        print(f"数字: {num}")
    
    # 手动使用迭代器
    print("\n手动使用迭代器:")
    numbers2 = NumberIterator(10, 15)
    try:
        while True:
            print(f"数字: {next(numbers2)}")
    except StopIteration:
        print("迭代结束")
    
    # 使用内置迭代器
    print("\n使用内置迭代器:")
    for i, char in enumerate("Hello"):
        print(f"位置 {i}: {char}")


# ==================== 2. 生成器函数 ====================

def fibonacci_generator(n: int) -> Generator[int, None, None]:
    """
    斐波那契数列生成器

    yield的作用：  
    - yield 用于定义生成器函数，每次迭代遇到yield就暂停，返回一个值，下次迭代从yield之后继续。  
    - 和return不同，yield不会结束函数，而是让函数可以多次返回（生成）值，适用于逐步产生序列的场景。

    下面用yield生成斐波那契数列的前n项，每次调用next()时返回下一个斐波那契数。
    """
    a, b = 0, 1
    count = 0
    while count < n:
        yield a  # 每次暂停并返回当前a，等next()再恢复执行
        a, b = b, a + b
        count += 1


def countdown_generator(start: int) -> Generator[int | str | Any, None, None]:
    """倒计时生成器"""
    while start > 0:
        yield start
        start -= 1
    yield "发射!"


def file_reader_generator(filename: str) -> Generator[str, None, None]:
    """文件读取生成器"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                yield line.strip()
    except FileNotFoundError:
        yield f"文件 {filename} 不存在"


def generator_function_demo():
    """生成器函数演示"""
    print("\n" + "=" * 50)
    print("2. 生成器函数演示")
    print("=" * 50)
    
    # 斐波那契数列
    print("斐波那契数列:")
    fib_gen = fibonacci_generator(10)
    for num in fib_gen:
        print(f"斐波那契: {num}")
    
    # 倒计时
    print("\n倒计时:")
    countdown_gen = countdown_generator(5)
    for item in countdown_gen:
        print(f"倒计时: {item}")
    
    # 文件读取
    print("\n文件读取:")
    file_gen = file_reader_generator("test.txt")
    for line in file_gen:
        print(f"文件行: {line}")


# ==================== 3. 生成器表达式 ====================

def generator_expression_demo():
    """生成器表达式演示"""
    print("\n" + "=" * 50)
    print("3. 生成器表达式演示")
    print("=" * 50)
    
    # 基本生成器表达式
    squares = (x**2 for x in range(10))
    print("平方数:")
    for square in squares:
        print(f"平方: {square}")
    
    # 条件过滤
    even_squares = (x**2 for x in range(20) if x % 2 == 0)
    print("\n偶数平方数:")
    for square in even_squares:
        print(f"偶数平方: {square}")
    
    # 字符串处理
    words = ["hello", "world", "python", "generator"]
    upper_words = (word.upper() for word in words if len(word) > 4)
    print("\n长单词转大写:")
    for word in upper_words:
        print(f"单词: {word}")


# ==================== 4. 生成器的高级用法 ====================

def data_processor_generator(data: List[Any]) -> Generator[dict, None, None]:
    """数据处理生成器 - 演示复杂生成器"""
    for i, item in enumerate(data):
        # 模拟数据处理
        processed_item = {
            "index": i,
            "original": item,
            "processed": str(item).upper() if isinstance(item, str) else item * 2,
            "timestamp": f"processed_at_{i}"
        }
        yield processed_item


def batch_processor_generator(data: List[Any], batch_size: int = 3) -> Generator[List[Any], None, None]:
    """批处理生成器"""
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        yield batch


def pipeline_generator():
    """管道生成器 - 演示生成器链"""
    # 数据源
    raw_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    # 第一步：过滤偶数
    filtered_data = (x for x in raw_data if x % 2 == 0)
    
    # 第二步：平方
    squared_data = (x**2 for x in filtered_data)
    
    # 第三步：转换为字符串
    string_data = (f"结果: {x}" for x in squared_data)
    
    return string_data


def advanced_generator_demo():
    """高级生成器演示"""
    print("\n" + "=" * 50)
    print("4. 高级生成器演示")
    print("=" * 50)
    
    # 数据处理生成器
    data = ["apple", "banana", "cherry", "date"]
    processor = data_processor_generator(data)
    print("数据处理:")
    for result in processor:
        print(f"处理结果: {result}")
    
    # 批处理生成器
    large_data = list(range(1, 11))
    batch_processor = batch_processor_generator(large_data, 3)
    print("\n批处理:")
    for batch in batch_processor:
        print(f"批次: {batch}")
    
    # 管道生成器
    pipeline = pipeline_generator()
    print("\n管道处理:")
    for result in pipeline:
        print(result)


# ==================== 5. 生成器的方法 ====================

def generator_methods_demo():
    """生成器方法演示"""
    print("\n" + "=" * 50)
    print("5. 生成器方法演示")
    print("=" * 50)
    
    def number_generator():
        """数字生成器 - 演示send和throw方法"""
        try:
            while True:
                received = yield
                if received is not None:
                    print(f"收到值: {received}")
                yield received
        except GeneratorExit:
            print("生成器被关闭")
        except Exception as e:
            print(f"生成器异常: {e}")
    
    # 创建生成器
    gen = number_generator()
    next(gen)  # 启动生成器
    
    # 使用send方法
    print("使用send方法:")
    gen.send(42)
    next(gen)
    
    gen.send(100)
    next(gen)
    
    # 使用throw方法
    print("\n使用throw方法:")
    try:
        gen.throw(ValueError, "测试异常")
    except ValueError as e:
        print(f"捕获异常: {e}")
    
    # 关闭生成器
    gen.close()


# ==================== 6. itertools模块 ====================

def itertools_demo():
    """itertools模块演示"""
    print("\n" + "=" * 50)
    print("6. itertools模块演示")
    print("=" * 50)
    
    # 无限迭代器
    print("无限迭代器:")
    counter = itertools.count(1, 2)  # 从1开始，步长为2
    for i, num in enumerate(counter):
        if i >= 5:
            break
        print(f"计数: {num}")
    
    # 循环迭代器
    print("\n循环迭代器:")
    cycle_iter = itertools.cycle(['A', 'B', 'C'])
    for i, item in enumerate(cycle_iter):
        if i >= 8:
            break
        print(f"循环: {item}")
    
    # 重复迭代器
    print("\n重复迭代器:")
    repeat_iter = itertools.repeat('Hello', 3)
    for item in repeat_iter:
        print(f"重复: {item}")
    
    # 组合和排列
    print("\n组合和排列:")
    data = [1, 2, 3]
    
    # 排列
    permutations = itertools.permutations(data, 2)
    print("排列:")
    for perm in permutations:
        print(f"排列: {perm}")
    
    # 组合
    combinations = itertools.combinations(data, 2)
    print("\n组合:")
    for comb in combinations:
        print(f"组合: {comb}")
    
    # 分组
    print("\n分组:")
    data_with_key = [(1, 'A'), (1, 'B'), (2, 'C'), (2, 'D'), (3, 'E')]
    grouped = itertools.groupby(data_with_key, key=lambda x: x[0])
    for key, group in grouped:
        print(f"键 {key}: {list(group)}")


# ==================== 7. 协程基础 ====================

def simple_coroutine():
    """简单协程 - 演示协程基础"""
    print("协程启动")
    while True:
        value = yield
        print(f"协程收到: {value}")


def accumulator_coroutine():
    """累加器协程"""
    total = 0
    while True:
        value = yield total
        if value is not None:
            total += value


def coroutine_demo():
    """协程演示"""
    print("\n" + "=" * 50)
    print("7. 协程基础演示")
    print("=" * 50)
    
    # 简单协程
    print("简单协程:")
    coro = simple_coroutine()
    next(coro)  # 启动协程
    coro.send("Hello")
    coro.send("World")
    coro.close()
    
    # 累加器协程
    print("\n累加器协程:")
    acc = accumulator_coroutine()
    next(acc)  # 启动协程
    print(f"初始值: {acc.send(10)}")
    print(f"累加后: {acc.send(20)}")
    print(f"累加后: {acc.send(30)}")
    acc.close()


# ==================== 8. 实际应用场景 ====================

def csv_reader_generator(filename: str) -> Generator[List[str], None, None]:
    """CSV文件读取生成器"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                yield line.strip().split(',')
    except FileNotFoundError:
        print(f"文件 {filename} 不存在")


def log_analyzer_generator(log_file: str, keyword: str) -> Generator[str, None, None]:
    """日志分析生成器"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if keyword in line:
                    yield f"行 {line_num}: {line.strip()}"
    except FileNotFoundError:
        yield f"日志文件 {log_file} 不存在"


def data_stream_processor():
    """数据流处理器 - 实际应用场景"""
    print("\n" + "=" * 50)
    print("8. 实际应用场景演示")
    print("=" * 50)
    
    # 模拟CSV数据
    csv_data = [
        "name,age,city",
        "张三,25,北京",
        "李四,30,上海",
        "王五,28,广州"
    ]
    
    # 写入测试文件
    with open("test_data.csv", "w", encoding="utf-8") as f:
        for line in csv_data:
            f.write(line + "\n")
    
    # 读取CSV文件
    print("CSV文件读取:")
    csv_reader = csv_reader_generator("test_data.csv")
    for row in csv_reader:
        print(f"CSV行: {row}")
    
    # 日志分析
    print("\n日志分析:")
    log_data = [
        "2023-01-01 INFO: 系统启动",
        "2023-01-01 ERROR: 数据库连接失败",
        "2023-01-01 INFO: 用户登录",
        "2023-01-01 ERROR: 文件读取失败"
    ]
    
    # 写入测试日志
    with open("app.log", "w", encoding="utf-8") as f:
        for line in log_data:
            f.write(line + "\n")
    
    log_analyzer = log_analyzer_generator("app.log", "ERROR")
    for error_line in log_analyzer:
        print(f"错误日志: {error_line}")


# ==================== 主函数 ====================

if __name__ == "__main__":
    print("Python 生成器和迭代器学习 - 完整演示")
    print("=" * 70)
    
    # 执行所有演示
    iterator_basic_demo()
    generator_function_demo()
    generator_expression_demo()
    advanced_generator_demo()
    generator_methods_demo()
    itertools_demo()
    coroutine_demo()
    data_stream_processor()
    
    print("\n" + "=" * 70)
    print("生成器和迭代器学习完成！")
    print("=" * 70)
    
    print("\n学习要点总结:")
    print("1. 迭代器协议：实现__iter__和__next__方法")
    print("2. 生成器函数：使用yield关键字")
    print("3. 生成器表达式：类似列表推导式，但返回生成器")
    print("4. 生成器方法：send、throw、close")
    print("5. itertools模块：提供强大的迭代工具")
    print("6. 协程：可以暂停和恢复的函数")
    print("7. 内存效率：生成器节省内存，适合大数据处理")
    print("8. 实际应用：文件处理、数据流、日志分析等")
