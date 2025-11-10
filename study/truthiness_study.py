"""
Python 判空逻辑详解 - Truthiness（真值测试）
与 Java 的对比学习
"""


def demo_basic_truthiness():
    """
    Python 的 Truthiness 概念
    在 Python 中，所有对象都有一个布尔值（真或假）
    """
    print("=" * 60)
    print("1. Python 的 Truthiness 基础概念")
    print("=" * 60)
    
    # 在 Python 中，以下值被认为是 False（假值）：
    false_values = [
        None,           # 空值
        False,          # 布尔假
        0,              # 数字零（0, 0.0, 0j）
        "",             # 空字符串
        '',             # 空字符串
        [],             # 空列表
        (),             # 空元组
        {},             # 空字典
        set(),          # 空集合
    ]
    
    print("\n以下值在 Python 中被认为是 False：")
    for value in false_values:
        print(f"  {repr(value):15} -> bool({repr(value)}) = {bool(value)}")
    
    print("\n所有其他值都被认为是 True")


def demo_string_check():
    """
    字符串判空 - Python vs Java
    """
    print("\n" + "=" * 60)
    print("2. 字符串判空")
    print("=" * 60)
    
    # Python 风格（推荐）
    print("\n【Python 推荐风格】")
    text1 = ""
    text2 = "Hello"
    text3 = None
    
    # 直接判断 - Pythonic 方式
    if not text1:
        print(f"  text1 = {repr(text1)} -> 是空的")
    
    if text2:
        print(f"  text2 = {repr(text2)} -> 不是空的")
    
    # 判断 None
    if text3 is None:
        print(f"  text3 = {repr(text3)} -> 是 None")
    
    print("\n【Java 风格对比】")
    print("  // Java 中的做法：")
    print('  if (text == null || text.isEmpty()) { ... }')
    print('  if (text == null || text.equals("")) { ... }')
    print('  if (text == null || text.length() == 0) { ... }')
    
    print("\n【Python 中不同的判空方式】")
    empty_str = ""
    
    # 方式1：直接判断（最 Pythonic）
    if not empty_str:
        print("  方式1: if not empty_str - ✓ 推荐")
    
    # 方式2：显式比较（不推荐）
    if empty_str == "":
        print("  方式2: if empty_str == '' - 可以，但不够 Pythonic")
    
    # 方式3：检查长度（不推荐）
    if len(empty_str) == 0:
        print("  方式3: if len(empty_str) == 0 - 不推荐，多此一举")
    
    print("\n【处理可能为 None 的字符串】")
    text_or_none = None
    
    # 错误做法（会报错）：
    # if not text_or_none:  # 这个可以工作，因为 None 也是 False
    
    # 推荐做法1：先判断 None
    if text_or_none is None or not text_or_none:
        print("  text_or_none 是 None 或空字符串")
    
    # 推荐做法2：使用 or 提供默认值
    safe_text = text_or_none or ""
    print(f"  使用 or 提供默认值: {repr(safe_text)}")


def demo_list_check():
    """
    列表/集合判空 - Python vs Java
    """
    print("\n" + "=" * 60)
    print("3. 列表/集合判空")
    print("=" * 60)
    
    # Python 风格
    print("\n【Python 推荐风格】")
    empty_list = []
    filled_list = [1, 2, 3]
    none_list = None
    
    # 直接判断（推荐）
    if not empty_list:
        print(f"  empty_list = {empty_list} -> 是空的")
    
    if filled_list:
        print(f"  filled_list = {filled_list} -> 不是空的")
    
    # 判断 None
    if none_list is None:
        print(f"  none_list = {none_list} -> 是 None")
    
    print("\n【Java 风格对比】")
    print("  // Java 中的做法：")
    print('  if (list == null || list.isEmpty()) { ... }')
    print('  if (list == null || list.size() == 0) { ... }')
    
    print("\n【Python 中不同的判空方式】")
    my_list = []
    
    # 方式1：直接判断（最 Pythonic）
    if not my_list:
        print("  方式1: if not my_list - ✓ 推荐")
    
    # 方式2：检查长度（不推荐）
    if len(my_list) == 0:
        print("  方式2: if len(my_list) == 0 - 不推荐")
    
    # 方式3：与空列表比较（不推荐）
    if my_list == []:
        print("  方式3: if my_list == [] - 不推荐")
    
    print("\n【不同集合类型的判空】")
    empty_dict = {}
    empty_set = set()
    empty_tuple = ()
    
    if not empty_dict:
        print(f"  空字典 {{}} -> False")
    if not empty_set:
        print(f"  空集合 set() -> False")
    if not empty_tuple:
        print(f"  空元组 () -> False")


