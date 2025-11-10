# Python 异常处理和上下文管理学习
"""
异常处理和上下文管理学习指南

对于Java开发者的理解：
- Python的异常处理类似于Java的try-catch-finally
- 上下文管理器类似于Java的try-with-resources
- Python的异常更加灵活，可以捕获多种异常类型
"""

import sys
import traceback
from contextlib import contextmanager, ExitStack
from typing import Any, Generator, Optional


# ==================== 1. 基础异常处理 ====================

def basic_exception_handling():
    """基础异常处理演示"""
    print("=" * 50)
    print("1. 基础异常处理演示")
    print("=" * 50)
    
    # 基本try-except
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        print(f"捕获到除零错误: {e}")
    
    # 捕获多种异常
    try:
        data = {"key": "value"}
        print(data["nonexistent_key"])
    except KeyError as e:
        print(f"捕获到键错误: {e}")
    except Exception as e:
        print(f"捕获到其他异常: {e}")
    
    # try-except-else-finally
    try:
        result = 10 / 2
        print(f"计算结果: {result}")
    except ZeroDivisionError:
        print("除零错误")
    else:
        print("没有异常发生")
    finally:
        print("无论如何都会执行")


# ==================== 2. 自定义异常类 ====================

class ValidationError(Exception):
    """验证错误异常"""
    
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)
    
    def __str__(self):
        if self.field:
            return f"字段 '{self.field}' 验证失败: {self.message}"
        return f"验证失败: {self.message}"


class BusinessLogicError(Exception):
    """业务逻辑错误异常"""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class DatabaseError(Exception):
    """数据库错误异常"""
    
    def __init__(self, message: str, sql: str = None):
        self.message = message
        self.sql = sql
        super().__init__(self.message)
    
    def __str__(self):
        if self.sql:
            return f"数据库错误: {self.message} (SQL: {self.sql})"
        return f"数据库错误: {self.message}"


def custom_exception_demo():
    """自定义异常演示"""
    print("\n" + "=" * 50)
    print("2. 自定义异常演示")
    print("=" * 50)
    
    # 验证错误
    try:
        age = -5
        if age < 0:
            raise ValidationError("年龄不能为负数", "age")
    except ValidationError as e:
        print(f"捕获验证错误: {e}")
    
    # 业务逻辑错误
    try:
        balance = 100
        withdraw_amount = 200
        if withdraw_amount > balance:
            raise BusinessLogicError("余额不足", "INSUFFICIENT_FUNDS")
    except BusinessLogicError as e:
        print(f"捕获业务逻辑错误: {e}")
    
    # 数据库错误
    try:
        sql = "SELECT * FROM users WHERE id = ?"
        raise DatabaseError("连接超时", sql)
    except DatabaseError as e:
        print(f"捕获数据库错误: {e}")


# ==================== 3. 异常链和异常上下文 ====================

def process_user_data(user_id: str) -> dict:
    """处理用户数据 - 演示异常链"""
    try:
        # 模拟数据库查询
        if user_id == "invalid":
            raise DatabaseError("用户不存在", f"SELECT * FROM users WHERE id = '{user_id}'")
        
        # 模拟数据处理
        if user_id == "corrupted":
            raise ValueError("数据格式错误")
        
        return {"id": user_id, "name": "张三", "email": "zhangsan@example.com"}
    
    except DatabaseError as e:
        # 重新抛出异常，添加更多上下文
        raise BusinessLogicError(f"无法处理用户 {user_id}") from e


