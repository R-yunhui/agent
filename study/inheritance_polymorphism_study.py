# Python 继承和多态学习
"""
继承和多态学习指南

对于Java开发者的理解：
- Python支持多重继承，而Java只支持单继承
- Python的多态基于鸭子类型，比Java更灵活
- 抽象基类(ABC)类似于Java的抽象类和接口
- MRO(Method Resolution Order)是Python特有的方法解析顺序
"""

from abc import ABC, abstractmethod
from typing import List, Any, Protocol
import math


# ==================== 1. 基础继承 ====================

class Animal:
    """动物基类 - 演示基础继承"""
    
    def __init__(self, name: str, age: int):
        """初始化动物"""
        self.name = name
        self.age = age
        self.species = "未知物种"
    
    def speak(self) -> str:
        """发声 - 基类方法"""
        return f"{self.name} 发出声音"
    
    def move(self) -> str:
        """移动 - 基类方法"""
        return f"{self.name} 正在移动"
    
    def info(self) -> str:
        """信息 - 基类方法"""
        return f"{self.species}: {self.name}, {self.age}岁"
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Animal({self.name}, {self.age})"


class Dog(Animal):
    """狗类 - 继承自Animal"""
    
    def __init__(self, name: str, age: int, breed: str):
        """初始化狗"""
        super().__init__(name, age)  # 调用父类构造函数
        self.species = "犬科"
        self.breed = breed
    
    def speak(self) -> str:
        """重写父类方法"""
        return f"{self.name} 汪汪叫"
    
    def fetch(self) -> str:
        """狗特有的方法"""
        return f"{self.name} 去捡球"
    
    def info(self) -> str:
        """重写信息方法"""
        return f"{self.species}: {self.name}, {self.age}岁, 品种: {self.breed}"


class Cat(Animal):
    """猫类 - 继承自Animal"""
    
    def __init__(self, name: str, age: int, color: str):
        """初始化猫"""
        super().__init__(name, age)
        self.species = "猫科"
        self.color = color
    
    def speak(self) -> str:
        """重写父类方法"""
        return f"{self.name} 喵喵叫"
    
    def climb(self) -> str:
        """猫特有的方法"""
        return f"{self.name} 爬树"
    
    def info(self) -> str:
        """重写信息方法"""
        return f"{self.species}: {self.name}, {self.age}岁, 颜色: {self.color}"


def basic_inheritance_demo():
    """基础继承演示"""
    print("=" * 50)
    print("1. 基础继承演示")
    print("=" * 50)
    
    # 创建动物对象
    animals = [
        Dog("旺财", 3, "金毛"),
        Cat("咪咪", 2, "橘色"),
        Animal("未知动物", 1)
    ]
    
    print("动物信息:")
    for animal in animals:
        print(f"  {animal.info()}")
    
    print("\n动物行为:")
    for animal in animals:
        print(f"  {animal.speak()}")
        print(f"  {animal.move()}")
        
        # 检查特有方法
        if hasattr(animal, 'fetch'):
            print(f"  {animal.fetch()}")
        if hasattr(animal, 'climb'):
            print(f"  {animal.climb()}")
        print()
    
    # isinstance 和 issubclass 检查
    dog = animals[0]
    print("类型检查:")
    print(f"isinstance(dog, Dog): {isinstance(dog, Dog)}")
    print(f"isinstance(dog, Animal): {isinstance(dog, Animal)}")
    print(f"issubclass(Dog, Animal): {issubclass(Dog, Animal)}")


# ==================== 2. 多重继承和MRO ====================

class Flyable:
    """可飞行的混入类"""
    
    def fly(self) -> str:
        """飞行方法"""
        return f"{self.name} 正在飞行"
    
    def land(self) -> str:
        """着陆方法"""
        return f"{self.name} 着陆了"


