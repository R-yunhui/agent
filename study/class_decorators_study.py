# Python 类装饰器和内置装饰器学习
"""
类装饰器和内置装饰器学习指南

对于Java开发者的理解：
- 类装饰器类似于Java的类级别注解
- @property 类似于Java的getter/setter模式
- @staticmethod 类似于Java的静态方法
- @classmethod 类似于Java的类方法
"""

import functools
from datetime import datetime
from typing import Any, Dict, List, Optional


# ==================== 1. 类装饰器基础 ====================

def singleton(cls):
    """
    单例模式装饰器 - 确保类只有一个实例

    原理解释：
    - 装饰目标类（比如DatabaseConnection）时，返回一个包装后的"构造器"函数get_instance。
    - 第一次创建类实例时，实例会被保存在instances字典中，下次无论传什么参数，都直接返回第一次创建的实例，实现单例。
    - instances字典以cls为key，保证每个应用singleton的类都各自管理单例。
    - functools.wraps用于保持原类的名称和文档，提高可读性和调试性。
    """
    instances = {}
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


@singleton
class DatabaseConnection:
    """数据库连接类 - 单例模式"""
    
    def __init__(self, host: str = "localhost", port: int = 5432):
        self.host = host
        self.port = port
        self.connected_at = datetime.now()
        print(f"数据库连接已建立: {host}:{port}")

    def __eq__(self, __value):
        return super().__eq__(__value)


def singleton_demo():
    """单例装饰器演示"""
    print("=" * 50)
    print("1. 单例装饰器演示")
    print("=" * 50)

    # 创建多个实例，但实际上是同一个对象
    db1 = DatabaseConnection("localhost", 5432)
    db2 = DatabaseConnection("localhost", 5432)
    db3 = DatabaseConnection("remote-host", 3306)  # 参数不同，但仍然是同一个实例

    # db1 is db2 在Python中类似于Java的== (比较引用/地址)
    # db1 == db2 如果没有实现__eq__，也是比较引用，类似Java的==（而非equals）
    print(f"db1 is db2: {db1 is db2}   # Python is 相当于 Java 的 ==，都是判断引用是否一致")
    print(f"db1 == db2: {db1 == db2}   # 如果没有自定义__eq__，等同于 db1 is db2")
    print(f"db1 is db3: {db1 is db3}")
    print(f"连接时间: {db1.connected_at}")


# ==================== 2. 类装饰器 - 添加方法 ====================

def add_timestamps(cls):

    formatter = "%Y-%m-%d %H:%M:%S"

    """
    为类添加时间戳方法的装饰器
    """
    def created_at(self):
        return f"对象创建于: {datetime.now().strftime(formatter)}"
    
    def updated_at(self):
        return f"对象更新于: {datetime.now().strftime(formatter)}"
    
    # 动态添加方法到类
    cls.created_at = created_at
    cls.updated_at = updated_at
    
    return cls


@add_timestamps
class User:
    """用户类"""
    
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
    
    def __str__(self):
        return f"User({self.name}, {self.email})"


def add_methods_demo():
    """添加方法装饰器演示"""
    print("\n" + "=" * 50)
    print("2. 添加方法装饰器演示")
    print("=" * 50)
    
    user = User("张三", "zhangsan@example.com")
    print(f"用户: {user}")
    print(user.created_at())
    print(user.updated_at())


# ==================== 3. 类装饰器 - 验证和约束 ====================

