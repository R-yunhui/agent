#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python初学者完整学习代码示例
适合有Java开发经验的程序员
作者: AI助手
日期: 2024
"""

from typing import List, Dict, Optional, Tuple, Any
import json
import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod


# ============================================================================
# 1. 基础语法对比 (与Java的差异)
# ============================================================================

def basic_syntax_demo():
    """
    基础语法演示 - 与Java的主要差异
    """
    print("=== 1. 基础语法演示 ===")

    # 变量声明 - Python不需要声明类型(动态类型)
    # Java: int age = 25;
    age = 25
    name = "张三"
    is_student = True

    # 类型提示(可选，但推荐使用)
    height: float = 175.5
    scores: List[int] = [85, 92, 78, 96]

    print(f"姓名: {name}, 年龄: {age}, 身高: {height}cm")
    print(f"是否学生: {is_student}")
    print(f"成绩列表: {scores}")

    # 字符串操作 - Python的字符串更加灵活
    # f-string格式化(Python 3.6+，类似Java的String.format)
    message: str = f"Hello, {name}! 你今年{age}岁了。"
    print(message)

    # 多行字符串
    multi_line = """
    这是一个多行字符串
    在Java中需要使用StringBuilder
    或者字符串连接
    """
    print(multi_line.strip())


# ============================================================================
# 2. 数据结构 (集合类对比)
# ============================================================================

def data_structures_demo():
    """
    数据结构演示 - 对比Java集合框架
    """
    print("\n=== 2. 数据结构演示 ===")

    # List - 类似Java的ArrayList，但更灵活
    fruits: List[str] = ["苹果", "香蕉", "橙子"]
    print(f"水果列表: {fruits}")
    print(f"第一个水果: {fruits[0]}")
    print(f"最后一个水果: {fruits[-1]}")  # Python特色：负索引
    fruits.append("葡萄")  # 添加元素
    print(f"更新后的水果列表: {fruits}")

    # 列表切片 - Python独有的强大功能
    print(f"前两个水果: {fruits[:2]}")
    print(f"后两个水果: {fruits[-2:]}")

    # Dictionary - 类似Java的HashMap
    student: Dict[str, Any] = {
        "name": "李四",
        "age": 20,
        "major": "计算机科学",
        "grades": [88, 92, 85]
    }
    print(f"学生信息: {student}")
    print(f"学生姓名: {student['name']}")
    print(f"学生年龄: {student.get('age', '未知')}")

    # Set - 类似Java的HashSet
    unique_numbers: set = {1, 2, 3, 3, 4, 4, 5}
    print(f"唯一数字集合: {unique_numbers}")

    # Tuple - 不可变序列(Java中没有直接对应)
    coordinates: Tuple[float, float] = (39.9042, 116.4074)
    print(f"坐标 (纬度, 经度): {coordinates}")

    animals: List[Dict[str: Any]] = [
        {
            "name": "狗",
            "age": 3,
            "type": "犬科动物"
        },
        {
            "name": "猫",
            "age": 2,
            "type": "猫科动物"
        },
        {
            "name": "鹦鹉",
            "age": 1,
            "type": "飞行类动物"
        }
    ]
    print(f"动物列表: {animals}")


# ============================================================================
# 3. 控制流程 (与Java类似但语法不同)
# ============================================================================

def control_flow_demo():
    """
    控制流程演示
    """
    print("\n=== 3. 控制流程演示 ===")

    # if-elif-else (Java: if-else if-else)
    score = 85
    if score >= 90:
        grade = "A"
    elif score >= 80:  # Java中是 else if
        grade = "B"
    elif score >= 70:
        grade = "C"
    else:
        grade = "D"
    print(f"分数: {score}, 等级: {grade}")

    # for循环 - Python的for更像Java的增强for循环
    print("\n数字1-5:")
    for i in range(1, 6):  # range(1, 6) 生成1到5
        print(f"数字: {i}")

    # 遍历列表
    colors = ["红色", "绿色", "蓝色"]
    print("\n颜色列表:")
    for color in colors:
        print(f"颜色: {color}")

    # enumerate - 获取索引和值
    print("\n带索引的颜色列表:")
    for index, color in enumerate(colors):
        print(f"索引{index}: {color}")

    # while循环
    print("\n倒计时:")
    countdown = 5
    while countdown > 0:
        print(f"{countdown}...")
        countdown -= 1
    print("发射!")


# ============================================================================
# 4. 函数定义 (与Java方法的差异)
# ============================================================================

def function_demo():
    """
    函数演示
    """
    print("\n=== 4. 函数演示 ===")

    # 基本函数定义
    def greet(name: str, age: int = 18) -> str:
        """问候函数 - 支持默认参数"""
        return f"你好，{name}！你今年{age}岁了。"

    # 调用函数
    message1 = greet("王五")
    message2 = greet("赵六", 25)
    print(message1)
    print(message2)

    # 可变参数 (*args)
    def sum_numbers(*number: int) -> int:
        """计算多个数字的和"""
        return sum(number)

    result = sum_numbers(1, 2, 3, 4, 5)
    print(f"1+2+3+4+5 = {result}")

    # 关键字参数 (**kwargs)
    def create_person(**kwargs) -> Dict[str, Any]:
        """创建人员信息字典"""
        return kwargs

    person = create_person(name="孙七", age=30, city="北京", job="工程师")
    print(f"人员信息: {person}")

    # Lambda表达式 (类似Java的Lambda)
    numbers = [1, 2, 3, 4, 5, 6]
    squared = list(map(lambda x: x ** 2, numbers))
    print(f"平方数: {squared}")

    # 列表推导式 (Python独有的强大功能)
    even_squares = [x ** 2 for x in numbers if x & 1 == 0]
    print(f"偶数的平方: {even_squares}")


# ============================================================================
# 5. 面向对象编程 (与Java的差异)
# ============================================================================

# 抽象基类 (类似Java的abstract class)
class Animal(ABC):
    """动物抽象基类"""

    def __init__(self, name: str, age: int):
        self.name = name  # public属性(Python没有真正的private)
        self._age = age  # 约定的protected属性(单下划线)
        self.__id = id(self)  # 约定的private属性(双下划线)

    @abstractmethod
    def make_sound(self) -> str:
        """抽象方法 - 子类必须实现"""
        pass

    def get_info(self) -> str:
        """获取动物信息"""
        return f"{self.name}, {self._age}岁"

    # Python特殊方法 (类似Java的toString)
    def __str__(self) -> str:
        return f"Animal(name={self.name}, age={self._age})"

    def __repr__(self) -> str:
        return self.__str__()


class Dog(Animal):
    """狗类 - 继承Animal"""

    def __init__(self, name: str, age: int, breed: str):
        super().__init__(name, age)  # 调用父类构造函数
        self.breed = breed

    def make_sound(self) -> str:
        """实现抽象方法"""
        return "汪汪!"

    def fetch(self, item: str) -> str:
        """狗特有的方法"""
        return f"{self.name}去捡{item}了!"


class Cat(Animal):
    """猫类 - 继承Animal"""

    def __init__(self, name: str, age: int, color: str):
        super().__init__(name, age)
        self.color = color

    def make_sound(self) -> str:
        """实现抽象方法"""
        return "喵喵~"

    def climb(self) -> str:
        """猫特有的方法"""
        return f"{self.name}爬上了树!"


# 数据类 (类似Java的record，Python 3.7+)
@dataclass
class Person:
    """人员数据类"""
    name: str
    age: int
    email: Optional[str] = None

    def is_adult(self) -> bool:
        return self.age >= 18

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps({
            "name": self.name,
            "age": self.age,
            "email": self.email
        }, ensure_ascii=False)


def oop_demo():
    """
    面向对象编程演示
    """
    print("\n=== 5. 面向对象编程演示 ===")

    # 创建对象
    dog = Dog("旺财", 3, "金毛")
    cat = Cat("咪咪", 2, "橘色")

    # 多态 - 相同接口，不同实现
    animals: List[Animal] = [dog, cat]
    for animal in animals:
        print(f"{animal.get_info()} 说: {animal.make_sound()}")

    # 调用特有方法
    print(dog.fetch("球"))
    print(cat.climb())

    # 数据类使用
    person = Person("张三", 25, "zhangsan@example.com")
    print(f"人员信息: {person}")
    print(f"是否成年: {person.is_adult()}")
    print(f"JSON格式: {person.to_json()}")


# ============================================================================
# 6. 异常处理 (与Java类似)
# ============================================================================

def exception_demo():
    """
    异常处理演示
    """
    print("\n=== 6. 异常处理演示 ===")

    # 基本异常处理
    try:
        # 模拟用户输入
        test_input = "a"  # 可以修改这个值来测试不同情况
        number = int(test_input)
        result = 100 / number
        print(f"100 / {number} = {result}")
    except ValueError:
        print("错误: 输入的不是有效数字!")
    except ZeroDivisionError:
        print("错误: 不能除以零!")
    except Exception as e:
        print(f"未知错误: {e}")
    else:
        print("计算成功完成!")
    finally:
        print("异常处理结束")

    # 自定义异常
    class CustomError(Exception):
        """自定义异常类"""

        def __init__(self, message: str):
            self.message = message
            super().__init__(self.message)

    def validate_age(age: int):
        if age < 0:
            raise CustomError("年龄不能为负数")
        if age > 150:
            raise CustomError("年龄不能超过150岁")

    try:
        validate_age(-5)
    except CustomError as e:
        print(f"验证失败: {e.message}")


# ============================================================================
# 7. 文件操作和上下文管理器
# ============================================================================

def file_operations_demo():
    """
    文件操作演示
    """
    print("\n=== 7. 文件操作演示 ===")

    # 写入文件 - 使用with语句(类似Java的try-with-resources)
    data = {
        "students": [
            {"name": "张三", "age": 20, "score": 85},
            {"name": "李四", "age": 21, "score": 92},
            {"name": "王五", "age": 19, "score": 78}
        ]
    }

    filename = "students.json"

    # 写入JSON文件
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        print(f"数据已写入 {filename}")

        # 读取JSON文件
        with open(filename, 'r', encoding='utf-8') as file:
            loaded_data = json.load(file)
        print(f"从文件读取的数据: {loaded_data}")
    except FileNotFoundError:
        print(f"文件 {filename} 不存在")
    except Exception as e:
        print(f"文件操作失败: {e}")


# ============================================================================
# 8. 实用工具和技巧
# ============================================================================

def utility_demo():
    """
    实用工具和技巧演示
    """
    print("\n=== 8. 实用工具和技巧演示 ===")

    # 日期时间处理
    now = datetime.datetime.now()
    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # 字符串操作
    text = "  Hello, Python World!  "
    print(f"原文本: '{text}'")
    print(f"去空格: '{text.strip()}'")
    print(f"大写: '{text.upper()}'")
    print(f"替换: '{text.replace('Python', 'Java')}'")

    # 列表操作技巧
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # 过滤
    even_numbers = [x for x in numbers if x % 2 == 0]
    print(f"偶数: {even_numbers}")

    # 映射
    squared_numbers = [x ** 2 for x in numbers]
    print(f"平方数: {squared_numbers}")

    # 聚合操作
    print(f"总和: {sum(numbers)}")
    print(f"最大值: {max(numbers)}")
    print(f"最小值: {min(numbers)}")
    print(f"平均值: {sum(numbers) / len(numbers)}")

    # 字典操作
    scores = {"张三": 85, "李四": 92, "王五": 78, "赵六": 96}

    # 字典推导式
    high_scores = {name: score for name, score in scores.items() if score >= 90}
    print(f"高分学生: {high_scores}")

    # 排序
    sorted_by_score = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print(f"按分数排序: {sorted_by_score}")


# ============================================================================
# 9. 简单的实际应用示例
# ============================================================================

class StudentManager:
    """
    学生管理系统 - 综合应用示例
    """

    def __init__(self):
        self.students: List[Person] = []

    def add_student(self, name: str, age: int, email: Optional[str] = None):
        """添加学生"""
        student = Person(name, age, email)
        self.students.append(student)
        print(f"学生 {name} 添加成功!")

    def list_students(self):
        """列出所有学生"""
        if not self.students:
            print("暂无学生信息")
            return

        print("\n学生列表:")
        for i, student in enumerate(self.students, 1):
            adult_status = "成年" if student.is_adult() else "未成年"
            print(f"{i}. {student.name}, {student.age}岁 ({adult_status})")

    def find_student(self, name: str) -> Optional[Person]:
        """查找学生"""
        for student in self.students:
            if student.name == name:
                return student
        return None

    def export_to_json(self, filename: str):
        """导出到JSON文件"""
        data = {
            "students": [
                {
                    "name": student.name,
                    "age": student.age,
                    "email": student.email,
                    "is_adult": student.is_adult()
                }
                for student in self.students
            ]
        }

        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            print(f"学生信息已导出到 {filename}")
        except Exception as e:
            print(f"导出失败: {e}")


def practical_demo():
    """
    实际应用演示
    """
    print("\n=== 9. 实际应用演示 - 学生管理系统 ===")

    manager = StudentManager()

    # 添加学生
    manager.add_student("张三", 20, "zhangsan@example.com")
    manager.add_student("李四", 17, "lisi@example.com")
    manager.add_student("王五", 22)

    # 列出学生
    manager.list_students()

    # 查找学生
    student = manager.find_student("张三")
    if student:
        print(f"\n找到学生: {student.name}, {student.age}岁")

    # 导出数据
    manager.export_to_json("student_data.json")


# ============================================================================
# 主程序入口
# ============================================================================

def main():
    """
    主函数 - 运行所有演示
    """
    print("Python 初学者完整学习示例")
    print("-" * 50)

    try:
        # 运行所有演示
        basic_syntax_demo()
        data_structures_demo()
        control_flow_demo()
        function_demo()
        oop_demo()
        exception_demo()
        file_operations_demo()
        utility_demo()
        practical_demo()

        print("\n" + "=" * 50)
        print("🎉 所有演示完成!")
        print("\n学习建议:")
        print("1. 仔细阅读每个函数的注释和代码")
        print("2. 尝试修改代码参数，观察结果变化")
        print("3. 练习编写类似的代码")
        print("4. 查阅Python官方文档了解更多细节")
        print("\nPython与Java的主要差异:")
        print("• 动态类型 vs 静态类型")
        print("• 缩进语法 vs 大括号")
        print("• 更简洁的语法")
        print("• 强大的内置数据结构")
        print("• 列表推导式等独特功能")

    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()