class Swimmable:
    """可游泳的混入类"""
    
    def swim(self) -> str:
        """游泳方法"""
        return f"{self.name} 正在游泳"
    
    def dive(self) -> str:
        """潜水方法"""
        return f"{self.name} 潜入水中"


class Bird(Animal, Flyable):
    """鸟类 - 多重继承"""
    
    def __init__(self, name: str, age: int, wingspan: float):
        """初始化鸟类"""
        super().__init__(name, age)
        self.species = "鸟类"
        self.wingspan = wingspan
    
    def speak(self) -> str:
        """重写发声方法"""
        return f"{self.name} 啾啾叫"
    
    def info(self) -> str:
        """重写信息方法"""
        return f"{self.species}: {self.name}, {self.age}岁, 翼展: {self.wingspan}米"


class Duck(Animal, Flyable, Swimmable):
    """鸭子类 - 多重继承多个混入类"""
    
    def __init__(self, name: str, age: int):
        """初始化鸭子"""
        super().__init__(name, age)
        self.species = "水禽"
    
    def speak(self) -> str:
        """重写发声方法"""
        return f"{self.name} 嘎嘎叫"
    
    def move(self) -> str:
        """重写移动方法"""
        return f"{self.name} 在水中游泳或在空中飞行"


class Penguin(Animal, Swimmable):
    """企鹅类 - 不能飞的鸟"""
    
    def __init__(self, name: str, age: int):
        """初始化企鹅"""
        super().__init__(name, age)
        self.species = "企鹅"
    
    def speak(self) -> str:
        """重写发声方法"""
        return f"{self.name} 嘎嘎叫"
    
    def slide(self) -> str:
        """企鹅特有的滑行方法"""
        return f"{self.name} 在冰上滑行"


def multiple_inheritance_demo():
    """多重继承演示"""
    print("\n" + "=" * 50)
    print("2. 多重继承和MRO演示")
    print("=" * 50)
    
    # 创建不同类型的动物
    bird = Bird("小鸟", 1, 0.3)
    duck = Duck("唐老鸭", 2)
    penguin = Penguin("企鹅", 3)
    
    animals = [bird, duck, penguin]
    
    print("动物能力测试:")
    for animal in animals:
        print(f"\n{animal.info()}")
        print(f"  发声: {animal.speak()}")
        
        # 测试飞行能力
        if hasattr(animal, 'fly'):
            print(f"  飞行: {animal.fly()}")
            print(f"  着陆: {animal.land()}")
        else:
            print(f"  {animal.name} 不会飞行")
        
        # 测试游泳能力
        if hasattr(animal, 'swim'):
            print(f"  游泳: {animal.swim()}")
            print(f"  潜水: {animal.dive()}")
        else:
            print(f"  {animal.name} 不会游泳")
        
        # 测试特殊能力
        if hasattr(animal, 'slide'):
            print(f"  滑行: {animal.slide()}")
    
    # MRO (Method Resolution Order) 演示
    print(f"\n方法解析顺序 (MRO):")
    print(f"Duck MRO: {[cls.__name__ for cls in Duck.__mro__]}")
    print(f"Bird MRO: {[cls.__name__ for cls in Bird.__mro__]}")
    print(f"Penguin MRO: {[cls.__name__ for cls in Penguin.__mro__]}")


# ==================== 3. 抽象基类 (ABC) ====================

class Shape(ABC):
    """形状抽象基类"""
    
    def __init__(self, name: str):
        """初始化形状"""
        self.name = name
    
    @abstractmethod
    def area(self) -> float:
        """计算面积 - 抽象方法"""
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        """计算周长 - 抽象方法"""
        pass
    
    def info(self) -> str:
        """形状信息 - 具体方法"""
        return f"{self.name}: 面积={self.area():.2f}, 周长={self.perimeter():.2f}"
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Shape({self.name})"