def demo_object_check():
    """
    对象判空 - Python vs Java
    """
    print("\n" + "=" * 60)
    print("4. 对象判空（None vs null）")
    print("=" * 60)
    
    print("\n【Python 的 None】")
    obj = None
    
    # 推荐方式：使用 is（检查身份）
    if obj is None:
        print("  obj is None - ✓ 推荐（检查身份）")
    
    # 不推荐方式：使用 ==
    if obj == None:
        print("  obj == None - 不推荐（可能被重载）")
    
    print("\n【Java 风格对比】")
    print("  // Java 中的做法：")
    print('  if (obj == null) { ... }')
    print('  if (obj != null) { ... }')
    
    print("\n【is vs ==】")
    print("  is  -> 检查是否是同一个对象（身份检查）")
    print("  ==  -> 检查值是否相等（可以被 __eq__ 重载）")
    
    # 示例
    a = [1, 2, 3]
    b = [1, 2, 3]
    c = a
    
    print(f"\n  a = {a}")
    print(f"  b = {b}")
    print(f"  c = a")
    print(f"  a == b: {a == b}  (值相等)")
    print(f"  a is b: {a is b}  (不是同一个对象)")
    print(f"  a is c: {a is c}  (是同一个对象)")


def demo_number_check():
    """
    数字判空/判零
    """
    print("\n" + "=" * 60)
    print("5. 数字判零")
    print("=" * 60)
    
    zero = 0
    zero_float = 0.0
    one = 1
    
    print("\n【数字的真值】")
    print(f"  bool(0) = {bool(zero)}")
    print(f"  bool(0.0) = {bool(zero_float)}")
    print(f"  bool(1) = {bool(one)}")
    
    print("\n【注意事项】")
    print("  如果你需要区分 0 和 None，不能只用 if not x")
    
    value = 0
    if not value:
        print(f"  value = {value} -> 判断为 False（但实际是 0，不是 None）")
    
    # 正确做法
    if value is None:
        print("  value 是 None")
    elif value == 0:
        print("  value 是 0")


def demo_custom_class():
    """
    自定义类的真值行为
    """
    print("\n" + "=" * 60)
    print("6. 自定义类的真值行为")
    print("=" * 60)
    
    print("\n【默认行为】")
    
    class Person:
        def __init__(self, name):
            self.name = name
    
    person = Person("Alice")
    print(f"  默认情况下，所有对象实例都是 True: bool(person) = {bool(person)}")
    
    print("\n【自定义 __bool__ 方法】")
    
    class SmartList:
        def __init__(self, items):
            self.items = items
        
        def __bool__(self):
            """定义对象的真值"""
            return len(self.items) > 0
        
        def __len__(self):
            """如果没有 __bool__，会使用 __len__"""
            return len(self.items)
    
    empty_smart = SmartList([])
    filled_smart = SmartList([1, 2, 3])
    
    print(f"  empty_smart: bool() = {bool(empty_smart)}, len() = {len(empty_smart)}")
    print(f"  filled_smart: bool() = {bool(filled_smart)}, len() = {len(filled_smart)}")
    
    if not empty_smart:
        print("  empty_smart 被判断为 False")
    
    if filled_smart:
        print("  filled_smart 被判断为 True")


def demo_best_practices():
    """
    最佳实践总结
    """
    print("\n" + "=" * 60)
    print("7. 最佳实践总结")
    print("=" * 60)
    
    practices = [
        ("字符串判空", "if not s:", "简洁且 Pythonic"),
        ("列表判空", "if not lst:", "简洁且 Pythonic"),
        ("字典判空", "if not d:", "简洁且 Pythonic"),
        ("判断 None", "if x is None:", "使用 is，不是 =="),
        ("判断非 None", "if x is not None:", "使用 is not"),
        ("区分 0 和 None", "if x is None:", "显式检查 None"),
        ("提供默认值", "x = value or default", "利用短路求值"),
    ]
    
    print("\n推荐的判空方式：")
    print("-" * 60)
    for situation, code, note in practices:
        print(f"  {situation:12} -> {code:20} # {note}")
    
    print("\n" + "-" * 60)
    print("为什么 Python 这样设计？")
    print("-" * 60)
    print("""
  1. 简洁性：减少样板代码，让代码更易读
  2. 一致性：所有"空"的概念都被视为 False
  3. Pythonic：符合 Python 的设计哲学
  4. 灵活性：可以通过 __bool__ 自定义真值行为
  
  Java 的设计更注重类型安全和显式性，
  而 Python 更注重简洁性和表达力。
    """)


