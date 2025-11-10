# Python 魔法方法学习
"""
魔法方法 (Magic Methods) 学习指南

对于Java开发者的理解：
- 魔法方法类似于Java的特殊方法，如toString(), equals(), hashCode()
- 通过魔法方法可以让自定义类支持内置操作符和函数
- Python的魔法方法更加灵活和强大，可以完全自定义对象行为
- 魔法方法以双下划线开头和结尾，如 __init__, __str__ 等
"""

from typing import Any, Union, Iterator
from datetime import datetime
import math


# ==================== 1. 基础魔法方法 ====================

class Person:
    """人类 - 演示基础魔法方法"""
    
    def __init__(self, name: str, age: int, email: str = None):
        """
        构造方法 - 类似Java的构造函数
        在创建对象时自动调用
        """
        self.name = name
        self.age = age
        self.email = email
        self.created_at = datetime.now()
    
    def __str__(self) -> str:
        """
        字符串表示 - 类似Java的toString()
        用于print()和str()函数
        应该返回用户友好的字符串
        """
        return f"Person(name='{self.name}', age={self.age})"
    
    def __repr__(self) -> str:
        """
        开发者表示 - 用于调试
        应该返回能重新创建对象的字符串
        如果没有定义__str__，print()会使用__repr__
        """
        return f"Person('{self.name}', {self.age}, '{self.email}')"
    
    def __eq__(self, other) -> bool:
        """
        相等比较 - 类似Java的equals()
        定义 == 操作符的行为
        """
        if not isinstance(other, Person):
            return False
        return self.name == other.name and self.age == other.age
    
    def __hash__(self) -> int:
        """
        哈希值 - 类似Java的hashCode()
        如果对象要用作字典键或集合元素，需要定义此方法
        """
        return hash((self.name, self.age))
    
    def __lt__(self, other) -> bool:
        """
        小于比较 - 定义 < 操作符
        """
        if not isinstance(other, Person):
            return NotImplemented
        return self.age < other.age
    
    def __le__(self, other) -> bool:
        """小于等于比较 - 定义 <= 操作符"""
        return self < other or self == other
    
    def __gt__(self, other) -> bool:
        """大于比较 - 定义 > 操作符"""
        if not isinstance(other, Person):
            return NotImplemented
        return self.age > other.age
    
    def __ge__(self, other) -> bool:
        """大于等于比较 - 定义 >= 操作符"""
        return self > other or self == other


def basic_magic_methods_demo():
    """基础魔法方法演示"""
    print("=" * 50)
    print("1. 基础魔法方法演示")
    print("=" * 50)
    
    # 创建对象
    person1 = Person("张三", 25, "zhangsan@example.com")
    person2 = Person("李四", 30, "lisi@example.com")
    person3 = Person("张三", 25, "zhangsan@company.com")  # 与person1相等
    
    # __str__ 和 __repr__
    print(f"str(person1): {str(person1)}")
    print(f"repr(person1): {repr(person1)}")
    print(f"print(person1): {person1}")  # 使用__str__
    
    # __eq__ 相等比较
    print(f"\nperson1 == person2: {person1 == person2}")
    print(f"person1 == person3: {person1 == person3}")  # True，因为姓名和年龄相同
    
    # __hash__ 哈希值
    print(f"\nhash(person1): {hash(person1)}")
    print(f"hash(person3): {hash(person3)}")  # 应该相同
    
    # 比较操作符
    print(f"\nperson1 < person2: {person1 < person2}")  # 25 < 30
    print(f"person1 > person2: {person1 > person2}")   # 25 > 30
    print(f"person1 <= person3: {person1 <= person3}") # 相等，所以<=为True
    
    # 用作字典键和集合元素
    people_dict = {person1: "员工1", person2: "员工2"}
    people_set = {person1, person2, person3}  # person3与person1相等，集合中只有2个元素
    
    print(f"\n字典: {people_dict}")
    print(f"集合大小: {len(people_set)}")  # 应该是2


