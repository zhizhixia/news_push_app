"""
推送服务模块

该模块负责生成和管理定时推送内容，集成多个MCP服务。
支持的功能：
- 生成每日推送内容
- 个性化内容定制
- 多种推送格式
- 内容缓存管理
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
from app.services.weather import weather_service
from app.services.news import news_service
from app.services.llm import llm_service
from app.services.location import location_service
from config.config import config
from app.utils.singleton import SingletonMeta

logger = logging.getLogger(__name__)

class PushService(metaclass=SingletonMeta):
    """
    推送服务类（单例模式）
    
    负责生成和管理各种推送内容
    """
    
    def __init__(self):
        self.weather_service = weather_service
        self.news_service = news_service
        self.llm_service = llm_service
        self.location_service = location_service
        
        # 内容缓存
        self.push_cache = {}
        self.cache_duration = 3600  # 1小时缓存
        
        logger.info("推送服务初始化完成")
    
    def generate_daily_push_content(self, city: str = None) -> str:
        """
        生成每日推送内容
        
        Args:
            city: 城市名称，默认使用配置中的默认城市
            
        Returns:
            格式化的推送内容
        """
        try:
            if not city:
                city = config.DEFAULT_CITY
            
            # 标准化城市名
            normalized_city = self.location_service.normalize_city_name(city)
            
            # 检查缓存
            cache_key = f"daily_push_{normalized_city}"
            if self._is_cache_valid(cache_key):
                logger.info(f"从缓存获取{normalized_city}每日推送内容")
                return self.push_cache[cache_key]['content']
            
            # 生成推送内容
            push_content = self._build_daily_content(normalized_city)
            
            # 更新缓存
            self.push_cache[cache_key] = {
                'content': push_content,
                'timestamp': datetime.now()
            }
            
            logger.info(f"成功生成{normalized_city}每日推送内容")
            return push_content
            
        except Exception as e:
            logger.error(f"生成每日推送内容失败: {str(e)}")
            return self._get_fallback_content(city)
    
    def generate_weather_push(self, city: str) -> str:
        """
        生成天气推送内容
        
        Args:
            city: 城市名称
            
        Returns:
            天气推送内容
        """
        try:
            normalized_city = self.location_service.normalize_city_name(city)
            weather_content = self.weather_service.format_push_weather(normalized_city)
            
            # 添加推送头部
            push_parts = []
            push_parts.append(f"🌟 {normalized_city}天气播报")
            push_parts.append("="*20)
            push_parts.append(weather_content)
            push_parts.append("")
            push_parts.append(f"📅 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            return "\n".join(push_parts)
            
        except Exception as e:
            logger.error(f"生成天气推送失败: {str(e)}")
            return f"抱歉，无法获取{city}的天气信息。"
    
    def generate_news_push(self, limit: int = 5) -> str:
        """
        生成新闻推送内容
        
        Args:
            limit: 新闻数量限制
            
        Returns:
            新闻推送内容
        """
        try:
            news_content = self.news_service.format_push_news(limit)
            
            # 添加推送头部
            push_parts = []
            push_parts.append("📰 今日新闻精选")
            push_parts.append("="*20)
            push_parts.append(news_content)
            push_parts.append("")
            push_parts.append(f"📅 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            return "\n".join(push_parts)
            
        except Exception as e:
            logger.error(f"生成新闻推送失败: {str(e)}")
            return "抱歉，无法获取新闻信息。"
    
    def generate_personalized_push(self, user_city: str, user_preferences: Dict = None) -> str:
        """
        生成个性化推送内容
        
        Args:
            user_city: 用户城市
            user_preferences: 用户偏好设置
            
        Returns:
            个性化推送内容
        """
        try:
            normalized_city = self.location_service.normalize_city_name(user_city)
            
            # 基础内容
            content_parts = []
            
            # 个性化问候
            greeting = self._generate_personalized_greeting(normalized_city)
            content_parts.append(greeting)
            content_parts.append("")
            
            # 天气信息
            weather_content = self.weather_service.format_push_weather(normalized_city)
            content_parts.append(weather_content)
            content_parts.append("")
            
            # 新闻信息
            news_content = self.news_service.get_daily_news_summary()
            content_parts.append(news_content)
            
            # 个性化建议
            if user_preferences:
                suggestions = self._generate_personalized_suggestions(normalized_city, user_preferences)
                if suggestions:
                    content_parts.append("")
                    content_parts.append(suggestions)
            
            # 结尾
            content_parts.append("")
            content_parts.append("💝 祝您今天愉快！")
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"生成个性化推送失败: {str(e)}")
            return self.generate_daily_push_content(user_city)
    
    def _build_daily_content(self, city: str) -> str:
        """
        构建每日推送内容
        
        Args:
            city: 标准化的城市名称
            
        Returns:
            完整的每日推送内容
        """
        content_parts = []
        
        # 推送头部
        current_time = datetime.now()
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][current_time.weekday()]
        
        content_parts.append(f"🌅 早安！{city}")
        content_parts.append(f"📅 {current_time.strftime('%Y年%m月%d日')} {weekday}")
        content_parts.append("="*30)
        content_parts.append("")
        
        # 天气信息
        try:
            weather_content = self.weather_service.format_push_weather(city)
            content_parts.append(weather_content)
        except Exception as e:
            logger.error(f"获取天气内容失败: {str(e)}")
            content_parts.append(f"🌤️ {city}天气信息暂时无法获取")
        
        content_parts.append("")
        content_parts.append("―"*30)
        content_parts.append("")
        
        # 新闻信息
        try:
            news_content = self.news_service.get_daily_news_summary()
            content_parts.append(news_content)
        except Exception as e:
            logger.error(f"获取新闻内容失败: {str(e)}")
            content_parts.append("📰 新闻信息暂时无法获取")
        
        # 生活提醒
        life_tips = self._generate_daily_tips(city)
        if life_tips:
            content_parts.append("")
            content_parts.append("―"*30)
            content_parts.append("")
            content_parts.append(life_tips)
        
        # 推送尾部
        content_parts.append("")
        content_parts.append("💝 祝您今天工作顺利，心情愉快！")
        content_parts.append("")
        content_parts.append("💬 回复'帮助'查看更多功能")
        
        return "\n".join(content_parts)
    
    def _generate_personalized_greeting(self, city: str) -> str:
        """
        生成个性化问候语
        """
        try:
            current_hour = datetime.now().hour
            
            if 5 <= current_hour < 9:
                greetings = [f"🌅 早安！{city}的朋友", f"🌞 美好的一天从{city}开始"]
            elif 9 <= current_hour < 12:
                greetings = [f"☀️ 上午好！{city}", f"🌤️ {city}的上午时光"]
            elif 12 <= current_hour < 14:
                greetings = [f"🌞 中午好！{city}", f"☀️ {city}的午间问候"]
            elif 14 <= current_hour < 18:
                greetings = [f"🌤️ 下午好！{city}", f"🌞 {city}的下午时光"]
            elif 18 <= current_hour < 22:
                greetings = [f"🌆 晚上好！{city}", f"🌃 {city}的夜晚"]
            else:
                greetings = [f"🌙 深夜好！{city}", f"🌃 {city}的深夜问候"]
            
            # 随机选择一个问候语
            import random
            return random.choice(greetings)
            
        except Exception as e:
            logger.error(f"生成个性化问候语失败: {str(e)}")
            return f"🌟 您好！{city}"
    
    def _generate_daily_tips(self, city: str) -> str:
        """
        生成每日生活提醒
        """
        try:
            # 获取天气信息生成相关建议
            weather_result = self.weather_service.get_current_weather(city)
            
            if weather_result.get("status") == "success":
                weather_data = weather_result.get("data", {})
                weather_type = weather_data.get("weather", "")
                temperature = weather_data.get("temperature", 20)
                
                tips = []
                tips.append("💡 生活小贴士：")
                
                # 根据天气给出建议
                if "雨" in weather_type:
                    tips.append("☔ 今日有雨，记得带伞出门")
                elif "晴" in weather_type:
                    tips.append("☀️ 阳光明媚，适合户外活动")
                elif "雪" in weather_type:
                    tips.append("❄️ 下雪天气，注意保暖和路滑")
                elif "风" in weather_type:
                    tips.append("💨 风力较大，外出注意安全")
                
                # 根据温度给出建议
                if isinstance(temperature, (int, float)):
                    if temperature < 5:
                        tips.append("🧥 气温较低，注意添衣保暖")
                    elif temperature > 30:
                        tips.append("🌡️ 气温较高，注意防暑降温")
                    elif 5 <= temperature <= 15:
                        tips.append("👔 气温适中，建议穿薄外套")
                
                # 添加通用健康提醒
                weekday = datetime.now().weekday()
                if weekday == 0:  # 周一
                    tips.append("💪 新的一周开始，保持积极心态")
                elif weekday == 4:  # 周五
                    tips.append("🎉 周末将至，适当放松心情")
                
                return "\n".join(tips)
            
            return "💡 记得保持良好的作息习惯，注意身体健康"
            
        except Exception as e:
            logger.error(f"生成每日提醒失败: {str(e)}")
            return ""
    
    def _generate_personalized_suggestions(self, city: str, preferences: Dict) -> str:
        """
        根据用户偏好生成个性化建议
        """
        try:
            suggestions = []
            suggestions.append("🎯 个性化推荐：")
            
            # 根据偏好生成建议（这里是示例逻辑）
            if preferences.get("interests"):
                interests = preferences["interests"]
                if "运动" in interests:
                    suggestions.append("🏃 今天适合进行户外运动")
                if "读书" in interests:
                    suggestions.append("📚 推荐您今天安排一些阅读时间")
                if "美食" in interests:
                    suggestions.append("🍽️ 不妨尝试一些当地特色美食")
            
            return "\n".join(suggestions) if len(suggestions) > 1 else ""
            
        except Exception as e:
            logger.error(f"生成个性化建议失败: {str(e)}")
            return ""
    
    def _get_fallback_content(self, city: str) -> str:
        """
        获取备用推送内容
        """
        fallback_content = [
            f"🌟 {city or config.DEFAULT_CITY}每日资讯",
            "="*20,
            "",
            "📱 由于网络原因，暂时无法获取最新的天气和新闻信息。",
            '🔄 请稍后重试或发送「天气」、「新闻」获取最新信息。',
            "",
            "💝 祝您今天愉快！",
            "",
            "💬 回复'帮助'查看更多功能"
        ]
        
        return "\n".join(fallback_content)
    
    def _is_cache_valid(self, key: str) -> bool:
        """
        检查缓存是否有效
        """
        if key not in self.push_cache:
            return False
        
        cache_entry = self.push_cache[key]
        cache_time = cache_entry['timestamp']
        
        return (datetime.now() - cache_time).total_seconds() < self.cache_duration
    
    def clear_cache(self):
        """
        清空推送内容缓存
        """
        self.push_cache.clear()
        logger.info("已清空推送服务缓存")
    
    def health_check(self) -> bool:
        """
        检查推送服务健康状态
        
        Returns:
            服务是否可用
        """
        try:
            # 检查依赖服务
            weather_ok = self.weather_service.health_check()
            news_ok = self.news_service.health_check()
            llm_ok = self.llm_service.health_check()
            location_ok = self.location_service.health_check()
            
            return weather_ok and news_ok and llm_ok and location_ok
        except Exception as e:
            logger.error(f"推送服务健康检查失败: {str(e)}")
            return False

# 全局推送服务实例
push_service = PushService()