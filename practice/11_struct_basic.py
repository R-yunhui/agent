def main():
    print("=" * 30)
    # 删除 list 中的指定元素
    num_list = [1, 2, 3, 4, 5, 3, 4]
    print(f"原始 list: {num_list}")
    # 1. 使用列表推导式
    """
    优点：
        简洁清晰：一行代码表达意图，符合 Pythonic 风格。
        高效：底层用 C 实现，速度通常最快。
        安全：不修改原列表，而是创建新列表，无副作用。
        函数式思维：避免状态突变，更易测试和推理。
    缺点：
        如果列表非常大（GB 级），会占用额外内存（因为创建新列表）。
        不能用于需要“就地修改”且外部有其他引用指向该列表的场景（极少见）。
    """
    num_list = [num for num in num_list if num not in [3, 4]]
    print(f"使用列表推导式删除 3 和 4 后的 list: {num_list}")

    # 2. 反向遍历列表
    """
    优点：
        就地修改：不创建新列表，节省内存。
        逻辑可靠：从后往前删，不影响前面未处理的索引。
    缺点：
        代码稍显冗长，可读性不如列表推导。
        性能略慢于列表推导（Python 层循环 vs C 层）。
        需要通过索引访问，不够“面向值”。
    """
    for i in range(len(num_list) - 1, -1, -1):
        if num_list[i] in [5]:
            del num_list[i]
    print(f"反向遍历列表删除 5 后的list: {num_list}")


if __name__ == "__main__":
    main()