class Rectangle(Shape):
    """矩形类 - 继承抽象基类"""
    
    def __init__(self, width: float, height: float):
        """初始化矩形"""
        super().__init__("矩形")
        self.width = width
        self.height = height
    
    def area(self) -> float:
        """实现抽象方法 - 计算面积"""
        return self.width * self.height
    
    def perimeter(self) -> float:
        """实现抽象方法 - 计算周长"""
        return 2 * (self.width + self.height)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Rectangle({self.width}x{self.height})"


class Circle(Shape):
    """圆形类 - 继承抽象基类"""
    
    def __init__(self, radius: float):
        """初始化圆形"""
        super().__init__("圆形")
        self.radius = radius
    
    def area(self) -> float:
        """实现抽象方法 - 计算面积"""
        return math.pi * self.radius ** 2
    
    def perimeter(self) -> float:
        """实现抽象方法 - 计算周长"""
        return 2 * math.pi * self.radius
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Circle(r={self.radius})"


class Triangle(Shape):
    """三角形类 - 继承抽象基类"""
    
    def __init__(self, a: float, b: float, c: float):
        """初始化三角形"""
        super().__init__("三角形")
        self.a = a
        self.b = b
        self.c = c
        
        # 验证三角形有效性
        if not self._is_valid_triangle():
            raise ValueError("无效的三角形边长")
    
    def _is_valid_triangle(self) -> bool:
        """验证三角形有效性"""
        return (self.a + self.b > self.c and 
                self.a + self.c > self.b and 
                self.b + self.c > self.a)
    
    def area(self) -> float:
        """实现抽象方法 - 使用海伦公式计算面积"""
        s = self.perimeter() / 2  # 半周长
        return math.sqrt(s * (s - self.a) * (s - self.b) * (s - self.c))
    
    def perimeter(self) -> float:
        """实现抽象方法 - 计算周长"""
        return self.a + self.b + self.c
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Triangle({self.a}, {self.b}, {self.c})"


def abstract_base_class_demo():
    """抽象基类演示"""
    print("\n" + "=" * 50)
    print("3. 抽象基类 (ABC) 演示")
    print("=" * 50)
    
    # 创建不同形状
    shapes = [
        Rectangle(5, 3),
        Circle(4),
        Triangle(3, 4, 5)
    ]
    
    print("形状信息:")
    for shape in shapes:
        print(f"  {shape}: {shape.info()}")
    
    # 尝试创建抽象基类实例（会失败）
    print(f"\n尝试创建抽象基类实例:")
    try:
        # shape = Shape("测试形状")  # 这会抛出TypeError
        print("无法直接实例化抽象基类")
    except TypeError as e:
        print(f"错误: {e}")
    
    # 计算总面积
    total_area = sum(shape.area() for shape in shapes)
    print(f"\n所有形状总面积: {total_area:.2f}")


# ==================== 4. 协议 (Protocol) - 结构化子类型 ====================

class Drawable(Protocol):
    """可绘制协议 - 类似于接口"""
    
    def draw(self) -> str:
        """绘制方法"""
        ...
    
    def get_color(self) -> str:
        """获取颜色方法"""
        ...


class Point:
    """点类 - 实现Drawable协议"""
    
    def __init__(self, x: float, y: float, color: str = "black"):
        """初始化点"""
        self.x = x
        self.y = y
        self.color = color
    
    def draw(self) -> str:
        """实现绘制方法"""
        return f"在({self.x}, {self.y})绘制{self.color}点"
    
    def get_color(self) -> str:
        """实现获取颜色方法"""
        return self.color
    
    def move(self, dx: float, dy: float) -> None:
        """移动点"""
        self.x += dx
        self.y += dy


class Line:
    """线类 - 实现Drawable协议"""
    
    def __init__(self, start: Point, end: Point, color: str = "black"):
        """初始化线"""
        self.start = start
        self.end = end
        self.color = color
    
    def draw(self) -> str:
        """实现绘制方法"""
        return f"绘制从({self.start.x}, {self.start.y})到({self.end.x}, {self.end.y})的{self.color}线"
    
    def get_color(self) -> str:
        """实现获取颜色方法"""
        return self.color
    
    def length(self) -> float:
        """计算线长"""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return math.sqrt(dx**2 + dy**2)


