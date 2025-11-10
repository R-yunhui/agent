# Python 装饰器学习 - 从基础到进阶
"""
装饰器 (Decorator) 学习指南

对于Java开发者的理解：
- 类似于Java的注解 (@Override, @Deprecated等)，但功能更强大
- 可以在不修改原函数代码的情况下，增加额外功能
- 本质上是一个高阶函数，接受函数作为参数，返回新的函数
"""

import functools
import time
from datetime import datetime


# ==================== 1. 装饰器基础概念 ====================

def my_decorator(func):
    """
    最简单的装饰器示例
    """
    def wrapper():
        print("在函数执行前做些什么")
        func()  # 调用原函数
        print("在函数执行后做些什么")
    return wrapper


# 使用装饰器的两种方式：

# 方式1：使用 @ 语法糖（推荐）
@my_decorator
def say_hello():
    print("Hello, World!")


# 方式2：手动调用装饰器
def say_goodbye():
    print("Goodbye!")

say_goodbye = my_decorator(say_goodbye)


def decorator_basic_demo():
    """装饰器基础演示"""
    print("=" * 50)
    print("1. 装饰器基础演示")
    print("=" * 50)
    
    print("\n调用被装饰的函数:")
    say_hello()
    
    print("\n手动装饰的函数:")
    say_goodbye()


# ==================== 2. 带参数的函数装饰器 ====================

def log_decorator(func):
    """
    日志装饰器 - 处理带参数的函数
    """
    @functools.wraps(func)  # 保持原函数的元数据
    def wrapper(*args, **kwargs):
        """
        *args:   位置参数, 以元组形式传递
        **kwargs: 关键字参数, 以字典形式传递
        这样可以让装饰器兼容任意参数的函数。
        """
        print(f"[LOG] 调用函数: {func.__name__}")
        print(f"[LOG] 参数: args={args}, kwargs={kwargs}")
        # args示例: (1, 2)
        # kwargs示例: {"name": "Tom", "age": 18}
        
        result = func(*args, **kwargs)
        
        print(f"[LOG] 返回值: {result}")
        print(f"[LOG] 函数 {func.__name__} 执行完成")
        return result

    return wrapper


@log_decorator
def add_numbers(a: int, b: int) -> int:
    """加法函数"""
    return a + b


@log_decorator
def greet_person(name: str, age: int = 25) -> str:
    """问候函数"""
    return f"Hello, {name}! You are {age} years old."


def log_decorator_demo():
    """日志装饰器演示"""
    print("\n" + "=" * 50)
    print("2. 日志装饰器演示")
    print("=" * 50)
    
    result1 = add_numbers(10, 20)
    print(f"最终结果: {result1}\n")

    # "张三" -> 元组   age=30 -> 字典
    result2 = greet_person("张三", age=30)
    print(f"最终结果: {result2}")


# ==================== 3. 计时装饰器 ====================

def timer_decorator(func):
    """
    计时装饰器 - 测量函数执行时间
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print(f"[TIMER] 开始执行 {func.__name__} - {datetime.now().strftime('%H:%M:%S')}")
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"[TIMER] {func.__name__} 执行完成，耗时: {execution_time:.4f} 秒")
        
        return result
    
    return wrapper


@timer_decorator
def slow_function():
    """模拟耗时操作"""
    print("正在执行耗时操作...")
    time.sleep(1)  # 模拟1秒的操作
    return "操作完成"


@timer_decorator
def calculate_sum(n: int) -> int:
    """计算1到n的和"""
    print(f"计算1到{n}的和...")
    return sum(range(1, n + 1))


def timer_decorator_demo():
    """计时装饰器演示"""
    print("\n" + "=" * 50)
    print("3. 计时装饰器演示")
    print("=" * 50)
    
    slow_function()
    print()
    
    result = calculate_sum(1000000)
    print(f"计算结果: {result}")


# ==================== 4. 缓存装饰器 ====================

def cache_decorator(func):
    """
    简单的缓存装饰器
    """
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 创建缓存键
        cache_key = str(args) + str(sorted(kwargs.items()))
        
        if cache_key in cache:
            print(f"[CACHE] 缓存命中: {func.__name__}{args}")
            return cache[cache_key]
        
        print(f"[CACHE] 缓存未命中，执行函数: {func.__name__}{args}")
        result = func(*args, **kwargs)
        cache[cache_key] = result
        
        return result
    
    return wrapper


@cache_decorator
def fibonacci(n: int) -> int:
    """斐波那契数列（递归实现）"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@cache_decorator
def expensive_calculation(x: int, y: int) -> int:
    """模拟昂贵的计算"""
    print(f"    执行复杂计算: {x} * {y}")
    time.sleep(0.1)  # 模拟计算时间
    return x * y


def cache_decorator_demo():
    """缓存装饰器演示"""
    print("\n" + "=" * 50)
    print("4. 缓存装饰器演示")
    print("=" * 50)
    
    print("斐波那契数列计算:")
    print(f"fibonacci(10) = {fibonacci(10)}")
    print(f"fibonacci(10) = {fibonacci(10)}")  # 第二次调用，应该使用缓存
    
    print("\n昂贵计算演示:")
    print(f"expensive_calculation(5, 6) = {expensive_calculation(5, 6)}")
    print(f"expensive_calculation(5, 6) = {expensive_calculation(5, 6)}")  # 缓存命中
    print(f"expensive_calculation(7, 8) = {expensive_calculation(7, 8)}")  # 新计算


# ==================== 5. 权限检查装饰器 ====================

# 模拟用户权限系统
current_user = {"name": "张三", "role": "admin", "permissions": ["read", "write", "delete"]}