def demo_common_patterns():
    """
    常见使用模式
    """
    print("\n" + "=" * 60)
    print("8. 常见使用模式")
    print("=" * 60)
    
    print("\n【模式1：提供默认值】")
    name = ""
    display_name = name or "Anonymous"
    print(f"  name = {repr(name)}")
    print(f"  display_name = name or 'Anonymous' -> {repr(display_name)}")
    
    print("\n【模式2：条件赋值】")
    data = None
    result = data if data is not None else []
    print(f"  data = {data}")
    print(f"  result = data if data is not None else [] -> {result}")
    
    print("\n【模式3：链式 or】")
    option1 = None
    option2 = ""
    option3 = "Valid"
    final = option1 or option2 or option3 or "Default"
    print(f"  option1={repr(option1)}, option2={repr(option2)}, option3={repr(option3)}")
    print(f"  final = option1 or option2 or option3 or 'Default' -> {repr(final)}")
    
    print("\n【模式4：安全的链式调用】")
    user = {"profile": {"name": "Alice"}}
    # 传统方式
    name = None
    if user and "profile" in user and "name" in user["profile"]:
        name = user["profile"]["name"]
    print(f"  传统方式获取嵌套值: {repr(name)}")
    
    # 使用 get 方法
    name2 = user.get("profile", {}).get("name")
    print(f"  使用 get 方法: {repr(name2)}")
    
    print("\n【模式5：过滤空值】")
    items = ["apple", "", "banana", None, "cherry", ""]
    filtered = [item for item in items if item]
    print(f"  原始列表: {items}")
    print(f"  过滤后: {filtered}")


def demo_pitfalls():
    """
    常见陷阱
    """
    print("\n" + "=" * 60)
    print("9. 常见陷阱 ⚠️")
    print("=" * 60)
    
    print("\n【陷阱1：0 和 None 的混淆】")
    count = 0
    if not count:
        print(f"  count = {count} -> 被判断为 False（但可能是有效值 0）")
    
    print("  正确做法：")
    if count is None:
        print("  count 是 None")
    else:
        print(f"  count 是 {count}（可能是 0）")
    
    print("\n【陷阱2：空字符串和 None 的混淆】")
    text = ""
    if not text:
        print(f"  text = {repr(text)} -> 被判断为 False（空字符串还是 None？）")
    
    print("  如果需要区分，应该：")
    if text is None:
        print("  text 是 None")
    elif text == "":
        print("  text 是空字符串")
    
    print("\n【陷阱3：使用 == None 而不是 is None】")
    print("  错误: if x == None")
    print("  正确: if x is None")
    print("  原因: __eq__ 方法可能被重载，导致意外行为")
    
    print("\n【陷阱4：误用 or 提供默认值】")
    # 问题：如果 value 是 0 或 False，会被替换
    value = 0
    result = value or 10
    print(f"  value = {value}, result = value or 10 -> {result}")
    print("  问题：我们想要 0，但得到了 10")
    
    print("  正确做法：")
    result2 = value if value is not None else 10
    print(f"  result = value if value is not None else 10 -> {result2}")


# 运行所有示例
if __name__ == "__main__":
    demo_basic_truthiness()
    demo_string_check()
    demo_list_check()
    demo_object_check()
    demo_number_check()
    demo_custom_class()
    demo_best_practices()
    demo_common_patterns()
    demo_pitfalls()
    
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print("""
Python 的判空哲学：
1. 简洁优于复杂（Simple is better than complex）
2. 使用 "if not x:" 而不是 "if x == None or x == ''"
3. 使用 "is None" 而不是 "== None"
4. 理解真值测试的规则，但也要注意边界情况
5. 当需要区分 0/False 和 None 时，显式检查

Java vs Python：
- Java: 显式、类型安全、防御性编程
- Python: 简洁、动态、鸭子类型
    """)

