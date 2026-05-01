# News Push App · 新闻天气推送服务

[English](#english) · [中文](#中文)

---

<div id="english">

## English

A FastAPI-based intelligent news & weather push service integrated with Alibaba DashScope LLM and WeChat Official Account.

### Features

- **Scheduled Daily Push** — Pushes weather forecasts and curated news summaries to all subscribed users daily (default 08:00 AM, configurable).
- **Intelligent User Interaction** — Natural language chat via WeChat Official Account, powered by DashScope LLM.
- **Personalized Settings** — Users can update their city, preferences, and notification settings through WeChat commands.
- **Intent Recognition** — Built-in regex + LLM hybrid intent detection for weather queries, news queries, and location updates.
- **Service Health Monitoring** — Periodic health checks and weekly usage reports via APScheduler.

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | FastAPI |
| LLM | Alibaba DashScope (qwen-turbo by default) |
| Task Scheduler | APScheduler (AsyncIOScheduler) |
| WeChat SDK | wechatpy |
| Data Validation | Pydantic |
| Config | python-dotenv |

### Project Structure

```
news_push_app/
├── app/
│   ├── adapters/          # External service adapters (weather, news, maps)
│   │   ├── moji_weather_mcp.py
│   │   ├── city_news_mcp.py
│   │   └── gaode_map_mcp.py
│   ├── api/               # HTTP route handlers
│   │   └── wechat.py      # GET/POST /api/wechat
│   ├── models/            # Pydantic data models
│   │   └── user.py        # User, LocationInfo, UserPreferences
│   ├── services/          # Core business logic (all singletons)
│   │   ├── interaction.py # User message dispatch + response generation
│   │   ├── llm.py         # DashScope LLM integration
│   │   ├── weather.py     # Weather service
│   │   ├── news.py        # News service
│   │   ├── location.py    # Location/geocoding service
│   │   ├── push_service.py # Push content assembly
│   │   └── scheduler.py   # APScheduler job definitions
│   ├── utils/             # Shared utilities
│   │   └── singleton.py   # SingletonMeta metaclass
│   └── main.py            # FastAPI app entry point
├── config/
│   └── config.py          # All configuration via .env
├── tests/
│   └── test_services.py   # 34 unit tests (unittest)
├── Dockerfile
├── requirements.txt
├── .env.example
└── DEPLOY.md
```

### Data Flow

```
WeChat User Message
    │
    ▼
GET/POST /api/wechat        (app/api/wechat.py)
    │
    ▼
handle_user_interaction()   (app/services/interaction.py)
    │
    ├── llm_service.analyze_user_intent()   → UserIntent
    ├── weather_service                     → WeatherService
    ├── news_service                        → NewsService
    └── location_service                    → LocationService
            │
            ▼
    Adapters (mock/stub data)               → Replace for production
```

### Quick Start

```bash
# 1. Clone and set up
git clone <your-repo-url>
cd news_push_app
cp .env.example .env          # Edit with real API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

For WeChat verification to work, expose port 8000 via ngrok or similar tunnel:
```bash
ngrok http 8000
```

Then configure your WeChat Official Account backend URL as `https://<your-ngrok-domain>/api/wechat`.

### Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DASHSCOPE_API_KEY` | — | **Yes** | Alibaba DashScope API key |
| `DASHSCOPE_MODEL` | `qwen-turbo` | No | DashScope model name |
| `WECHAT_TOKEN` | — | Prod only | WeChat verification token |
| `WECHAT_APPID` | — | Prod only | WeChat Official Account AppID |
| `WECHAT_APPSECRET` | — | Prod only | WeChat Official Account AppSecret |
| `DEFAULT_CITY` | `北京` | No | Default city for new users |
| `PUSH_TIME_HOUR` | `8` | No | Daily push hour (0-23) |
| `PUSH_TIME_MINUTE` | `0` | No | Daily push minute (0-59) |
| `LOG_LEVEL` | `INFO` | No | Logging level |
| `DEBUG` | `false` | No | Relaxes config validation when `true` |
| `SCHEDULER_TIMEZONE` | `Asia/Shanghai` | No | Timezone for scheduled jobs |

> **Note**: In `DEBUG=true` mode, only `DASHSCOPE_API_KEY` is required. Production mode (`DEBUG=false`) additionally requires all WeChat variables.

### Running Tests

```bash
# Preferred — unittest runner
python -m unittest discover tests -v

# Alternative — pytest
pytest tests/ -v
```

> Tests call the adapter stubs directly. The LLM service test (`test_generate_response`) hits the real DashScope API unless mocked via `@patch`.

### Scheduled Tasks

Defined in `app/services/scheduler.py`:

| Job | Schedule | Description |
|-----|----------|-------------|
| Daily Push | `PUSH_TIME_HOUR:PUSH_TIME_MINUTE` | Sends weather + news to all users |
| News Cache Refresh | Every 2 hours | Pre-loads hot news by category |
| Weather Cache Refresh | Every 1 hour | Pre-loads weather for all user cities |
| Health Check | Every 30 minutes | Checks all service health |
| Cache Cleanup | Daily 02:00 | Clears expired cache entries |
| Weekly Report | Monday 09:00 | Generates usage statistics |

### Docker

```bash
docker build -t news-push-app .
docker run -d --name news-push-app -p 8000:8000 --env-file .env news-push-app
```

Health check endpoint: `GET /health`

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/wechat` | WeChat server verification (signature check) |
| `POST` | `/api/wechat` | Handle WeChat user messages |
| `GET` | `/health` | System health + scheduler status |
| `GET` | `/` | System info |

### Architecture Notes

- **Singleton services**: All 6 service classes use `SingletonMeta` (defined in `app/utils/singleton.py`). Always import the module-level instance:
  ```python
  from app.services.weather import weather_service   # ✅ correct
  ws = WeatherService()                                 # ❌ discouraged
  ```

- **Error handling contract**: Three-layer pattern:
  - **Data layer** (adapters + service `get_*` methods): return `{"status": "success"/"error", ...}` dicts
  - **Display layer** (service `format_*` methods + `interaction.py`): convert dicts to user-facing strings
  - **Infrastructure layer** (scheduler): log and suppress exceptions

- **Adapter stubs**: All three adapters (`MojiWeatherMCP`, `CityNewsMCP`, `GaodeMapMCP`) currently return hardcoded mock data. The `base_url = "mcp://..."` lines are placeholders. Replace adapter implementations when connecting to real APIs.

- **In-memory storage**: User data is stored in a global `user_db` dict (`app/models/user.py`) — no database. All data is lost on restart. This is by design for the template. Swap in a database (PostgreSQL, Redis, etc.) for production.

### User Commands

| Command | Example | Description |
|---------|---------|-------------|
| `帮助` / `help` | — | Show help message |
| `更改城市 <city>` | `更改城市 上海` | Update user city |
| `天气` / `今日天气` | — | Get current weather |
| `天气预报` / `明天天气` | — | Get weather forecast |
| `新闻` / `今日新闻` | — | Get latest news |
| Any text | — | Natural language chat with LLM |

### License

MIT — see [LICENSE](LICENSE).

---

</div>

<div id="中文">

## 中文

基于 FastAPI + 阿里百炼 DashScope + 微信公众号的智能新闻天气推送服务。

### 功能特性

- **定时推送** — 每日定时（默认早 8:00）向所有关注用户推送天气预报与新闻摘要。
- **智能交互** — 用户通过微信公众号发送消息，由 DashScope 大模型进行自然语言理解和回复。
- **个性化设置** — 支持「更改城市」「我的设置」等指令，自动适配用户位置和偏好。
- **意图识别** — 内置正则 + LLM 混合意图检测，准确区分天气查询、新闻查询、位置更新等意图。
- **服务监控** — 定时健康检查 + 每周运营报告。

### 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| 大模型 | 阿里百炼 DashScope（默认 qwen-turbo） |
| 任务调度 | APScheduler (AsyncIOScheduler) |
| 微信 SDK | wechatpy |
| 数据校验 | Pydantic |
| 配置管理 | python-dotenv |

### 项目结构

```
news_push_app/
├── app/
│   ├── adapters/          # 外部服务适配器（天气 / 新闻 / 地图）
│   │   ├── moji_weather_mcp.py
│   │   ├── city_news_mcp.py
│   │   └── gaode_map_mcp.py
│   ├── api/               # HTTP 路由
│   │   └── wechat.py      # GET/POST /api/wechat
│   ├── models/            # Pydantic 数据模型
│   │   └── user.py        # User / LocationInfo / UserPreferences
│   ├── services/          # 核心业务逻辑（全部单例）
│   │   ├── interaction.py # 用户消息分发 + 响应生成
│   │   ├── llm.py         # DashScope 大模型服务
│   │   ├── weather.py     # 天气服务
│   │   ├── news.py        # 新闻服务
│   │   ├── location.py    # 位置 / 地理编码服务
│   │   ├── push_service.py # 推送内容拼装
│   │   └── scheduler.py   # APScheduler 定时任务
│   ├── utils/             # 共享工具
│   │   └── singleton.py   # SingletonMeta 元类
│   └── main.py            # FastAPI 应用入口
├── config/
│   └── config.py          # 所有配置通过 .env 加载
├── tests/
│   └── test_services.py   # 34 条单元测试 (unittest)
├── Dockerfile
├── requirements.txt
├── .env.example
└── DEPLOY.md
```

### 数据流

```
微信用户消息
    │
    ▼
GET/POST /api/wechat        (app/api/wechat.py)
    │
    ▼
handle_user_interaction()   (app/services/interaction.py)
    │
    ├── llm_service.analyze_user_intent()   → UserIntent
    ├── weather_service                     → WeatherService
    ├── news_service                        → NewsService
    └── location_service                    → LocationService
            │
            ▼
    Adapters（当前为模拟数据）              → 生产环境需替换
```

### 快速开始

```bash
# 1. 克隆并配置
git clone <your-repo-url>
cd news_push_app
cp .env.example .env          # 编辑填入真实 API Key

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

微信验证需要公网 URL，可使用 ngrok 将本地 8000 端口暴露出去：
```bash
ngrok http 8000
```

然后在微信公众平台后台将服务器 URL 配置为 `https://<your-ngrok-domain>/api/wechat`。

### 环境变量

| 变量 | 默认值 | 必需 | 说明 |
|------|--------|------|------|
| `DASHSCOPE_API_KEY` | — | **是** | 阿里百炼 API Key |
| `DASHSCOPE_MODEL` | `qwen-turbo` | 否 | 大模型名称 |
| `WECHAT_TOKEN` | — | 生产环境 | 微信 Token |
| `WECHAT_APPID` | — | 生产环境 | 微信公众号 AppID |
| `WECHAT_APPSECRET` | — | 生产环境 | 微信公众号 AppSecret |
| `DEFAULT_CITY` | `北京` | 否 | 新用户默认城市 |
| `PUSH_TIME_HOUR` | `8` | 否 | 每日推送小时 (0-23) |
| `PUSH_TIME_MINUTE` | `0` | 否 | 每日推送分钟 (0-59) |
| `LOG_LEVEL` | `INFO` | 否 | 日志级别 |
| `DEBUG` | `false` | 否 | `true` 时放宽配置校验 |
| `SCHEDULER_TIMEZONE` | `Asia/Shanghai` | 否 | 定时任务时区 |

> **注意**: `DEBUG=true` 模式下仅校验 `DASHSCOPE_API_KEY`；生产模式 (`DEBUG=false`) 还需微信全套配置。

### 运行测试

```bash
# 推荐方式 — unittest
python -m unittest discover tests -v

# 备选 — pytest
pytest tests/ -v
```

> 测试直接调用适配器模拟数据，不需要 mock。LLM 服务测试 (`test_generate_response`) 会请求真实 DashScope API，除非加 `@patch` 装饰器。

### 定时任务

定义于 `app/services/scheduler.py`：

| 任务 | 周期 | 说明 |
|------|------|------|
| 每日推送 | `PUSH_TIME_HOUR:PUSH_TIME_MINUTE` | 向全体用户推送天气+新闻 |
| 新闻缓存刷新 | 每 2 小时 | 按类别预加载热门新闻 |
| 天气缓存刷新 | 每 1 小时 | 按用户城市预加载天气 |
| 健康检查 | 每 30 分钟 | 检查各服务可用性 |
| 缓存清理 | 每日 02:00 | 清理过期缓存 |
| 每周报告 | 周一 09:00 | 生成使用统计 |

### Docker 部署

```bash
docker build -t news-push-app .
docker run -d --name news-push-app -p 8000:8000 --env-file .env news-push-app
```

健康检查端点：`GET /health`

### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/wechat` | 微信服务器验证（签名校验） |
| `POST` | `/api/wechat` | 处理微信用户消息 |
| `GET` | `/health` | 系统健康状态 + 调度器状态 |
| `GET` | `/` | 系统信息 |

### 架构说明

- **单例服务**: 6 个 Service 类全部使用 `SingletonMeta` 元类（定义在 `app/utils/singleton.py`），统一通过模块级实例导入：
  ```python
  from app.services.weather import weather_service   # ✅ 正确
  ws = WeatherService()                                 # ❌ 不推荐
  ```

- **错误处理契约**: 三层模式：
  - **数据层**（适配器 + Service 的 `get_*` 方法）：返回 `{"status": "success"/"error", ...}` 字典
  - **展示层**（Service 的 `format_*` 方法 + `interaction.py`）：将字典转为用户可见文本
  - **基础设施层**（scheduler）：捕获异常并记录日志

- **适配器均为模拟数据**: 当前三个适配器（`MojiWeatherMCP`、`CityNewsMCP`、`GaodeMapMCP`）返回硬编码的模拟数据。`base_url = "mcp://..."` 行仅为占位标识，接入真实 API 时需替换适配器实现。

- **内存存储**: 用户数据存储在全局字典 `user_db`（`app/models/user.py`），无数据库持久化，重启即丢失。此为模板设计，生产环境需替换为数据库（PostgreSQL / Redis 等）。

### 用户交互命令

| 命令 | 示例 | 说明 |
|------|------|------|
| `帮助` / `help` | — | 显示帮助信息 |
| `更改城市 <城市名>` | `更改城市 上海` | 更新用户城市 |
| `天气` / `今日天气` | — | 获取当前天气 |
| `天气预报` / `明天天气` | — | 获取多日预报 |
| `新闻` / `今日新闻` | — | 获取新闻摘要 |
| 任意文本 | — | 与大模型自由对话 |

### 许可证

MIT — 详见 [LICENSE](LICENSE)。

</div>
