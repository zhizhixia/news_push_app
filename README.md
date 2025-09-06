# 基于阿里百炼和微信服务号的MCP新闻推送应用

## 1. 项目简介

本项目是一个基于MCP（Model-View-Controller-Presenter）架构的本地新闻、天气及国内外重要新闻实时推送应用。它通过集成阿里百炼大模型，实现了智能对话和信息处理，并通过微信服务号为用户提供个性化的新闻和天气信息推送服务。

## 2. 主要功能

- **定时新闻推送**: 每天定时（默认早上8点）向所有关注用户推送最新的新闻摘要和天气预报。
- **智能用户交互**: 用户可以通过微信服务号与阿里百炼大模型进行自然语言交互，获取更详细的信息或执行特定操作。
- **个性化设置**: 用户可以随时通过向服务号发送指令（如“更改城市 [城市名]”）来更新自己的地理位置，从而接收到更精准的天气信息。
- **微信集成**: 无缝集成微信服务号，支持消息的接收、处理和回复。

## 3. 技术架构

- **Web框架**: FastAPI
- **大语言模型**: 阿里百炼（DashScope）
- **消息调度**: APScheduler
- **微信SDK**: wechatpy
- **数据获取**: 通过第三方API（如极速数据）获取新闻和天气信息。

## 4. 环境配置与安装

### 4.1. 克隆项目

```bash
git clone <your-repo-url>
cd news_push_app
```

### 4.2. 安装依赖

```bash
pip install -r requirements.txt
```

### 4.3. 配置环境变量

在项目根目录下创建一个 `.env` 文件，并根据 `config/config.py` 中的定义，填入以下配置信息：

```
DASHSCOPE_API_KEY="your_dashscope_api_key"
WECHAT_TOKEN="your_wechat_token"
WECHAT_APPID="your_wechat_appid"
WECHAT_APPSECRET="your_wechat_appsecret"
NEWS_API_KEY="your_news_api_key"
WEATHER_API_KEY="your_weather_api_key"
```

**注意**: 
- `WECHAT_TOKEN` 需要与您在微信公众平台后台设置的Token保持一致。
- `WECHAT_APPID` 和 `WECHAT_APPSECRET` 是您服务号的唯一凭证。
- `DASHSCOPE_API_KEY` 是您在阿里百炼平台上创建的应用的API Key。
- `NEWS_API_KEY` 和 `WEATHER_API_KEY` 来自您选择的第三方数据提供商。

## 5. 运行与部署

### 5.1. 本地运行

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

应用启动后，您需要使用内网穿透工具（如 ngrok）将本地的 `8000` 端口暴露到公网，以便微信服务器能够访问您的API。

### 5.2. 微信服务号配置

1. 登录微信公众平台，进入您的服务号后台。
2. 在“开发” -> “基本配置”页面，找到“服务器配置”部分。
3. 点击“修改配置”，并填写以下信息：
   - **URL**: `http://<your-ngrok-domain>/api/wechat`
   - **Token**: 与您在 `.env` 文件中配置的 `WECHAT_TOKEN` 一致。
   - **EncodingAESKey**: 随机生成即可。
   - **消息加解密方式**: 选择“明文模式”。
4. 点击“提交”并“启用”服务器配置。

## 6. 测试

### 6.1. 单元测试

您可以在 `tests` 目录下编写单元测试用例。例如，创建一个 `test_services.py` 文件：

```python
import unittest
from app.services.push_service import get_push_content

class TestServices(unittest.TestCase):
    def test_get_push_content(self):
        # 注意：此测试会真实调用API，请确保API Key有效
        content = get_push_content("北京")
        self.assertIn("北京今日天气", content)
        self.assertIn("今日新闻摘要", content)

if __name__ == '__main__':
    unittest.main()
```

运行测试：

```bash
python -m unittest discover tests
```

### 6.2. 微信交互测试

- 关注您的微信服务号。
- 发送“帮助”查看可用指令。
- 发送“更改城市 上海”来更新您的位置。
- 发送“今日新闻”或“天气预报”来获取实时信息。
- 直接输入任何文本，与阿里百炼大模型进行对话。

## 7. MCP架构说明

本应用基于MCP（Model-View-Controller-Presenter）架构设计，采用模块化和服务化的方式组织代码：

### 7.1. 架构组件

- **适配器层（Adapters）**: 封装外部MCP服务的API调用
  - `MojiWeatherMCP`: 墨迹天气服务适配器
  - `CityNewsMCP`: 城市新闻服务适配器
  - `GaodeMapMCP`: 高德地图服务适配器

- **服务层（Services）**: 实现核心业务逻辑
  - `LLMService`: 阿里百炼大模型服务
  - `WeatherService`: 天气信息服务
  - `NewsService`: 新闻信息服务
  - `LocationService`: 位置管理服务
  - `InteractionService`: 用户交互处理
  - `PushService`: 推送内容生成
  - `SchedulerService`: 任务调度管理

### 7.2. 数据流架构

```
微信用户 → 微信API → 交互服务 → 意图识别（LLM） → 业务服务 → MCP适配器 → 外部API
         ←         ←         ←                ←         ←          ←
```

## 8. 用户交互命令

系统支持以下用户交互命令：

### 8.1. 基础命令

- `帮助` 或 `help`: 显示帮助信息
- `更改城市 [城市名]`: 更新用户所在城市
- `我的设置`: 查看当前用户设置
- `今日天气`: 获取当前城市天气信息
- `今日新闻`: 获取最新新闻摘要

### 8.2. 高级交互

- **自然语言对话**: 直接发送任何文本，与阿里百炼大模型进行智能对话
- **智能意图识别**: 系统能理解用户的复杂需求并提供相应服务
- **上下文理解**: 支持多轮对话和上下文记忆

## 9. API文档

### 9.1. 微信回调接口

```
POST /api/wechat
```

处理微信公众号消息推送。

### 9.2. 健康检查接口

```
GET /health
```

返回系统健康状态和各MCP服务状态。

## 10. 部署指南

### 10.1. 生产环境部署

推荐使用Docker进行部署：

```bash
# 构建镜像
docker build -t news-push-app .

# 运行容器
docker run -d --name news-push-app \
  -p 8000:8000 \
  --env-file .env \
  news-push-app
```

### 10.2. 常见问题

**Q**: 微信服务器配置验证失败？
**A**: 检查Token配置和URL可访问性，确保防火墙允许微信服务器访问。

**Q**: 第三方API调用失败？
**A**: 检查API Key配置和网络连接，查看详细错误日志。

## 11. 许可证

本项目采用 MIT 许可证 - 详细信息请查看 [LICENSE](LICENSE) 文件。