---
trigger: always_on
---

# Antigravity Rules

## 1. 语言与沟通 (Language & Communication)
- **语言**: 必须使用**中文**回答所有问题。
- **风格**: 保持专业、简洁且具有教学性。解释代码时，不仅要说明“是什么”，还要解释“为什么”，辅助我学习 Python。

## 2. 环境与系统 (Environment & System)
- **操作系统**: **Windows**。
  - 文件路径使用反斜杠 `\` 或 `os.path.join`。
  - 命令行指令默认使用 **PowerShell** 格式。
- **Python 环境**: 假设使用 Python 3.x。

## 3. 代码规范 (Code Standards)
- **真实性**: **绝对不要**胡编乱造不存在的包、模块或 API。如果不确定，请先查证或告知不确定。
- **风格**: 遵循 PEP 8 规范。
- **类型提示**: 尽量使用 Type Hints (e.g., `def func(a: int) -> str:`)，这有助于学习和代码健壮性。
- **注释**: 关键逻辑和复杂代码段必须包含中文注释。
- **错误处理**: 编写健壮的代码，包含适当的 try-except 块，不要忽略异常。

## 4. 项目管理 (Project Management)
- **文件创建**:
  - **README**: 除非我明确要求，否则**不要**主动创建或更新 `README.md` 文件。
  - **位置**: 代码文件应保存在当前工作区的合适子目录下，避免直接散落在根目录（除非是配置文件）。
- **依赖管理**: 如果引入了新的第三方库，请提示我更新 [requirements.txt](cci:7://file:///d:/ryh/personal/python/agent/requirements.txt:0:0-0:0) 或安装命令，但不要自动修改 [requirements.txt](cci:7://file:///d:/ryh/personal/python/agent/requirements.txt:0:0-0:0) 除非我确认。

## 5. 交互习惯 (Interaction)
- **简洁性**: 如果只是简单的代码修改，直接给出代码即可，不需要过多的寒暄。
- **确认**: 在执行破坏性操作（如删除文件、重写大量代码）前，请先简要告知计划。