# ==================== 2. 容器类型魔法方法 ====================

class CustomList:
    """自定义列表 - 演示容器类型魔法方法"""
    
    def __init__(self, items=None):
        """初始化列表"""
        self._items = list(items) if items else []
    
    def __len__(self) -> int:
        """
        长度 - 定义len()函数的行为
        类似Java的size()方法
        """
        return len(self._items)
    
    def __getitem__(self, index: int) -> Any:
        """
        获取元素 - 定义[]操作符的读取行为
        类似Java的get(index)方法
        """
        return self._items[index]
    
    def __setitem__(self, index: int, value: Any) -> None:
        """
        设置元素 - 定义[]操作符的赋值行为
        类似Java的set(index, value)方法
        """
        self._items[index] = value
    
    def __delitem__(self, index: int) -> None:
        """
        删除元素 - 定义del操作符的行为
        """
        del self._items[index]
    
    def __contains__(self, item: Any) -> bool:
        """
        包含检查 - 定义in操作符的行为
        类似Java的contains()方法
        """
        return item in self._items
    
    def __iter__(self) -> Iterator:
        """
        迭代器 - 定义for循环的行为
        类似Java的iterator()方法
        """
        return iter(self._items)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"CustomList({self._items})"
    
    def __repr__(self) -> str:
        """开发者表示"""
        return f"CustomList({self._items!r})"
    
    def append(self, item: Any) -> None:
        """添加元素"""
        self._items.append(item)
    
    def extend(self, items) -> None:
        """扩展列表"""
        self._items.extend(items)


def container_magic_methods_demo():
    """容器类型魔法方法演示"""
    print("\n" + "=" * 50)
    print("2. 容器类型魔法方法演示")
    print("=" * 50)
    
    # 创建自定义列表
    my_list = CustomList([1, 2, 3, 4, 5])
    
    # __len__ - 长度
    print(f"len(my_list): {len(my_list)}")
    
    # __getitem__ - 获取元素
    print(f"my_list[0]: {my_list[0]}")
    print(f"my_list[2]: {my_list[2]}")
    
    # __setitem__ - 设置元素
    my_list[1] = 20
    print(f"修改后 my_list[1]: {my_list[1]}")
    
    # __contains__ - 包含检查
    print(f"3 in my_list: {3 in my_list}")
    print(f"10 in my_list: {10 in my_list}")
    
    # __iter__ - 迭代
    print("遍历列表:")
    for item in my_list:
        print(f"  项目: {item}")
    
    # __delitem__ - 删除元素
    print(f"删除前: {my_list}")
    del my_list[0]
    print(f"删除后: {my_list}")
    
    # 添加元素
    my_list.append(100)
    my_list.extend([200, 300])
    print(f"添加元素后: {my_list}")


# ==================== 3. 数值运算魔法方法 ====================

