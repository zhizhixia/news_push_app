"""
阿里百炼大语言模型服务

该模块封装阿里云百炼（DashScope）大语言模型的调用逻辑，
提供统一的AI对话和内容生成接口。

功能包括：
- 智能对话响应
- 用户意图识别
- 新闻内容摘要
- 天气信息格式化
- 上下文管理
"""

import dashscope
from dashscope import Generation
from dashscope.api_entities.dashscope_response import GenerationResponse
from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime
from config.config import config
from app.utils.singleton import SingletonMeta

logger = logging.getLogger(__name__)

# 设置API Key
dashscope.api_key = config.DASHSCOPE_API_KEY

class UserIntent:
    """用户意图类"""
    def __init__(self, intent_type: str, confidence: float = 0.0, entities: Dict = None):
        self.intent_type = intent_type
        self.confidence = confidence
        self.entities = entities or {}
        self.timestamp = datetime.now()

class LLMService(metaclass=SingletonMeta):
    """
    阿里百炼大语言模型服务类（单例模式）
    """
    
    def __init__(self):
        self.model = config.DASHSCOPE_MODEL
        self.max_tokens = 2000
        self.temperature = 0.7
        self.top_p = 0.9
        
        # 对话历史管理
        self.conversation_history = {}
        self.max_history_length = 10
        
        # 意图识别模板
        self.intent_patterns = {
            "update_location": [
                r"更改城市\s*(.+)",
                r"设置位置\s*(.+)",
                r"我在\s*(.+)",
                r"切换到\s*(.+)",
                r"定位\s*(.+)"
            ],
            "query_forecast": [
                r"明天天气",
                r"未来\d+天",
                r"天气预报",
                r"预报"
            ],
            "query_weather": [
                r"天气",
                r"气温",
                r"温度",
                r"下雨",
                r"晴天",
                r"阴天"
            ],
            "query_news": [
                r"新闻",
                r"资讯",
                r"头条",
                r"热点",
                r"消息"
            ],
            "help": [
                r"帮助",
                r"使用说明",
                r"怎么用",
                r"功能"
            ]
        }
        logger.info("LLM服务初始化完成")
    
    def generate_response(self, prompt: str, context: str = None, user_id: str = None) -> str:
        """
        生成AI响应
        
        Args:
            prompt: 用户输入的提示
            context: 上下文信息
            user_id: 用户ID（用于管理对话历史）
            
        Returns:
            AI生成的响应文本
        """
        try:
            # 构建完整的prompt
            full_prompt = self._build_prompt(prompt, context, user_id)
            
            # 调用DashScope API
            response = Generation.call(
                model=self.model,
                prompt=full_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                # 仅保留必要的停止词，避免正常输出被过度截断
                stop=["用户："]
            )
            
            if response.status_code == 200:
                generated_text = response.output.text.strip()
                
                # 更新对话历史
                if user_id:
                    self._update_conversation_history(user_id, prompt, generated_text)
                
                logger.info(f"成功生成AI响应，用户: {user_id}")
                return generated_text
            else:
                error_msg = f"API调用失败: {getattr(response, 'code', response.status_code)} - {getattr(response, 'message', '')}"
                logger.error(error_msg)
                return "抱歉，我现在无法处理您的请求，请稍后再试。"
                
        except Exception as e:
            logger.error(f"生成AI响应失败: {str(e)}")
            return "抱歉，我遇到了一些技术问题，请稍后再试。"
    
    def analyze_user_intent(self, message: str) -> UserIntent:
        """
        分析用户意图
        
        Args:
            message: 用户消息
            
        Returns:
            识别出的用户意图
        """
        try:
            import re
            
            message = message.strip().lower()
            
            # 规则匹配
            for intent_type, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, message, re.IGNORECASE)
                    if match:
                        entities = {}
                        if match.groups():
                            entities['extracted_text'] = match.group(1).strip()
                        
                        return UserIntent(
                            intent_type=intent_type,
                            confidence=0.9,
                            entities=entities
                        )
            
            # AI辅助意图识别
            intent_prompt = f"""
请分析以下用户消息的意图，从以下选项中选择最合适的一个：
1. update_location - 更新位置/城市
2. query_weather - 查询天气
3. query_news - 查询新闻
4. query_forecast - 查询天气预报
5. help - 寻求帮助
6. general_chat - 一般对话

用户消息: {message}

请只返回意图类型，不要其他内容。
"""
            
            response = Generation.call(
                model=self.model,
                prompt=intent_prompt,
                max_tokens=50,
                temperature=0.1
            )
            
            if response.status_code == 200:
                intent_type = response.output.text.strip().lower()
                if intent_type in self.intent_patterns or intent_type == "general_chat":
                    return UserIntent(
                        intent_type=intent_type,
                        confidence=0.7
                    )
            
            # 默认返回一般对话意图
            return UserIntent(intent_type="general_chat", confidence=0.5)
            
        except Exception as e:
            logger.error(f"意图识别失败: {str(e)}")
            return UserIntent(intent_type="general_chat", confidence=0.3)
    
    def format_news_summary(self, news_data: List[Dict]) -> str:
        """
        格式化新闻摘要
        
        Args:
            news_data: 新闻数据列表
            
        Returns:
            格式化后的新闻摘要文本
        """
        try:
            if not news_data:
                return "暂无新闻数据"
            
            # 构建新闻摘要prompt
            news_text = "\n".join([
                f"{i+1}. {news.get('title', '')} - {news.get('summary', '')}"
                for i, news in enumerate(news_data[:5])
            ])
            
            format_prompt = f"""
请将以下新闻信息整理成简洁易读的摘要格式：

{news_text}

要求：
1. 保持新闻的主要信息
2. 语言简洁明了
3. 按重要性排序
4. 每条新闻一行
5. 总字数控制在200字以内
"""
            
            response = Generation.call(
                model=self.model,
                prompt=format_prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            if response.status_code == 200:
                formatted_summary = response.output.text.strip()
                logger.info("成功格式化新闻摘要")
                return formatted_summary
            else:
                # 回退到简单格式
                return self._simple_news_format(news_data)
                
        except Exception as e:
            logger.error(f"格式化新闻摘要失败: {str(e)}")
            return self._simple_news_format(news_data)
    
    def format_weather_info(self, weather_data: Dict, city: str) -> str:
        """
        格式化天气信息
        
        Args:
            weather_data: 天气数据
            city: 城市名称
            
        Returns:
            格式化后的天气信息文本
        """
        try:
            if not weather_data or weather_data.get("status") != "success":
                return f"抱歉，无法获取{city}的天气信息"
            
            weather_info = weather_data.get("data", {})
            
            format_prompt = f"""
请将以下天气数据格式化成用户友好的文本：

城市：{city}
天气数据：{json.dumps(weather_info, ensure_ascii=False, indent=2)}

要求：
1. 语言自然流畅
2. 包含主要天气信息
3. 适合微信消息发送
4. 控制在100字以内
"""
            
            response = Generation.call(
                model=self.model,
                prompt=format_prompt,
                max_tokens=300,
                temperature=0.3
            )
            
            if response.status_code == 200:
                formatted_weather = response.output.text.strip()
                logger.info(f"成功格式化{city}天气信息")
                return formatted_weather
            else:
                # 回退到简单格式
                return self._simple_weather_format(weather_info, city)
                
        except Exception as e:
            logger.error(f"格式化天气信息失败: {str(e)}")
            return self._simple_weather_format(weather_data.get("data", {}), city)
    
    def _build_prompt(self, user_input: str, context: str = None, user_id: str = None) -> str:
        """
        构建完整的prompt
        """
        system_prompt = """
你是一个智能的新闻天气助手，具有以下特点：
1. 友好、专业、乐于助人
2. 能够提供准确的新闻和天气信息
3. 回答简洁明了，适合微信对话
4. 支持位置更新和个性化服务

请根据用户的问题提供有帮助的回答。
"""
        
        # 获取对话历史
        history = self._get_conversation_history(user_id) if user_id else []
        
        # 构建完整prompt
        prompt_parts = [system_prompt]
        
        if context:
            prompt_parts.append(f"上下文信息：{context}")
        
        if history:
            prompt_parts.append("对话历史：")
            for entry in history[-3:]:  # 只保留最近3轮对话
                prompt_parts.append(f"用户：{entry['user']}")
                prompt_parts.append(f"助手：{entry['assistant']}")
        
        prompt_parts.append(f"用户：{user_input}")
        prompt_parts.append("助手：")
        
        return "\n".join(prompt_parts)
    
    def _update_conversation_history(self, user_id: str, user_input: str, assistant_response: str):
        """
        更新对话历史
        """
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "user": user_input,
            "assistant": assistant_response,
            "timestamp": datetime.now()
        })
        
        # 限制历史长度
        if len(self.conversation_history[user_id]) > self.max_history_length:
            self.conversation_history[user_id] = self.conversation_history[user_id][-self.max_history_length:]
    
    def _get_conversation_history(self, user_id: str) -> List[Dict]:
        """
        获取对话历史
        """
        return self.conversation_history.get(user_id, [])
    
    def _simple_news_format(self, news_data: List[Dict]) -> str:
        """
        简单的新闻格式化（回退方案）
        """
        if not news_data:
            return "暂无新闻数据"
        
        formatted_news = []
        for i, news in enumerate(news_data[:5], 1):
            title = news.get('title', '无标题')
            source = news.get('source', '未知来源')
            formatted_news.append(f"{i}. {title} - {source}")
        
        return "\n".join(formatted_news)
    
    def _simple_weather_format(self, weather_info: Dict, city: str) -> str:
        """
        简单的天气格式化（回退方案）
        """
        if not weather_info:
            return f"无法获取{city}的天气信息"
        
        temp = weather_info.get('temperature', '未知')
        weather = weather_info.get('weather', '未知')
        humidity = weather_info.get('humidity', '未知')
        
        return f"{city}天气：{weather}，温度{temp}°C，湿度{humidity}%"
    
    def clear_conversation_history(self, user_id: str):
        """
        清除用户对话历史
        """
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            logger.info(f"已清除用户{user_id}的对话历史")
    
    def health_check(self) -> bool:
        """
        检查LLM服务健康状态
        
        Returns:
            服务是否可用
        """
        try:
            test_response = Generation.call(
                model=self.model,
                prompt="请回复'正常'",
                max_tokens=10
            )
            return test_response.status_code == 200
        except Exception as e:
            logger.error(f"LLM服务健康检查失败: {str(e)}")
            return False

# 全局LLM服务实例
llm_service = LLMService()