def exception_chaining_demo():
    """异常链演示"""
    print("\n" + "=" * 50)
    print("3. 异常链演示")
    print("=" * 50)
    
    # 测试正常情况
    try:
        result = process_user_data("123")
        print(f"处理成功: {result}")
    except Exception as e:
        print(f"处理失败: {e}")
        print(f"异常类型: {type(e).__name__}")
        if e.__cause__:
            print(f"原始异常: {e.__cause__}")
    
    # 测试数据库错误
    try:
        result = process_user_data("invalid")
        print(f"处理成功: {result}")
    except Exception as e:
        print(f"处理失败: {e}")
        print(f"异常类型: {type(e).__name__}")
        if e.__cause__:
            print(f"原始异常: {e.__cause__}")
    
    # 测试数据错误
    try:
        result = process_user_data("corrupted")
        print(f"处理成功: {result}")
    except Exception as e:
        print(f"处理失败: {e}")
        print(f"异常类型: {type(e).__name__}")


# ==================== 4. 上下文管理器基础 ====================

class FileManager:
    """文件管理器 - 演示上下文管理器"""
    
    def __init__(self, filename: str, mode: str = 'r'):
        self.filename = filename
        self.mode = mode
        self.file = None
    
    def __enter__(self):
        """进入上下文时调用"""
        print(f"打开文件: {self.filename}")
        self.file = open(self.filename, self.mode, encoding='utf-8')
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时调用"""
        print(f"关闭文件: {self.filename}")
        if self.file:
            self.file.close()
        
        # 如果发生异常，可以在这里处理
        if exc_type:
            print(f"文件操作发生异常: {exc_type.__name__}: {exc_val}")
            # 返回True表示异常已被处理，不会向上传播
            # 返回False或None表示异常继续向上传播
            return False
        return None


def context_manager_demo():
    """上下文管理器演示"""
    print("\n" + "=" * 50)
    print("4. 上下文管理器演示")
    print("=" * 50)
    
    # 正常使用
    try:
        with FileManager("test.txt", "w") as f:
            f.write("Hello, World!")
            print("文件写入成功")
    except Exception as e:
        print(f"文件操作失败: {e}")
    
    # 异常情况
    try:
        with FileManager("nonexistent.txt", "r") as f:
            content = f.read()
            print(f"文件内容: {content}")
    except Exception as e:
        print(f"文件操作失败: {e}")


# ==================== 5. 使用contextlib创建上下文管理器 ====================

@contextmanager
def database_connection(host: str, port: int) -> Generator[Any, None, None]:
    """数据库连接上下文管理器"""
    connection = None
    try:
        print(f"连接到数据库: {host}:{port}")
        # 模拟数据库连接
        connection = f"Connection to {host}:{port}"
        yield connection
    except Exception as e:
        print(f"数据库操作异常: {e}")
        raise
    finally:
        if connection:
            print(f"关闭数据库连接: {host}:{port}")


@contextmanager
def transaction():
    """事务上下文管理器"""
    print("开始事务")
    try:
        yield
        print("提交事务")
    except Exception as e:
        print(f"回滚事务: {e}")
        raise
    finally:
        print("事务结束")


def contextlib_demo():
    """contextlib演示"""
    print("\n" + "=" * 50)
    print("5. contextlib演示")
    print("=" * 50)
    
    # 数据库连接
    try:
        with database_connection("localhost", 5432) as conn:
            print(f"使用连接: {conn}")
            # 模拟数据库操作
            print("执行查询...")
    except Exception as e:
        print(f"数据库操作失败: {e}")
    
    # 事务处理
    try:
        with transaction():
            print("执行业务逻辑...")
            # 模拟业务操作
            print("更新数据...")
    except Exception as e:
        print(f"事务处理失败: {e}")


# ==================== 6. 嵌套上下文管理器 ====================

def nested_context_demo():
    """嵌套上下文管理器演示"""
    print("\n" + "=" * 50)
    print("6. 嵌套上下文管理器演示")
    print("=" * 50)
    
    # 使用ExitStack管理多个上下文
    with ExitStack() as stack:
        # 打开多个资源
        db_conn = stack.enter_context(database_connection("localhost", 5432))
        file_mgr = stack.enter_context(FileManager("output.txt", "w"))
        
        print(f"使用数据库连接: {db_conn}")
        print("写入文件...")
        file_mgr.write("数据库查询结果")
        
        # 所有资源会在退出时自动关闭


# ==================== 7. 实际应用场景 ====================

class LogManager:
    """日志管理器 - 实际应用场景"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.log_entries = []
    
    def __enter__(self):
        print(f"开始日志记录: {self.log_file}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.log_entries.append(f"ERROR: {exc_type.__name__}: {exc_val}")
        else:
            self.log_entries.append("INFO: 操作完成")
        
        # 写入日志文件
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                for entry in self.log_entries:
                    f.write(f"{entry}\n")
        except Exception as e:
            print(f"写入日志失败: {e}")
        
        print(f"结束日志记录: {self.log_file}")
        return False
    
    def log(self, message: str):
        """记录日志"""
        self.log_entries.append(f"INFO: {message}")


def real_world_demo():
    """实际应用场景演示"""
    print("\n" + "=" * 50)
    print("7. 实际应用场景演示")
    print("=" * 50)
    
    # 正常操作
    try:
        with LogManager("app.log") as logger:
            logger.log("开始处理用户请求")
            logger.log("验证用户权限")
            logger.log("执行业务逻辑")
            logger.log("返回处理结果")
    except Exception as e:
        print(f"操作失败: {e}")
    
    # 异常情况
    try:
        with LogManager("error.log") as logger:
            logger.log("开始处理用户请求")
            logger.log("验证用户权限")
            # 模拟异常
            raise ValueError("业务逻辑错误")
    except Exception as e:
        print(f"操作失败: {e}")


# ==================== 8. 异常处理最佳实践 ====================

def safe_divide(a: float, b: float) -> Optional[float]:
    """安全除法 - 异常处理最佳实践"""
    try:
        return a / b
    except ZeroDivisionError:
        print("警告: 除零错误，返回None")
        return None
    except TypeError:
        print("警告: 类型错误，返回None")
        return None


def robust_file_processor(filename: str) -> bool:
    """健壮的文件处理器"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"文件内容长度: {len(content)}")
            return True
    except FileNotFoundError:
        print(f"文件不存在: {filename}")
        return False
    except PermissionError:
        print(f"没有权限访问文件: {filename}")
        return False
    except UnicodeDecodeError:
        print(f"文件编码错误: {filename}")
        return False
    except Exception as e:
        print(f"未知错误: {type(e).__name__}: {e}")
        return False


def best_practices_demo():
    """最佳实践演示"""
    print("\n" + "=" * 50)
    print("8. 异常处理最佳实践演示")
    print("=" * 50)
    
    # 安全除法
    print(f"10 / 2 = {safe_divide(10, 2)}")
    print(f"10 / 0 = {safe_divide(10, 0)}")
    print(f"10 / 'a' = {safe_divide(10, 'a')}")
    
    # 健壮的文件处理
    print(f"处理存在文件: {robust_file_processor('test.txt')}")
    print(f"处理不存在文件: {robust_file_processor('nonexistent.txt')}")


# ==================== 主函数 ====================

if __name__ == "__main__":
    print("Python 异常处理和上下文管理学习 - 完整演示")
    print("=" * 70)
    
    # 执行所有演示
    basic_exception_handling()
    custom_exception_demo()
    exception_chaining_demo()
    context_manager_demo()
    contextlib_demo()
    nested_context_demo()
    real_world_demo()
    best_practices_demo()
    
    print("\n" + "=" * 70)
    print("异常处理和上下文管理学习完成！")
    print("=" * 70)
    
    print("\n学习要点总结:")
    print("1. 使用try-except-else-finally处理异常")
    print("2. 创建自定义异常类提供更好的错误信息")
    print("3. 使用异常链追踪错误来源")
    print("4. 实现__enter__和__exit__方法创建上下文管理器")
    print("5. 使用@contextmanager装饰器简化上下文管理器")
    print("6. 使用ExitStack管理多个上下文")
    print("7. 异常处理要具体，避免捕获所有异常")
    print("8. 上下文管理器确保资源正确释放")