class Vector2D:
    """二维向量 - 演示数值运算魔法方法"""
    
    def __init__(self, x: float, y: float):
        """初始化向量"""
        self.x = x
        self.y = y
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Vector2D({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        """开发者表示"""
        return f"Vector2D({self.x!r}, {self.y!r})"
    
    def __add__(self, other) -> 'Vector2D':
        """
        加法 - 定义+操作符
        类似Java中重载+操作符（Java不支持，但概念类似）
        """
        if isinstance(other, Vector2D):
            return Vector2D(self.x + other.x, self.y + other.y)
        elif isinstance(other, (int, float)):
            return Vector2D(self.x + other, self.y + other)
        return NotImplemented
    
    def __sub__(self, other) -> 'Vector2D':
        """减法 - 定义-操作符"""
        if isinstance(other, Vector2D):
            return Vector2D(self.x - other.x, self.y - other.y)
        elif isinstance(other, (int, float)):
            return Vector2D(self.x - other, self.y - other)
        return NotImplemented
    
    def __mul__(self, other) -> Union['Vector2D', float]:
        """乘法 - 定义*操作符"""
        if isinstance(other, Vector2D):
            # 点积
            return self.x * other.x + self.y * other.y
        elif isinstance(other, (int, float)):
            # 标量乘法
            return Vector2D(self.x * other, self.y * other)
        return NotImplemented
    
    def __truediv__(self, other) -> 'Vector2D':
        """除法 - 定义/操作符"""
        if isinstance(other, (int, float)):
            if other == 0:
                raise ZeroDivisionError("不能除以零")
            return Vector2D(self.x / other, self.y / other)
        return NotImplemented
    
    def __neg__(self) -> 'Vector2D':
        """负号 - 定义-操作符（一元）"""
        return Vector2D(-self.x, -self.y)
    
    def __abs__(self) -> float:
        """绝对值 - 定义abs()函数的行为"""
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def __eq__(self, other) -> bool:
        """相等比较"""
        if not isinstance(other, Vector2D):
            return False
        return self.x == other.x and self.y == other.y
    
    def __iadd__(self, other) -> 'Vector2D':
        """
        就地加法 - 定义+=操作符
        修改自身并返回
        """
        if isinstance(other, Vector2D):
            self.x += other.x
            self.y += other.y
        elif isinstance(other, (int, float)):
            self.x += other
            self.y += other
        else:
            return NotImplemented
        return self
    
    def magnitude(self) -> float:
        """向量长度"""
        return abs(self)


def numeric_magic_methods_demo():
    """数值运算魔法方法演示"""
    print("\n" + "=" * 50)
    print("3. 数值运算魔法方法演示")
    print("=" * 50)
    
    # 创建向量
    v1 = Vector2D(3, 4)
    v2 = Vector2D(1, 2)
    
    print(f"v1: {v1}")
    print(f"v2: {v2}")
    
    # __add__ - 加法
    v3 = v1 + v2
    print(f"v1 + v2: {v3}")
    
    # 与标量相加
    v4 = v1 + 5
    print(f"v1 + 5: {v4}")
    
    # __sub__ - 减法
    v5 = v1 - v2
    print(f"v1 - v2: {v5}")
    
    # __mul__ - 乘法
    dot_product = v1 * v2  # 点积
    print(f"v1 * v2 (点积): {dot_product}")
    
    v6 = v1 * 2  # 标量乘法
    print(f"v1 * 2: {v6}")
    
    # __truediv__ - 除法
    v7 = v1 / 2
    print(f"v1 / 2: {v7}")
    
    # __neg__ - 负号
    v8 = -v1
    print(f"-v1: {v8}")
    
    # __abs__ - 绝对值（向量长度）
    print(f"abs(v1): {abs(v1)}")
    print(f"v1.magnitude(): {v1.magnitude()}")
    
    # __iadd__ - 就地加法
    v9 = Vector2D(1, 1)
    print(f"v9 初始: {v9}")
    v9 += Vector2D(2, 3)
    print(f"v9 += Vector2D(2, 3): {v9}")


# ==================== 4. 属性访问魔法方法 ====================

class DynamicAttributes:
    """动态属性 - 演示属性访问魔法方法"""
    
    def __init__(self):
        """初始化"""
        self._data = {}
        self._access_log = []
    
    def __getattr__(self, name: str) -> Any:
        """
        获取不存在的属性时调用
        只有在正常属性查找失败时才会调用
        """
        self._access_log.append(f"GET: {name}")
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{type(self).__name__}' 对象没有属性 '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """
        设置属性时调用
        会拦截所有属性设置操作
        """
        if name.startswith('_'):
            # 私有属性直接设置
            super().__setattr__(name, value)
        else:
            # 公共属性存储在_data中
            if not hasattr(self, '_data'):
                super().__setattr__('_data', {})
            if not hasattr(self, '_access_log'):
                super().__setattr__('_access_log', [])
            
            self._access_log.append(f"SET: {name} = {value}")
            self._data[name] = value
    
    def __delattr__(self, name: str) -> None:
        """
        删除属性时调用
        """
        self._access_log.append(f"DEL: {name}")
        if name in self._data:
            del self._data[name]
        else:
            raise AttributeError(f"'{type(self).__name__}' 对象没有属性 '{name}'")
    
    def __getattribute__(self, name: str) -> Any:
        """
        获取任何属性时都会调用
        需要小心使用，避免无限递归
        """
        if name == 'special_method_called':
            return "通过__getattribute__访问"
        return super().__getattribute__(name)
    
    def get_access_log(self) -> list:
        """获取访问日志"""
        return self._access_log.copy()
    
    def get_data(self) -> dict:
        """获取存储的数据"""
        return self._data.copy()


def attribute_access_demo():
    """属性访问魔法方法演示"""
    print("\n" + "=" * 50)
    print("4. 属性访问魔法方法演示")
    print("=" * 50)
    
    obj = DynamicAttributes()
    
    # __setattr__ - 设置属性
    obj.name = "张三"
    obj.age = 25
    obj.city = "北京"
    
    print("设置属性后的数据:")
    print(f"数据: {obj.get_data()}")
    print(f"访问日志: {obj.get_access_log()}")
    
    # __getattr__ - 获取属性
    print(f"\n获取属性:")
    print(f"obj.name: {obj.name}")
    print(f"obj.age: {obj.age}")
    
    # __getattribute__ - 特殊属性
    print(f"obj.special_method_called: {obj.special_method_called}")
    
    # 尝试获取不存在的属性
    try:
        print(f"obj.nonexistent: {obj.nonexistent}")
    except AttributeError as e:
        print(f"属性错误: {e}")
    
    # __delattr__ - 删除属性
    del obj.city
    print(f"\n删除属性后的数据: {obj.get_data()}")
    
    print(f"最终访问日志: {obj.get_access_log()}")


# ==================== 5. 调用魔法方法 ====================

class Calculator:
    """计算器 - 演示调用魔法方法"""
    
    def __init__(self, name: str):
        """初始化计算器"""
        self.name = name
        self.history = []
    
    def __call__(self, operation: str, a: float, b: float = None) -> float:
        """
        使对象可调用 - 定义()操作符
        类似Java的函数式接口
        """
        result = None
        
        if operation == "add" and b is not None:
            result = a + b
        elif operation == "subtract" and b is not None:
            result = a - b
        elif operation == "multiply" and b is not None:
            result = a * b
        elif operation == "divide" and b is not None:
            if b == 0:
                raise ZeroDivisionError("不能除以零")
            result = a / b
        elif operation == "square":
            result = a ** 2
        elif operation == "sqrt":
            if a < 0:
                raise ValueError("不能计算负数的平方根")
            result = math.sqrt(a)
        else:
            raise ValueError(f"不支持的操作: {operation}")
        
        # 记录历史
        operation_str = f"{operation}({a}, {b})" if b is not None else f"{operation}({a})"
        self.history.append(f"{operation_str} = {result}")
        
        return result
    
    def get_history(self) -> list:
        """获取计算历史"""
        return self.history.copy()
    
    def clear_history(self) -> None:
        """清空历史"""
        self.history.clear()


class Counter:
    """计数器 - 另一个调用示例"""
    
    def __init__(self, start: int = 0, step: int = 1):
        """初始化计数器"""
        self.value = start
        self.step = step
    
    def __call__(self) -> int:
        """每次调用时递增并返回当前值"""
        current = self.value
        self.value += self.step
        return current
    
    def reset(self, start: int = 0) -> None:
        """重置计数器"""
        self.value = start


def callable_magic_method_demo():
    """调用魔法方法演示"""
    print("\n" + "=" * 50)
    print("5. 调用魔法方法演示")
    print("=" * 50)
    
    # 计算器示例
    calc = Calculator("我的计算器")
    
    print("计算器演示:")
    print(f"加法: {calc('add', 10, 5)}")
    print(f"减法: {calc('subtract', 10, 3)}")
    print(f"乘法: {calc('multiply', 4, 6)}")
    print(f"除法: {calc('divide', 15, 3)}")
    print(f"平方: {calc('square', 7)}")
    print(f"开方: {calc('sqrt', 16)}")
    
    print(f"\n计算历史:")
    for record in calc.get_history():
        print(f"  {record}")
    
    # 计数器示例
    print(f"\n计数器演示:")
    counter = Counter(0, 2)  # 从0开始，步长为2
    
    print("连续调用计数器:")
    for i in range(5):
        print(f"  调用 {i+1}: {counter()}")
    
    # 重置计数器
    counter.reset(100)
    print(f"重置后调用: {counter()}")


# ==================== 6. 上下文管理器魔法方法 ====================

class FileProcessor:
    """文件处理器 - 演示上下文管理器魔法方法"""
    
    def __init__(self, filename: str, mode: str = 'r'):
        """初始化文件处理器"""
        self.filename = filename
        self.mode = mode
        self.file = None
        self.start_time = None
    
    def __enter__(self):
        """
        进入上下文时调用
        类似Java的try-with-resources
        """
        print(f"打开文件: {self.filename}")
        self.start_time = datetime.now()
        self.file = open(self.filename, self.mode, encoding='utf-8')
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文时调用
        exc_type: 异常类型
        exc_val: 异常值
        exc_tb: 异常追踪
        """
        if self.file:
            self.file.close()
            print(f"关闭文件: {self.filename}")
        
        if self.start_time:
            duration = datetime.now() - self.start_time
            print(f"文件操作耗时: {duration.total_seconds():.4f} 秒")
        
        if exc_type:
            print(f"文件操作发生异常: {exc_type.__name__}: {exc_val}")
            # 返回False表示不抑制异常，异常会继续传播
            return False
        
        print("文件操作成功完成")
        return False


def context_manager_demo():
    """上下文管理器魔法方法演示"""
    print("\n" + "=" * 50)
    print("6. 上下文管理器魔法方法演示")
    print("=" * 50)
    
    # 正常文件操作
    try:
        with FileProcessor("test_output.txt", "w") as f:
            f.write("Hello, World!\n")
            f.write("这是测试内容。\n")
            print("文件写入成功")
    except Exception as e:
        print(f"文件操作失败: {e}")
    
    # 读取文件
    try:
        with FileProcessor("test_output.txt", "r") as f:
            content = f.read()
            print(f"文件内容:\n{content}")
    except Exception as e:
        print(f"文件读取失败: {e}")


# ==================== 7. 实际应用场景 ====================

class SmartDict:
    """智能字典 - 综合应用多种魔法方法"""
    
    def __init__(self, **kwargs):
        """初始化智能字典"""
        self._data = {}
        self._access_count = {}
        for key, value in kwargs.items():
            self[key] = value
    
    def __getitem__(self, key: str) -> Any:
        """获取项目"""
        if key not in self._data:
            raise KeyError(f"键 '{key}' 不存在")
        
        # 记录访问次数
        self._access_count[key] = self._access_count.get(key, 0) + 1
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """设置项目"""
        self._data[key] = value
        if key not in self._access_count:
            self._access_count[key] = 0
    
    def __delitem__(self, key: str) -> None:
        """删除项目"""
        if key not in self._data:
            raise KeyError(f"键 '{key}' 不存在")
        del self._data[key]
        del self._access_count[key]
    
    def __contains__(self, key: str) -> bool:
        """检查是否包含键"""
        return key in self._data
    
    def __len__(self) -> int:
        """获取长度"""
        return len(self._data)
    
    def __iter__(self):
        """迭代键"""
        return iter(self._data)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"SmartDict({dict(self._data)})"
    
    def __repr__(self) -> str:
        """开发者表示"""
        return f"SmartDict({self._data!r})"
    
    def __eq__(self, other) -> bool:
        """相等比较"""
        if isinstance(other, SmartDict):
            return self._data == other._data
        elif isinstance(other, dict):
            return self._data == other
        return False
    
    def __add__(self, other) -> 'SmartDict':
        """合并字典"""
        if isinstance(other, (SmartDict, dict)):
            result = SmartDict(**self._data)
            for key, value in (other._data if isinstance(other, SmartDict) else other).items():
                result[key] = value
            return result
        return NotImplemented
    
    def get_access_count(self, key: str) -> int:
        """获取键的访问次数"""
        return self._access_count.get(key, 0)
    
    def get_most_accessed(self) -> tuple:
        """获取访问次数最多的键"""
        if not self._access_count:
            return None, 0
        key = max(self._access_count, key=self._access_count.get)
        return key, self._access_count[key]
    
    def keys(self):
        """获取所有键"""
        return self._data.keys()
    
    def values(self):
        """获取所有值"""
        return self._data.values()
    
    def items(self):
        """获取所有键值对"""
        return self._data.items()


def practical_application_demo():
    """实际应用场景演示"""
    print("\n" + "=" * 50)
    print("7. 实际应用场景演示 - 智能字典")
    print("=" * 50)
    
    # 创建智能字典
    smart_dict = SmartDict(name="张三", age=25, city="北京")
    
    print(f"初始字典: {smart_dict}")
    print(f"长度: {len(smart_dict)}")
    
    # 访问元素
    print(f"\n访问元素:")
    print(f"smart_dict['name']: {smart_dict['name']}")
    print(f"smart_dict['age']: {smart_dict['age']}")
    print(f"smart_dict['name']: {smart_dict['name']}")  # 再次访问
    print(f"smart_dict['age']: {smart_dict['age']}")   # 再次访问
    print(f"smart_dict['age']: {smart_dict['age']}")   # 第三次访问
    
    # 检查访问次数
    print(f"\n访问次数统计:")
    for key in smart_dict.keys():
        count = smart_dict.get_access_count(key)
        print(f"  {key}: {count} 次")
    
    most_key, most_count = smart_dict.get_most_accessed()
    print(f"访问最多的键: {most_key} ({most_count} 次)")
    
    # 添加和删除元素
    smart_dict['email'] = 'zhangsan@example.com'
    print(f"\n添加元素后: {smart_dict}")
    
    # 检查包含
    print(f"'email' in smart_dict: {'email' in smart_dict}")
    print(f"'phone' in smart_dict: {'phone' in smart_dict}")
    
    # 字典合并
    other_dict = {'phone': '123456789', 'department': 'IT'}
    merged = smart_dict + other_dict
    print(f"\n合并后的字典: {merged}")
    
    # 迭代
    print(f"\n迭代字典:")
    for key in smart_dict:
        print(f"  {key}: {smart_dict[key]}")


# ==================== 主函数 ====================

if __name__ == "__main__":
    print("Python 魔法方法学习 - 完整演示")
    print("=" * 70)
    
    # 执行所有演示
    basic_magic_methods_demo()
    container_magic_methods_demo()
    numeric_magic_methods_demo()
    attribute_access_demo()
    callable_magic_method_demo()
    context_manager_demo()
    practical_application_demo()
    
    print("\n" + "=" * 70)
    print("魔法方法学习完成！")
    print("=" * 70)
    
    print("\n学习要点总结:")
    print("1. 基础魔法方法：__init__, __str__, __repr__, __eq__, __hash__")
    print("2. 容器魔法方法：__len__, __getitem__, __setitem__, __contains__")
    print("3. 数值运算魔法方法：__add__, __sub__, __mul__, __truediv__")
    print("4. 属性访问魔法方法：__getattr__, __setattr__, __delattr__")
    print("5. 调用魔法方法：__call__ 使对象可调用")
    print("6. 上下文管理器：__enter__, __exit__ 支持with语句")
    print("7. 魔法方法让自定义类具有内置类型的行为")
    print("8. 合理使用魔法方法可以让代码更加Pythonic")
