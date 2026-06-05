# AI 测试用例智能生成平台

基于大语言模型的企业级测试用例智能生成平台，覆盖需求解析 → AI 用例生成 → 用例管理 → 导出的完整流程。

## 功能亮点

- **多模态需求解析**：支持 PDF/Word/Excel/Markdown/TXT 上传，AI 自动提取结构化需求点
- **AI 智能生成**：基于等价类、边界值、场景法等经典测试方法，生成功能/接口/单元测试用例
- **多模型支持**：OpenAI GPT、Claude、通义千问、智谱 GLM、DeepSeek，灵活切换
- **用例全生命周期**：用例库管理、版本记录、优先级筛选、状态流转
- **多格式导出**：Excel（带样式）/ Markdown / CSV
- **评分反馈**：对 AI 生成结果进行 1-5 星评分，持续优化模型效果

## 技术架构

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue 3 + TypeScript + Element Plus + Pinia + Vite |
| 后端 | Python FastAPI + SQLAlchemy + SQLite |
| AI层 | OpenAI SDK + Anthropic SDK（兼容 OpenAI 格式的供应商统一接入） |
| 认证 | JWT (python-jose + bcrypt) |
| 文档解析 | python-docx / PyPDF2 / openpyxl / pandas |

## 快速启动

### 环境要求

- Python 3.9+
- Node.js 18+

### Windows 一键启动

```bat
start.bat
```

说明：若默认端口 8000 或 5173 已被占用，脚本会自动选择附近的可用端口，并在启动完成后输出实际访问地址。

Windows 停止服务：

```bat
stop.bat
```

### Linux/macOS 一键启动

```bash
chmod +x start.sh && ./start.sh
```

说明：若默认端口 8000 或 5173 已被占用，脚本会自动选择附近的可用端口，并在启动完成后输出实际访问地址。

Linux/macOS 停止服务：

```bash
chmod +x stop.sh && ./stop.sh
```

### 手动启动

**后端：**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # 然后填入 AI API Key
uvicorn app.main:app --reload --port 8000
```

**前端：**
```bash
cd frontend
npm install --cache /tmp/npm-cache
npm run dev
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:5173 |
| 后端 API | http://localhost:8000/api/v1 |
| Swagger 文档 | http://localhost:8000/docs |

**默认账号：** `admin` / `Admin@123`（首次启动自动创建）

## 配置 AI 模型

1. 打开平台 → 左侧菜单**模型设置**
2. 点击**添加模型配置**，选择供应商并填入 API Key
3. 点击**连通性测试**验证配置
4. 设为默认后，即可在智能生成页面使用

### 支持的供应商

| 供应商 | 环境变量 | 推荐模型 |
|--------|----------|----------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o |
| Anthropic | `ANTHROPIC_API_KEY` | claude-3-5-sonnet-20241022 |
| 通义千问 | `TONGYI_API_KEY` | qwen-max |
| 智谱 GLM | `ZHIPU_API_KEY` | glm-4 |
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-chat |

也可直接在平台设置页面配置，无需修改配置文件。

## 使用流程

```
1. 登录 → 创建项目
2. 需求管理 → 上传文档或输入需求文本 → 等待 AI 解析
3. 智能生成 → 选择需求来源 → 配置生成参数 → 点击生成
4. 用例库 → 查看/编辑生成结果 → 对用例评分 → 导出
```

## Docker 部署

```bash
# 配置 .env 文件
cp backend/.env.example backend/.env

# 一键启动
docker compose up -d
```

## 项目结构

```
AITestPlatform/
├── backend/                  # Python FastAPI 后端
│   ├── app/
│   │   ├── api/             # 路由层 (auth/projects/requirements/cases/models)
│   │   ├── core/            # 核心配置 (config/database/security)
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── schemas/         # Pydantic 请求/响应 Schema
│   │   ├── services/        # 业务逻辑 (AI适配器/文档解析/导出)
│   │   └── main.py          # 应用入口
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # Vue 3 前端
│   └── src/
│       ├── api/             # HTTP 客户端 & API 封装
│       ├── stores/          # Pinia 状态管理
│       ├── views/           # 页面组件
│       └── router/          # 路由配置
├── start.bat                 # Windows 启动脚本
├── start.sh                  # Linux/macOS 启动脚本
└── docker-compose.yml
```
