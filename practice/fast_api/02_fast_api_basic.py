"""
在设计 API 时，路径的顺序可能影响匹配结果。FastAPI 按顺序处理路由，因此你需要将固定路径放在动态路径之前，以避免冲突。
"""
from enum import Enum

from fastapi import FastAPI

app = FastAPI()

"""
如果/users/{user_id}定义在/users/me之前，访问/users/me会被误匹配为user_id="me"，导致错误行为。
•最佳实践：始终优先声明具体路径（如/users/me），再声明通用路径（如/users/{user_id}）。这确保了 API 的预期逻辑，避免潜在 bug。
"""


@app.get("/users/me")
def read_me():
    return {"username": "renyh"}


@app.get("/users/{username}")
def read_user(username: str):
    return {"username": username}


"""
枚举作为参数
FastAPI 会自动校验输入，只允许预设值，增强了 API 的可靠性。
"""


class DayEnum(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


@app.get("/days/{day}")
def get_day(day: DayEnum):
    if day == DayEnum.MONDAY:
        return {"day": day, "message": "It's Monday!"}
    elif day == DayEnum.TUESDAY:
        return {"day": day, "message": "It's Tuesday!"}
    elif day == DayEnum.WEDNESDAY:
        return {"day": day, "message": "It's Wednesday!"}
    elif day == DayEnum.THURSDAY:
        return {"day": day, "message": "It's Thursday!"}
    elif day == DayEnum.FRIDAY:
        return {"day": day, "message": "It's Friday!"}
    elif day == DayEnum.SATURDAY:
        return {"day": day, "message": "It's Saturday!"}
    elif day == DayEnum.SUNDAY:
        return {"day": day, "message": "It's Sunday!"}
    else:
        return {"day": day, "message": "Invalid day!"}


if __name__ == "__main__":
    import uvicorn

    # reload=True 开启自动重载，开发时使用
    uvicorn.run(app="02_fast_api_basic:app", host="0.0.0.0", port=8000, reload=True, workers=1)