def draw_objects(objects: List[Drawable]) -> None:
    """绘制对象列表 - 使用协议类型"""
    print("绘制对象:")
    for obj in objects:
        print(f"  {obj.draw()}")
        print(f"  颜色: {obj.get_color()}")


def protocol_demo():
    """协议演示"""
    print("\n" + "=" * 50)
    print("4. 协议 (Protocol) 演示")
    print("=" * 50)
    
    # 创建可绘制对象
    point1 = Point(1, 2, "red")
    point2 = Point(5, 6, "blue")
    line = Line(point1, point2, "green")
    
    # 使用协议类型
    drawable_objects = [point1, point2, line]
    draw_objects(drawable_objects)
    
    print(f"\n线长: {line.length():.2f}")


# ==================== 5. 多态演示 ====================

class Vehicle(ABC):
    """交通工具抽象基类"""
    
    def __init__(self, brand: str, model: str):
        """初始化交通工具"""
        self.brand = brand
        self.model = model
    
    @abstractmethod
    def start_engine(self) -> str:
        """启动引擎 - 抽象方法"""
        pass
    
    @abstractmethod
    def stop_engine(self) -> str:
        """停止引擎 - 抽象方法"""
        pass
    
    def info(self) -> str:
        """交通工具信息"""
        return f"{self.brand} {self.model}"


class Car(Vehicle):
    """汽车类"""
    
    def __init__(self, brand: str, model: str, fuel_type: str):
        """初始化汽车"""
        super().__init__(brand, model)
        self.fuel_type = fuel_type
    
    def start_engine(self) -> str:
        """启动汽车引擎"""
        return f"{self.info()} 汽车引擎启动 ({self.fuel_type})"
    
    def stop_engine(self) -> str:
        """停止汽车引擎"""
        return f"{self.info()} 汽车引擎停止"
    
    def honk(self) -> str:
        """汽车鸣笛"""
        return f"{self.info()} 嘀嘀嘀！"


class Motorcycle(Vehicle):
    """摩托车类"""
    
    def __init__(self, brand: str, model: str, engine_size: int):
        """初始化摩托车"""
        super().__init__(brand, model)
        self.engine_size = engine_size
    
    def start_engine(self) -> str:
        """启动摩托车引擎"""
        return f"{self.info()} 摩托车引擎启动 ({self.engine_size}cc)"
    
    def stop_engine(self) -> str:
        """停止摩托车引擎"""
        return f"{self.info()} 摩托车引擎停止"
    
    def wheelie(self) -> str:
        """摩托车翘头"""
        return f"{self.info()} 做翘头动作！"


class Bicycle(Vehicle):
    """自行车类"""
    
    def __init__(self, brand: str, model: str, gear_count: int):
        """初始化自行车"""
        super().__init__(brand, model)
        self.gear_count = gear_count
    
    def start_engine(self) -> str:
        """启动自行车（人力驱动）"""
        return f"{self.info()} 开始踩踏板 ({self.gear_count}速)"
    
    def stop_engine(self) -> str:
        """停止自行车"""
        return f"{self.info()} 停止踩踏板"
    
    def ring_bell(self) -> str:
        """自行车铃铛"""
        return f"{self.info()} 叮铃铃！"


def operate_vehicle(vehicle: Vehicle) -> None:
    """操作交通工具 - 多态函数"""
    print(f"操作 {vehicle.info()}:")
    print(f"  {vehicle.start_engine()}")
    
    # 检查特有方法
    if hasattr(vehicle, 'honk'):
        print(f"  {vehicle.honk()}")
    elif hasattr(vehicle, 'wheelie'):
        print(f"  {vehicle.wheelie()}")
    elif hasattr(vehicle, 'ring_bell'):
        print(f"  {vehicle.ring_bell()}")
    
    print(f"  {vehicle.stop_engine()}")


