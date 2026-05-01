"""
用户交互处理服务

该模块负责处理用户与系统的交互，包括：
- 意图识别
- 响应生成
- 上下文管理
- 多服务集成

# 错误处理约定

本代码库采用分层错误处理模式：

**数据层（适配器 + 服务 get/fetch 方法）** → 返回 `{"status": "success"/"error", ...}` 字典
  - 成功: `{"status": "success", "data": {...}}`
  - 失败: `{"status": "error", "message": "..."}`
  - 示例: weather_service.get_current_weather(), news_service.get_hot_news()

**展示层（服务 format/summary 方法 + 本模块）** → 返回用户可读的 `str`
  - 负责将数据层字典转换为面向用户的文本消息
  - 在数据层返回错误字典时生成友好的中文提示语
  - 示例: weather_service.get_weather_summary(), generate_weather_response()

**基础设施层（scheduler.py）** → 使用异常捕获（except Exception），直接记录日志

**本模块是展示层与数据层的核心桥梁**:
  - 调用数据层 get/fetch 方法获取 `{"status": ...}` 字典
  - 检查 `result.get("status")` 判断成功/失败
  - 成功时格式化为用户消息，失败时返回 `"抱歉，..."`
  - 所有公开方法返回类型均为 `str`（面向微信用户的文本消息）

**不要在数据层方法中返回裸字符串作为错误信息** — 这是展示层的职责。
"""

from typing import Dict, Any, Optional
import logging
import re
from app.services.llm import llm_service, UserIntent
from app.services.weather import weather_service
from app.services.news import news_service
from app.services.location import location_service
from app.models.user import get_user, update_user_city
from config.config import config

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    响应生成器，集成MCP服务
    """
    
    def __init__(self):
        self.weather_service = weather_service
        self.news_service = news_service
        self.location_service = location_service
        self.llm_service = llm_service

    def generate_weather_response(self, city: str, detailed: bool = False) -> str:
        """
        生成天气响应
        
        Args:
            city: 城市名称
            detailed: 是否返回详细信息
            
        Returns:
            天气响应文本
        """
        try:
            # 使用位置服务标准化城市名
            normalized_city = self.location_service.normalize_city_name(city)
            
            if detailed:
                # 详细天气预报
                forecast_text = self.weather_service.get_detailed_forecast(normalized_city, 3)
                return forecast_text
            else:
                # 简要天气信息
                summary_text = self.weather_service.get_weather_summary(normalized_city)
                return summary_text
                
        except Exception as e:
            logger.error(f"生成天气响应失败: {str(e)}")
            return f"抱歉，无法获取{city}的天气信息"

    def generate_news_response(self, category: str = None, city: str = None) -> str:
        """
        生成新闻响应
        
        Args:
            category: 新闻类别
            city: 城市名称
            
        Returns:
            新闻响应文本
        """
        try:
            if category:
                result = self.news_service.get_news_by_category(category, 5)
                if result.get("status") == "success":
                    news_data = result.get("data", {}).get("news", [])
                    return self._format_news_list(news_data, f"{category}类别新闻")
                else:
                    return f"抱歉，无法获取{category}类别的新闻"
            elif city:
                result = self.news_service.get_hot_news(city, 5)
                if result.get("status") == "success":
                    news_data = result.get("data", {}).get("news", [])
                    return self._format_news_list(news_data, f"{city}热点新闻")
                else:
                    return f"抱歉，无法获取{city}的新闻"
            else:
                return self.news_service.get_daily_news_summary()
                
        except Exception as e:
            logger.error(f"生成新闻响应失败: {str(e)}")
            return "抱歉，无法获取新闻信息"
    
    def generate_location_update_response(self, user_id: str, location: str) -> str:
        """
        处理位置更新
        
        Args:
            user_id: 用户ID
            location: 位置信息
            
        Returns:
            位置更新响应文本
        """
        try:
            # 处理位置更新
            location_result = self.location_service.process_location_update(location)
            
            if location_result.get("status") == "success":
                location_data = location_result.get("data", {})
                normalized_city = location_data.get("normalized_city")
                confirmation_message = location_data.get("confirmation_message")
                
                # 更新用户位置
                update_user_city(user_id, normalized_city)
                
                # 获取当前天气作为确认
                weather_info = self.weather_service.get_weather_summary(normalized_city)
                
                response_parts = []
                response_parts.append(confirmation_message)
                response_parts.append("")
                response_parts.append("🎆 为您提供当前天气信息：")
                response_parts.append(weather_info)
                
                return "\n".join(response_parts)
            else:
                error_message = location_result.get("message", "位置更新失败")
                return error_message
                
        except Exception as e:
            logger.error(f"处理位置更新失败: {str(e)}")
            return f"抱歉，位置更新失败：{str(e)}"
    
    def _format_news_list(self, news_data: list, title: str) -> str:
        """
        格式化新闻列表
        """
        if not news_data:
            return f"暂无{title}数据"
        
        news_parts = []
        news_parts.append(f"📰 {title}")
        news_parts.append("")
        
        for i, news in enumerate(news_data[:5], 1):
            title = news.get('title', '无标题')
            source = news.get('source', '')
            
            news_line = f"{i}. {title}"
            if source:
                news_line += f" - {source}"
            
            news_parts.append(news_line)
        
        return "\n".join(news_parts)

# 全局响应生成器实例
response_generator = ResponseGenerator()

# 帮助信息
HELP_MESSAGE = """
🤖 欢迎使用智能新闻天气助手！

📍 您可以使用以下功能：

1️⃣ 更改城市：
   • "更改城市 上海"
   • "设置位置 北京"
   • "我在深圳"

2️⃣ 查询天气：
   • "天气"
   • "天气预报"
   • "明天天气"

3️⃣ 查询新闻：
   • "今日新闻"
   • "新闻头条"
   • "热点资讯"

4️⃣ 日常对话：
   • 直接与我对话，询问任何问题

📢 每日早上8点会自动推送天气和新闻信息

输入 "帮助" 可以随时查看此帮助信息
"""

def handle_user_interaction(openid: str, message: str) -> str:
    """
    处理用户交互的主函数
    
    Args:
        openid: 微信用户唯一标识
        message: 用户消息
        
    Returns:
        系统响应文本
    """
    try:
        user = get_user(openid)
        
        # 帮助信息
        if message.strip().lower() in ["帮助", "help", "使用说明", "功能"]:
            return HELP_MESSAGE
        
        # 使用LLM进行意图识别
        user_intent = llm_service.analyze_user_intent(message)
        intent_type = user_intent.intent_type
        
        logger.info(f"用户{openid}消息: {message}, 识别意图: {intent_type}")
        
        # 根据意图类型处理
        if intent_type == "update_location":
            # 位置更新 - 信任LLM服务已提取的实体
            location = user_intent.entities.get('extracted_text')
            if not location:
                return "请指定城市名称，例如：更改城市 深圳"
            
            return response_generator.generate_location_update_response(openid, location)
        
        elif intent_type == "query_weather":
            # 天气查询
            return response_generator.generate_weather_response(user.city)
        
        elif intent_type == "query_news":
            # 新闻查询
            return response_generator.generate_news_response()
        
        elif intent_type == "query_forecast":
            # 天气预报
            return response_generator.generate_weather_response(user.city, detailed=True)
        
        else:
            # 一般对话，使用LLM处理
            context = f"用户所在城市：{user.city}"
            return llm_service.generate_response(message, context, openid)
    
    except Exception as e:
        logger.error(f"处理用户交互失败: {str(e)}")
        return "抱歉，我遇到了一些技术问题，请稍后再试"