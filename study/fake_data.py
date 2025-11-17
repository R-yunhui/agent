# 使用 fake 包生成随机数据
from faker import Faker
from faker.providers import BaseProvider

import pandas as pd
import os

# 设置 locale 为中文
fake = Faker(
    locale="zh_CN",
)


def main():
    # 生成随机姓名
    name = fake.name()
    print(f"随机姓名: {name}")

    # 生成随机手机号
    phone = fake.phone_number()
    print(f"随机手机号: {phone}")

    # 生成随机邮箱
    email = fake.email()
    print(f"随机邮箱: {email}")

    # 生成随机地址
    address = fake.address()
    print(f"随机地址: {address}")


# 自定义学号提供者
class StudentIDProvider(BaseProvider):
    def student_id(self):
        year = self.random_int(min=2020, max=2024)  # 入学年份
        major_code = self.numerify(text="##")  # 2位专业代码
        seq = self.numerify(text="###")  # 3位序号
        return f"{year}{major_code}{seq}"


def create_csv():
    # 注册自定义学号提供者（复用前文的StudentIDProvider）
    fake.add_provider(StudentIDProvider)
    students = []
    for _ in range(50):
        chinese = fake.random_int(min=60, max=100)
        math = fake.random_int(min=60, max=100)
        english = fake.random_int(min=60, max=100)
        total = chinese + math + english

        # 判定等级
        if total >= 270:
            grade = "A"
        elif total >= 240:
            grade = "B"
        elif total >= 210:
            grade = "C"
        else:
            grade = "D"

        students.append({
            "学号": fake.student_id(),
            "姓名": fake.name(),
            "语文": chinese,
            "数学": math,
            "英语": english,
            "总分": total,
            "等级": grade
        })
    # 保存为CSV用于教学
    os.makedirs(os.path.join(os.getcwd(), "data"), exist_ok=True)
    pd.DataFrame(students).to_csv(os.path.join(os.getcwd(), "data", "students.csv"), index=False, encoding="utf-8-sig")
    print("教学用成绩表生成完成，共50名学生")


if __name__ == "__main__":
    # main()
    create_csv()