def validate_fields(**field_validators):
    """
    字段验证装饰器
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            # 调用原始初始化方法
            original_init(self, *args, **kwargs)
            
            # 验证字段
            for field_name, validator in field_validators.items():
                if hasattr(self, field_name):
                    value = getattr(self, field_name)
                    if not validator(value):
                        raise ValueError(f"字段 '{field_name}' 验证失败: {value}")
        
        cls.__init__ = new_init
        return cls
    
    return decorator


def is_positive(value):
    """验证正数"""
    return isinstance(value, (int, float)) and value > 0


def is_email(value):
    """验证邮箱格式"""
    return isinstance(value, str) and "@" in value and "." in value


@validate_fields(
    age=is_positive,
    email=is_email
)
class Employee:
    """员工类 - 带字段验证"""
    
    def __init__(self, name: str, age: int, email: str, salary: float):
        self.name = name
        self.age = age
        self.email = email
        self.salary = salary
    
    def __str__(self):
        return f"Employee({self.name}, {self.age}岁, {self.email}, ¥{self.salary})"


def validation_demo():
    """验证装饰器演示"""
    print("\n" + "=" * 50)
    print("3. 字段验证装饰器演示")
    print("=" * 50)
    
    try:
        # 正确的数据
        emp1 = Employee("李四", 28, "lisi@company.com", 8000.0)
        print(f"员工创建成功: {emp1}")
    except ValueError as e:
        print(f"验证失败: {e}")
    
    try:
        # 错误的年龄
        emp2 = Employee("王五", -5, "wangwu@company.com", 6000.0)
        print(f"员工创建成功: {emp2}")
    except ValueError as e:
        print(f"验证失败: {e}")
    
    try:
        # 错误的邮箱
        emp3 = Employee("赵六", 30, "invalid-email", 7000.0)
        print(f"员工创建成功: {emp3}")
    except ValueError as e:
        print(f"验证失败: {e}")


# ==================== 4. @property 装饰器 ====================

class BankAccount:
    """银行账户类 - 演示 @property 装饰器"""
    
    def __init__(self, initial_balance: float = 0.0):
        self._balance = initial_balance
        self._transaction_history = []
    
    @property
    def balance(self) -> float:
        """余额属性 - 只读"""
        return self._balance
    
    @property
    def formatted_balance(self) -> str:
        """格式化余额 - 只读"""
        return f"¥{self._balance:.2f}"
    
    @property
    def transaction_count(self) -> int:
        """交易次数 - 只读"""
        return len(self._transaction_history)
    
    def deposit(self, amount: float) -> bool:
        """存款"""
        if amount > 0:
            self._balance += amount
            self._transaction_history.append(f"存款: +¥{amount}")
            return True
        return False
    
    def withdraw(self, amount: float) -> bool:
        """取款"""
        if 0 < amount <= self._balance:
            self._balance -= amount
            self._transaction_history.append(f"取款: -¥{amount}")
            return True
        return False
    
    @property
    def transaction_history(self) -> List[str]:
        """交易历史 - 只读"""
        return self._transaction_history.copy()  # 返回副本，防止外部修改


def property_demo():
    """@property 装饰器演示"""
    print("\n" + "=" * 50)
    print("4. @property 装饰器演示")
    print("=" * 50)
    
    account = BankAccount(1000.0)
    
    print(f"初始余额: {account.balance}")
    print(f"格式化余额: {account.formatted_balance}")
    print(f"交易次数: {account.transaction_count}")
    
    # 存款
    account.deposit(500.0)
    print(f"存款后余额: {account.formatted_balance}")
    print(f"交易次数: {account.transaction_count}")
    
    # 取款
    account.withdraw(200.0)
    print(f"取款后余额: {account.formatted_balance}")
    print(f"交易历史: {account.transaction_history}")
    
    # 尝试直接修改余额（会失败，因为是只读属性）
    try:
        account.balance = 9999.0  # 这会失败
    except AttributeError as e:
        print(f"无法直接修改余额: {e}")


# ==================== 5. @staticmethod 装饰器 ====================

class MathUtils:
    """数学工具类 - 演示 @staticmethod"""
    
    @staticmethod
    def add(a: float, b: float) -> float:
        """加法"""
        return a + b
    
    @staticmethod
    def multiply(a: float, b: float) -> float:
        """乘法"""
        return a * b
    
    @staticmethod
    def is_prime(n: int) -> bool:
        """判断是否为质数"""
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    @staticmethod
    def factorial(n: int) -> int:
        """计算阶乘"""
        if n < 0:
            raise ValueError("阶乘不能计算负数")
        if n <= 1:
            return 1
        return n * MathUtils.factorial(n - 1)


def staticmethod_demo():
    """@staticmethod 装饰器演示"""
    print("\n" + "=" * 50)
    print("5. @staticmethod 装饰器演示")
    print("=" * 50)
    
    # 通过类调用静态方法
    print(f"MathUtils.add(5, 3) = {MathUtils.add(5, 3)}")
    print(f"MathUtils.multiply(4, 6) = {MathUtils.multiply(4, 6)}")
    print(f"MathUtils.is_prime(17) = {MathUtils.is_prime(17)}")
    print(f"MathUtils.factorial(5) = {MathUtils.factorial(5)}")
    
    # 通过实例调用静态方法（不推荐，但可以）
    math_utils = MathUtils()
    print(f"math_utils.add(2, 8) = {math_utils.add(2, 8)}")


# ==================== 6. @classmethod 装饰器 ====================

class Person:
    """人类 - 演示 @classmethod"""
    
    population = 0  # 类变量，记录总人口
    
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
        Person.population += 1  # 每创建一个实例，人口+1
    
    @classmethod
    def from_birth_year(cls, name: str, birth_year: int) -> 'Person':
        """从出生年份创建Person实例"""
        current_year = datetime.now().year
        age = current_year - birth_year
        return cls(name, age)
    
    @classmethod
    def get_population(cls) -> int:
        """获取当前人口数"""
        return cls.population
    
    @classmethod
    def create_baby(cls, name: str) -> 'Person':
        """创建婴儿（0岁）"""
        return cls(name, 0)
    
    def __str__(self):
        return f"Person({self.name}, {self.age}岁)"


def classmethod_demo():
    """@classmethod 装饰器演示"""
    print("\n" + "=" * 50)
    print("6. @classmethod 装饰器演示")
    print("=" * 50)
    
    # 普通创建方式
    person1 = Person("张三", 25)
    print(f"普通创建: {person1}")
    
    # 使用类方法从出生年份创建
    person2 = Person.from_birth_year("李四", 1995)
    print(f"从出生年份创建: {person2}")
    
    # 使用类方法创建婴儿
    baby = Person.create_baby("小明")
    print(f"创建婴儿: {baby}")
    
    print(f"当前人口数: {Person.get_population()}")


# ==================== 7. 组合使用装饰器 ====================

class DataProcessor:
    """数据处理器 - 演示装饰器组合使用"""
    
    _instance_count = 0
    
    def __init__(self, name: str):
        self.name = name
        self._data = []
        DataProcessor._instance_count += 1
    
    @classmethod
    def get_instance_count(cls) -> int:
        """获取实例数量"""
        return cls._instance_count
    
    @staticmethod
    def validate_data(data: Any) -> bool:
        """验证数据"""
        return data is not None and data != ""
    
    @property
    def data_count(self) -> int:
        """数据数量"""
        return len(self._data)
    
    @property
    def data(self) -> List[Any]:
        """数据列表（只读）"""
        return self._data.copy()
    
    def add_data(self, item: Any) -> bool:
        """添加数据"""
        if self.validate_data(item):
            self._data.append(item)
            return True
        return False
    
    def process_data(self) -> Dict[str, Any]:
        """处理数据"""
        return {
            "processor": self.name,
            "data_count": self.data_count,
            "data": self.data,
            "processed_at": datetime.now().isoformat()
        }


def combined_decorators_demo():
    """组合装饰器演示"""
    print("\n" + "=" * 50)
    print("7. 组合装饰器演示")
    print("=" * 50)
    
    # 创建处理器
    processor = DataProcessor("主处理器")
    
    # 添加数据
    processor.add_data("数据1")
    processor.add_data("数据2")
    processor.add_data("")  # 无效数据，不会添加
    processor.add_data("数据3")
    
    print(f"处理器: {processor.name}")
    print(f"数据数量: {processor.data_count}")
    print(f"数据列表: {processor.data}")
    
    # 处理数据
    result = processor.process_data()
    print(f"处理结果: {result}")
    
    # 类方法调用
    print(f"实例数量: {DataProcessor.get_instance_count()}")


# ==================== 8. 高级装饰器应用 ====================

def memoize_property(func):
    """
    记忆化属性装饰器 - 缓存计算结果
    """
    @functools.wraps(func)
    def wrapper(self):
        if not hasattr(self, '_memo_cache'):
            self._memo_cache = {}
        
        cache_key = func.__name__
        if cache_key not in self._memo_cache:
            self._memo_cache[cache_key] = func(self)
        
        return self._memo_cache[cache_key]
    
    return property(wrapper)


class ExpensiveCalculator:
    """昂贵计算器 - 演示记忆化属性"""
    
    def __init__(self, n: int):
        self.n = n
    
    @memoize_property
    def fibonacci(self) -> int:
        """计算斐波那契数列（记忆化）"""
        print(f"计算 fibonacci({self.n})...")
        if self.n <= 1:
            return self.n
        
        # 这里使用递归，但由于记忆化，不会重复计算
        calc1 = ExpensiveCalculator(self.n - 1)
        calc2 = ExpensiveCalculator(self.n - 2)
        return calc1.fibonacci + calc2.fibonacci
    
    @memoize_property
    def factorial(self) -> int:
        """计算阶乘（记忆化）"""
        print(f"计算 factorial({self.n})...")
        if self.n <= 1:
            return 1
        return self.n * ExpensiveCalculator(self.n - 1).factorial


def advanced_decorators_demo():
    """高级装饰器演示"""
    print("\n" + "=" * 50)
    print("8. 高级装饰器演示 - 记忆化属性")
    print("=" * 50)
    
    calc = ExpensiveCalculator(10)
    
    print("第一次计算斐波那契数列:")
    result1 = calc.fibonacci
    print(f"结果: {result1}")
    
    print("\n第二次计算斐波那契数列（应该使用缓存）:")
    result2 = calc.fibonacci
    print(f"结果: {result2}")
    
    print("\n计算阶乘:")
    factorial_result = calc.factorial
    print(f"结果: {factorial_result}")


# ==================== 主函数 ====================

if __name__ == "__main__":
    print("Python 类装饰器和内置装饰器学习 - 完整演示")
    print("=" * 70)
    
    # 执行所有演示
    singleton_demo()
    add_methods_demo()
    validation_demo()
    property_demo()
    staticmethod_demo()
    classmethod_demo()
    combined_decorators_demo()
    advanced_decorators_demo()
    
    print("\n" + "=" * 70)
    print("类装饰器和内置装饰器学习完成！")
    print("=" * 70)
    
    print("\n学习要点总结:")
    print("1. 类装饰器可以修改类的行为")
    print("2. @property 用于创建只读属性")
    print("3. @staticmethod 用于创建静态方法")
    print("4. @classmethod 用于创建类方法")
    print("5. 装饰器可以组合使用")
    print("6. 记忆化装饰器可以提高性能")
    print("7. 类装饰器常用于：单例、验证、添加方法等")
