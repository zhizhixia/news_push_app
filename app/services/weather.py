"""
天气服务模块

该模块集成墨迹天气MCP服务，提供统一的天气数据接口。
"""

from typing import Dict, Any
import logging
from datetime import datetime, timedelta
from app.adapters.moji_weather_mcp import MojiWeatherMCP
from config.config import config

logger = logging.getLogger(__name__)

class WeatherService:
    """
    天气服务类（单例模式）
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WeatherService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self.mcp_client = MojiWeatherMCP()
        self.cache_duration = config.WEATHER_CACHE_DURATION
        self.weather_cache = {}
        self.forecast_cache = {}
        
        self._initialized = True
        logger.info("天气服务初始化完成")
    
    def get_current_weather(self, city: str, use_cache: bool = True) -> Dict[str, Any]:
        """获取指定城市的当前天气信息"""
        try:
            if use_cache and self._is_cache_valid(city, self.weather_cache):
                logger.info(f"从缓存获取{city}天气信息")
                return self.weather_cache[city]['data']
            
            result = self.mcp_client.get_current_weather(city)
            
            if result.get("status") == "success":
                self.weather_cache[city] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                logger.info(f"成功获取{city}当前天气")
                return result
            else:
                logger.error(f"获取{city}天气失败: {result.get('message')}")
                return {
                    "status": "error",
                    "message": f"获取{city}天气信息失败"
                }
                
        except Exception as e:
            logger.error(f"获取{city}天气服务异常: {str(e)}")
            return {
                "status": "error",
                "message": f"天气服务不可用: {str(e)}"
            }
    
    def get_weather_forecast(self, city: str, days: int = 7, use_cache: bool = True) -> Dict[str, Any]:
        """获取指定城市的天气预报"""
        try:
            cache_key = f"{city}_{days}d"
            
            if use_cache and self._is_cache_valid(cache_key, self.forecast_cache):
                logger.info(f"从缓存获取{city} {days}天预报")
                return self.forecast_cache[cache_key]['data']
            
            result = self.mcp_client.get_weather_forecast(city, days)
            
            if result.get("status") == "success":
                self.forecast_cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                logger.info(f"成功获取{city} {days}天天气预报")
                return result
            else:
                logger.error(f"获取{city}天气预报失败: {result.get('message')}")
                return {
                    "status": "error",
                    "message": f"获取{city}天气预报失败"
                }
                
        except Exception as e:
            logger.error(f"获取{city}天气预报服务异常: {str(e)}")
            return {
                "status": "error",
                "message": f"天气预报服务不可用: {str(e)}"
            }
    
    def get_weather_summary(self, city: str) -> str:
        """获取天气摘要（用于推送和快速查询）"""
        try:
            weather_result = self.get_current_weather(city)
            
            if weather_result.get("status") != "success":
                return f"抱歉，无法获取{city}的天气信息。"
            
            weather_data = weather_result.get("data", {})
            
            summary_parts = []
            summary_parts.append(f"🌦️ {city}天气")
            
            if 'weather' in weather_data:
                summary_parts.append(f"天气：{weather_data['weather']}")
            
            if 'temperature' in weather_data:
                summary_parts.append(f"温度：{weather_data['temperature']}°C")
            
            if 'humidity' in weather_data:
                summary_parts.append(f"湿度：{weather_data['humidity']}%")
            
            if 'wind_direction' in weather_data and 'wind_speed' in weather_data:
                summary_parts.append(f"风力：{weather_data['wind_direction']} {weather_data['wind_speed']}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"生成{city}天气摘要失败: {str(e)}")
            return f"获取{city}天气信息时出现错误。"
    
    def format_push_weather(self, city: str) -> str:
        """格式化推送用天气信息"""
        try:
            current_weather = self.get_weather_summary(city)
            forecast_result = self.get_weather_forecast(city, 2)
            
            push_content = [current_weather]
            
            if forecast_result.get("status") == "success":
                forecast_data = forecast_result.get("data", {}).get("forecast", [])
                if len(forecast_data) > 1:
                    tomorrow = forecast_data[1]
                    tomorrow_summary = f"\n🌅 明日天气：{tomorrow.get('weather', '')}，{tomorrow.get('temp_low', '')}°C ~ {tomorrow.get('temp_high', '')}°C"
                    push_content.append(tomorrow_summary)
            
            return "\n".join(push_content)
            
        except Exception as e:
            logger.error(f"格式化{city}推送天气失败: {str(e)}")
            return f"{city}天气信息获取失败。"
    
    def _is_cache_valid(self, key: str, cache_dict: Dict, cache_hours: float = None) -> bool:
        """检查缓存是否有效"""
        if key not in cache_dict:
            return False
        
        cache_entry = cache_dict[key]
        cache_time = cache_entry['timestamp']
        
        if cache_hours is None:
            cache_seconds = self.cache_duration
        else:
            cache_seconds = cache_hours * 3600
        
        return (datetime.now() - cache_time).total_seconds() < cache_seconds
    
    def clear_cache(self):
        """清空所有缓存"""
        self.weather_cache.clear()
        self.forecast_cache.clear()
        logger.info("已清空天气服务缓存")
    
    def health_check(self) -> bool:
        """检查天气服务健康状态"""
        try:
            return self.mcp_client.health_check()
        except Exception as e:
            logger.error(f"天气服务健康检查失败: {str(e)}")
            return False

# 全局天气服务实例
weather_service = WeatherService()

# 向后兼容的函数
def get_weather(city: str) -> dict:
    """向后兼容的天气查询函数"""
    return weather_service.get_current_weather(city)