def polymorphism_demo():
    """多态演示"""
    print("\n" + "=" * 50)
    print("5. 多态演示")
    print("=" * 50)
    
    # 创建不同类型的交通工具
    vehicles = [
        Car("丰田", "凯美瑞", "汽油"),
        Motorcycle("本田", "CBR600", 600),
        Bicycle("捷安特", "ATX", 21)
    ]
    
    # 多态操作
    for vehicle in vehicles:
        operate_vehicle(vehicle)
        print()


# ==================== 6. 混入类 (Mixin) 设计模式 ====================

class TimestampMixin:
    """时间戳混入类"""
    
    def __init__(self, *args, **kwargs):
        """初始化时间戳"""
        super().__init__(*args, **kwargs)
        from datetime import datetime
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_timestamp(self) -> None:
        """更新时间戳"""
        from datetime import datetime
        self.updated_at = datetime.now()
    
    def get_age(self) -> str:
        """获取创建时间"""
        from datetime import datetime
        age = datetime.now() - self.created_at
        return f"{age.total_seconds():.2f} 秒前创建"


class SerializableMixin:
    """可序列化混入类"""
    
    def to_dict(self) -> dict:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if hasattr(value, 'isoformat'):  # datetime对象
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        return result
    
    def from_dict(self, data: dict) -> None:
        """从字典恢复"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class User(TimestampMixin, SerializableMixin):
    """用户类 - 使用多个混入类"""
    
    def __init__(self, username: str, email: str):
        """初始化用户"""
        self.username = username
        self.email = email
        super().__init__()  # 调用混入类的初始化
    
    def update_email(self, new_email: str) -> None:
        """更新邮箱"""
        self.email = new_email
        self.update_timestamp()
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"User({self.username}, {self.email})"


def mixin_demo():
    """混入类演示"""
    print("\n" + "=" * 50)
    print("6. 混入类 (Mixin) 演示")
    print("=" * 50)
    
    # 创建用户
    user = User("zhangsan", "zhangsan@example.com")
    
    print(f"用户: {user}")
    print(f"创建时间: {user.get_age()}")
    
    # 序列化
    user_dict = user.to_dict()
    print(f"序列化: {user_dict}")
    
    # 更新邮箱
    import time
    time.sleep(1)  # 等待1秒
    user.update_email("zhangsan@newdomain.com")
    
    print(f"更新后: {user}")
    print(f"创建时间: {user.get_age()}")
    print(f"更新后序列化: {user.to_dict()}")
    
    # MRO 查看
    print(f"User MRO: {[cls.__name__ for cls in User.__mro__]}")


# ==================== 7. 实际应用场景 ====================

class DatabaseConnection(ABC):
    """数据库连接抽象基类"""
    
    def __init__(self, host: str, port: int, database: str):
        """初始化数据库连接"""
        self.host = host
        self.port = port
        self.database = database
        self.connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """连接数据库"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str) -> List[dict]:
        """执行查询"""
        pass
    
    def get_connection_info(self) -> str:
        """获取连接信息"""
        status = "已连接" if self.connected else "未连接"
        return f"{self.host}:{self.port}/{self.database} ({status})"


class MySQLConnection(DatabaseConnection):
    """MySQL连接实现"""
    
    def connect(self) -> bool:
        """连接MySQL数据库"""
        print(f"连接到MySQL: {self.host}:{self.port}/{self.database}")
        self.connected = True
        return True
    
    def disconnect(self) -> bool:
        """断开MySQL连接"""
        print(f"断开MySQL连接: {self.host}:{self.port}")
        self.connected = False
        return True
    
    def execute_query(self, query: str) -> List[dict]:
        """执行MySQL查询"""
        print(f"执行MySQL查询: {query}")
        # 模拟查询结果
        return [{"id": 1, "name": "张三"}, {"id": 2, "name": "李四"}]


