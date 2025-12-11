import json
from typing import Any, Dict

# ==========================================
# Python JSON 序列化与反序列化示例
# 对应 Java 中的 Jackson/Fastjson 功能
# ==========================================


# 1. 定义一个简单的类 (类似于 Java Bean)
class User:
    def __init__(self, name: str, age: int, email: str = None):
        self.name = name
        self.age = age
        self.email = email

    def __repr__(self):
        return f"User(name='{self.name}', age={self.age}, email='{self.email}')"


def main():
    # 场景 1: 基础字典 (Dict) 与 JSON 的转换
    # Python 的 dict 天然对应 JSON 对象，无需特殊处理
    print("--- 1. 基础字典转换 ---")

    data_dict = {
        "id": 1001,
        "title": "Python Practice",
        "is_active": True,
        "tags": ["json", "serialization"],
    }

    # 序列化 (Serialization): Dict -> JSON String
    # ensure_ascii=False 允许输出中文而非 Unicode 编码
    # indent=4 用于美化输出 (Pretty Print)
    json_str = json.dumps(data_dict, ensure_ascii=False, indent=4)
    print(f"JSON 字符串:\n{json_str}")

    # 反序列化 (Deserialization): JSON String -> Dict
    parsed_dict = json.loads(json_str)
    print(f"解析后的类型: {type(parsed_dict)}")
    print(f"解析后的数据: {parsed_dict['title']}")

    # 场景 2: 自定义对象 (Object) 转 JSON
    # Python 的 json 模块默认不知道如何转换自定义类，
    # 需要指定 default 参数，或者先转为 dict。
    print("\n--- 2. 自定义对象转 JSON (Object -> JSON) ---")

    user = User("张三", 25, "zhangsan@example.com")

    try:
        # 直接 dumps 会报错: TypeError: Object of type User is not JSON serializable
        print(json.dumps(user))
    except TypeError as e:
        print(f"直接序列化报错 (预期行为): {e}")

    # 方法 A: 简单对象可以使用 __dict__ 属性 (类似 Java 反射获取字段)
    # 注意: 这仅适用于简单对象，且不包含私有属性等复杂情况
    user_json = json.dumps(user, default=lambda o: o.__dict__, ensure_ascii=False)
    print(f"对象序列化结果 (使用 __dict__): {user_json}")

    # 场景 3: JSON 转自定义对象 (JSON -> Object)
    # json.loads 默认返回 dict，需要手动转为对象
    print("\n--- 3. JSON 转自定义对象 (JSON -> Object) ---")

    input_json = '{"name": "李四", "age": 30, "email": "lisi@example.com"}'

    # 步骤 1: 先解析为字典
    temp_dict = json.loads(input_json)

    # 步骤 2: 将字典转为对象
    # 方式 A: 构造函数解包 (**kwargs) - 推荐，类似 Java 的构造器传参
    user_obj = User(**temp_dict)
    print(f"反序列化后的对象: {user_obj}")
    print(f"访问属性: {user_obj.name}")


if __name__ == "__main__":
    main()
