# AI智能测试平台

> 一站式 AI 驱动全链路测试效能平台，基于大模型实现需求解析→用例生成→接口测试→自动化脚本→缺陷分析→质量报告全流程自动化。

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue3 + TypeScript + Element Plus + ECharts |
| 后端 | Python + FastAPI + SQLAlchemy 2.0 |
| 数据库 | MySQL 8.0 + Redis 7 |
| AI | OpenAI 兼容接口（支持通义千问/文心一言/讯飞星火/自定义） |
| 部署 | Docker Compose / K8s |

## 功能模块

- 🏠 **质量看板** - 项目数据统计、缺陷趋势、通过率图表
- ⚙️ **平台管理** - 用户/角色/项目/迭代/LLM模型配置
- 📋 **AI需求&用例** - 需求文档上传解析、AI一键生成测试用例
- 🔌 **AI接口测试** - Swagger导入、接口调试、AI生成接口用例
- 🤖 **AI自动化** - AI生成Pytest/Playwright脚本、任务调度
- 🐛 **AI缺陷管理** - 缺陷提报、AI分类/根因分析/修复建议
- 🎲 **测试数据** - 随机数据生成、业务数据模板、数据脱敏
- 📊 **质量报告** - AI自动生成专业测试报告

## 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <repo-url>
cd ai-test-platform

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入您的 LLM API Key

# 3. 启动所有服务
docker-compose up -d

# 4. 访问
# 前端: http://localhost
# API文档: http://localhost:8000/api/docs
```

### 方式二：本地开发

**后端**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env

# 初始化数据库（需要先创建MySQL数据库 ai_test_platform）
alembic upgrade head

# 启动后端
uvicorn main:app --reload --port 8000
```

**前端**
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

## 配置LLM

在 `backend/.env` 或平台管理→AI模型配置中配置：

```env
# OpenAI
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 通义千问
OPENAI_API_KEY=your-dashscope-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-turbo
```

## 项目结构

```
ai-test-platform/
├── frontend/                # Vue3 前端
│   ├── src/
│   │   ├── api/             # API请求层
│   │   ├── components/      # 公共组件 (Layout)
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia状态管理
│   │   ├── types/           # TypeScript类型
│   │   └── views/           # 页面组件
│   └── Dockerfile
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/          # API路由 (11个模块)
│   │   ├── core/            # 配置/安全/依赖注入
│   │   ├── db/              # 数据库连接
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── schemas/         # Pydantic 验证模式
│   │   └── services/        # AI服务层 (LLM客户端/Prompt管理)
│   ├── alembic/             # 数据库迁移
│   └── Dockerfile
└── docker-compose.yml
```

## API 文档

启动后访问: http://localhost:8000/api/docs

主要接口：
- `POST /api/v1/auth/login` - 登录
- `POST /api/v1/testcases/ai-generate` - AI生成测试用例
- `POST /api/v1/apitest/cases/ai-generate` - AI生成接口用例
- `POST /api/v1/automation/scripts/ai-generate` - AI生成自动化脚本
- `POST /api/v1/defects/ai-analyze` - AI缺陷分析
- `POST /api/v1/reports/ai-report` - AI生成测试报告
- `POST /api/v1/apitest/debug` - 接口在线调试

## 默认账号

| 账号 | 密码 | 权限 |
|------|------|------|
| admin | admin123 | 超级管理员 |

> ⚠️ 请在生产环境中修改默认密码和 SECRET_KEY