class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL连接实现"""
    
    def connect(self) -> bool:
        """连接PostgreSQL数据库"""
        print(f"连接到PostgreSQL: {self.host}:{self.port}/{self.database}")
        self.connected = True
        return True
    
    def disconnect(self) -> bool:
        """断开PostgreSQL连接"""
        print(f"断开PostgreSQL连接: {self.host}:{self.port}")
        self.connected = False
        return True
    
    def execute_query(self, query: str) -> List[dict]:
        """执行PostgreSQL查询"""
        print(f"执行PostgreSQL查询: {query}")
        # 模拟查询结果
        return [{"user_id": 1, "username": "admin"}, {"user_id": 2, "username": "user"}]


class DatabaseManager:
    """数据库管理器 - 使用多态"""
    
    def __init__(self):
        """初始化数据库管理器"""
        self.connections: List[DatabaseConnection] = []
    
    def add_connection(self, connection: DatabaseConnection) -> None:
        """添加数据库连接"""
        self.connections.append(connection)
    
    def connect_all(self) -> None:
        """连接所有数据库"""
        print("连接所有数据库:")
        for conn in self.connections:
            conn.connect()
            print(f"  {conn.get_connection_info()}")
    
    def execute_query_on_all(self, query: str) -> dict:
        """在所有数据库上执行查询"""
        results = {}
        for i, conn in enumerate(self.connections):
            if conn.connected:
                result = conn.execute_query(query)
                results[f"database_{i}"] = result
        return results
    
    def disconnect_all(self) -> None:
        """断开所有数据库连接"""
        print("断开所有数据库连接:")
        for conn in self.connections:
            conn.disconnect()
            print(f"  {conn.get_connection_info()}")


def practical_application_demo():
    """实际应用场景演示"""
    print("\n" + "=" * 50)
    print("7. 实际应用场景演示 - 数据库管理")
    print("=" * 50)
    
    # 创建数据库管理器
    db_manager = DatabaseManager()
    
    # 添加不同类型的数据库连接
    mysql_conn = MySQLConnection("localhost", 3306, "myapp")
    postgres_conn = PostgreSQLConnection("localhost", 5432, "myapp")
    
    db_manager.add_connection(mysql_conn)
    db_manager.add_connection(postgres_conn)
    
    # 连接所有数据库
    db_manager.connect_all()
    
    # 执行查询
    print(f"\n执行查询:")
    results = db_manager.execute_query_on_all("SELECT * FROM users")
    for db_name, result in results.items():
        print(f"  {db_name}: {result}")
    
    # 断开连接
    print()
    db_manager.disconnect_all()


# ==================== 主函数 ====================

if __name__ == "__main__":
    print("Python 继承和多态学习 - 完整演示")
    print("=" * 70)
    
    # 执行所有演示
    basic_inheritance_demo()
    multiple_inheritance_demo()
    abstract_base_class_demo()
    protocol_demo()
    polymorphism_demo()
    mixin_demo()
    practical_application_demo()
    
    print("\n" + "=" * 70)
    print("继承和多态学习完成！")
    print("=" * 70)
    
    print("\n学习要点总结:")
    print("1. 基础继承：super()调用父类方法，方法重写")
    print("2. 多重继承：Python支持多重继承，注意MRO顺序")
    print("3. 抽象基类：使用ABC定义抽象类和抽象方法")
    print("4. 协议(Protocol)：结构化子类型，类似接口")
    print("5. 多态：不同类型对象响应相同接口")
    print("6. 混入类(Mixin)：提供可重用功能的设计模式")
    print("7. 实际应用：数据库连接、图形系统等场景")
    print("8. isinstance()和issubclass()进行类型检查")
