# Weekly AI Reporter - MVP 任务清单

- [x] **设计阶段**
  - [x] 创建设计文档 (implementation_plan.md) 包含 PlantUML 图表
  - [ ] 用户审查设计

- [ ] **项目初始化**
  - [ ] 初始化 Python 项目 (virtualenv, requirements.txt)
  - [ ] 创建项目结构 (main.py, database.py, models/, routers/)

- [ ] **数据库实现**
  - [ ] 定义 SQLModel `WorkLog` 模型
  - [ ] 配置 SQLite 数据库连接

- [ ] **API 接口实现**
  - [ ] 实现 `POST /logs` (创建日志)
  - [ ] 实现 `GET /logs` (获取日志列表)
  - [ ] 实现 `POST /reports/weekly` (生成周报存根)

- [ ] **AI 集成**
  - [ ] 实现 LLM 服务 (Mock 或真实 API 调用)
  - [ ] 创建周报总结的 Prompt 模板
  - [ ] 连接 `POST /reports/weekly` 到 LLM 服务

- [ ] **验证**
  - [ ] 手动测试: 创建周一到周五的日志
  - [ ] 手动测试: 生成周报
