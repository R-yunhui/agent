from typing import TypedDict, NotRequired
from dataclasses import dataclass


class User:

    # 类变量（≈ static）
    species = "Homo sapiens"

    def __init__(self, name, age):
        # 实例变量，类似 java 的 public String name
        self.name = name
        self.age = age

    @property
    def name(self):
        # @property 将方法变成只读属性
        return self._name

    @name.setter
    def name(self, value):
        # @<属性名>.setter 允许你为该属性定义赋值行为
        if not isinstance(value, str):
            raise ValueError("Name must be a string")

        if len(value) == 0:
            raise ValueError("Name must be at least 0 characters long")
        self._name = value.strip()


class Animal(TypedDict):
    """
    TypedDict：带字段类型注解的字典结构
    """

    name: str
    category: str
    sound: str
    color: NotRequired[str]


class MathUtils:

    @staticmethod
    def add(x: int, y: int) -> int:
        """
        本质上是一个普通函数
        不能访问实例属性（self.xxx）或类属性（cls.xxx）

        工具函数（如日期格式化、数学计算）
        与类逻辑相关但无需状态的方法
        """
        return x + y

    @staticmethod
    def is_even(x: int) -> bool:
        return x & 1 == 0


class Person:

    species = "Homo sapiens"

    def __init__(self, name, age):
        self.name = name
        self.age = age

    @classmethod
    def from_string(cls, s: str):
        """
        可以访问类属性（cls.attr）
        继承友好：在子类中调用时，cls 是子类

        多种初始化方式（如从字符串、JSON、文件创建对象）
        单例模式、注册工厂等
        是实现“替代构造器”的标准方式。
        """
        name, age = s.split(",")
        return cls(name, int(age))

    @classmethod
    def get_species(cls):
        return cls.species


class Student(Person):

    pass


@dataclass
class Point:
    """
    自动生成 __init__、__repr__、__eq__ 等样板代码
    专为存储数据的类设计（类似 C 的 struct 或 Java 的 record）
    """

    x: int
    y: int


def main():
    user = User("John", 30)
    print(user.name)
    user.name = "   Jane   "
    print(user.name)

    print(f"user species: {user.species}")

    # 如果通过实例赋值（user.species = "Alien"），会创建一个新的实例变量，遮蔽类变量！
    user.species = "Alien"
    print(f"user species: {user.species}")

    # 类变量不会被影响
    print(f"User species: {User.species}")

    """
    公开（public）	直接定义：x = 1
    受保护（protected）	单下划线：_x（约定）
    私有（private）	双下划线：__x（名称改写）
    静态变量	类变量：count = 0
    常量	全大写类变量：PI = 3.14
    """

    animal = Animal(name="Cat", category="Mammal", sound="Meow", color="Black")
    print(f"animal is dict: {isinstance(animal, dict)}, animal: {animal}")

    sum = MathUtils.add(1, 2)
    print(f"add result: {sum}")

    math_utils = MathUtils()
    print(f"is even: {math_utils.is_even(1)}")

    person = Person.from_string("John,30")
    print(f"person name: {person.name}, age: {person.age}")
    print(f"person species: {Person.get_species()}")

    student = Student("Alice", 13)
    print(f"student name: {student.name}, age: {student.age}")
    print(f"student species: {Student.get_species()}")

    point = Point(1, 2)
    print(f"point: {point}")


if __name__ == "__main__":
    main()