def require_permission(permission: str):
    """
    权限检查装饰器工厂
    这是一个带参数的装饰器
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if permission in current_user.get("permissions", []):
                print(f"[AUTH] 权限检查通过: {current_user['name']} 有 '{permission}' 权限")
                return func(*args, **kwargs)
            else:
                print(f"[AUTH] 权限不足: {current_user['name']} 缺少 '{permission}' 权限")
                return "权限不足，操作被拒绝"
        
        return wrapper
    return decorator


@require_permission("read")
def read_data():
    """读取数据"""
    return "数据读取成功"


@require_permission("write")
def write_data(data: str):
    """写入数据"""
    return f"数据写入成功: {data}"


@require_permission("admin")
def admin_operation():
    """管理员操作"""
    return "管理员操作执行成功"


def permission_decorator_demo():
    """权限装饰器演示"""
    print("\n" + "=" * 50)
    print("5. 权限检查装饰器演示")
    print("=" * 50)
    
    print(f"当前用户: {current_user['name']}, 角色: {current_user['role']}")
    print(f"权限列表: {current_user['permissions']}")
    print()
    
    print("尝试读取数据:")
    print(read_data())
    print()
    
    print("尝试写入数据:")
    print(write_data("重要数据"))
    print()
    
    print("尝试管理员操作:")
    print(admin_operation())


# ==================== 6. 重试装饰器 ====================

def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    重试装饰器
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    print(f"[RETRY] 第 {attempt} 次尝试执行 {func.__name__}")
                    result = func(*args, **kwargs)
                    print(f"[RETRY] {func.__name__} 执行成功")
                    return result
                
                except Exception as e:
                    print(f"[RETRY] 第 {attempt} 次尝试失败: {e}")
                    
                    if attempt == max_attempts:
                        print(f"[RETRY] 达到最大重试次数 ({max_attempts})，放弃执行")
                        raise e
                    
                    print(f"[RETRY] 等待 {delay} 秒后重试...")
                    time.sleep(delay)
                    return None
            return None

        return wrapper
    return decorator


@retry(max_attempts=3, delay=0.5)
def unreliable_network_call(success_rate: float = 0.3):
    """
    模拟不稳定的网络调用
    """
    import random
    
    if random.random() < success_rate:
        return "网络请求成功"
    else:
        raise ConnectionError("网络连接失败")


def retry_decorator_demo():
    """重试装饰器演示"""
    print("\n" + "=" * 50)
    print("6. 重试装饰器演示")
    print("=" * 50)
    
    try:
        result = unreliable_network_call(success_rate=0.7)  # 70% 成功率
        print(f"最终结果: {result}")
    except Exception as e:
        print(f"最终失败: {e}")


# ==================== 7. 多个装饰器组合 ====================

@timer_decorator
@log_decorator
@cache_decorator
def complex_calculation(n: int) -> int:
    """
    复杂计算函数 - 演示多个装饰器的组合使用
    装饰器的执行顺序是从下到上，即：
    1. cache_decorator
    2. log_decorator  
    3. timer_decorator
    """
    print(f"    正在计算 {n} 的阶乘...")
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result


def multiple_decorators_demo():
    """多装饰器组合演示"""
    print("\n" + "=" * 50)
    print("7. 多装饰器组合演示")
    print("=" * 50)
    
    print("第一次调用:")
    result1 = complex_calculation(5)
    print(f"结果: {result1}")
    
    print("\n第二次调用 (应该使用缓存):")
    result2 = complex_calculation(5)
    print(f"结果: {result2}")


# ==================== 8. 装饰器最佳实践 ====================

def validate_types(**expected_types):
    """
    类型验证装饰器 - 演示更高级的装饰器用法
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数的参数名
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # 验证类型
            for param_name, expected_type in expected_types.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeError(
                            f"参数 '{param_name}' 期望类型 {expected_type.__name__}, "
                            f"但得到 {type(value).__name__}"
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


@validate_types(name=str, age=int, salary=float)
def create_employee(name: str, age: int, salary: float = 5000.0) -> dict:
    """创建员工信息"""
    return {
        "name": name,
        "age": age,
        "salary": salary,
        "created_at": datetime.now().isoformat()
    }


def best_practices_demo():
    """装饰器最佳实践演示"""
    print("\n" + "=" * 50)
    print("8. 装饰器最佳实践 - 类型验证")
    print("=" * 50)
    
    # 正确的调用
    try:
        employee1 = create_employee("李四", 28, 8000.0)
        print(f"员工创建成功: {employee1}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 错误的类型
    try:
        employee2 = create_employee("王五", "28", 8000.0)  # age应该是int
        print(f"员工创建成功: {employee2}")
    except Exception as e:
        print(f"类型验证失败: {e}")


# ==================== 主函数 ====================

if __name__ == "__main__":
    print("🎯 Python 装饰器学习 - 完整演示")
    print("=" * 60)
    
    # 执行所有演示
    decorator_basic_demo()
    log_decorator_demo()
    timer_decorator_demo()
    cache_decorator_demo()
    permission_decorator_demo()
    retry_decorator_demo()
    multiple_decorators_demo()
    best_practices_demo()

    print("\n" + "=" * 60)
    print("🎉 装饰器基础学习完成！")
    print("=" * 60)

    print("\n📚 学习要点总结:")
    print("1. 装饰器本质上是高阶函数")
    print("2. 使用 @functools.wraps 保持原函数元数据")
    print("3. *args, **kwargs 处理任意参数")
    print("4. 装饰器可以组合使用")
    print("5. 带参数的装饰器需要三层嵌套")
    print("6. 装饰器常用于：日志、计时、缓存、权限、重试等")
