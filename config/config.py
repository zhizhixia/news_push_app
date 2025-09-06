"""
配置管理模块

该模块负责管理应用的所有配置参数，包括：
- 阿里云百炼大模型配置
- 微信公众号配置
- MCP服务配置
- 应用基础配置
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # 阿里云百炼配置
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_MODEL: str = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")
    
    # 微信公众号配置
    WECHAT_TOKEN: str = os.getenv("WECHAT_TOKEN", "")
    WECHAT_APPID: str = os.getenv("WECHAT_APPID", "")
    WECHAT_APPSECRET: str = os.getenv("WECHAT_APPSECRET", "")
    
    # MCP服务配置
    # 注意：以下MCP服务已开通，无需额外配置
    MCP_WEATHER_SERVICE_ENABLED: bool = True  # 墨迹天气MCP服务
    MCP_NEWS_SERVICE_ENABLED: bool = True     # 城市热点新闻MCP服务
    MCP_MAP_SERVICE_ENABLED: bool = True      # 高德地图MCP服务
    
    # 应用配置
    DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "北京")
    PUSH_TIME_HOUR: int = int(os.getenv("PUSH_TIME_HOUR", "8"))
    PUSH_TIME_MINUTE: int = int(os.getenv("PUSH_TIME_MINUTE", "0"))
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # 开发环境配置
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    RELOAD: bool = os.getenv("RELOAD", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 缓存配置
    NEWS_CACHE_DURATION: int = int(os.getenv("NEWS_CACHE_DURATION", "7200"))  # 2小时
    WEATHER_CACHE_DURATION: int = int(os.getenv("WEATHER_CACHE_DURATION", "3600"))  # 1小时
    
    # 任务调度配置
    SCHEDULER_TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "Asia/Shanghai")
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置完整性"""
        required_fields = [
            cls.DASHSCOPE_API_KEY,
            cls.WECHAT_TOKEN,
            cls.WECHAT_APPID,
            cls.WECHAT_APPSECRET
        ]
        
        missing_fields = []
        if not cls.DASHSCOPE_API_KEY:
            missing_fields.append("DASHSCOPE_API_KEY")
        if not cls.WECHAT_TOKEN:
            missing_fields.append("WECHAT_TOKEN")
        if not cls.WECHAT_APPID:
            missing_fields.append("WECHAT_APPID")
        if not cls.WECHAT_APPSECRET:
            missing_fields.append("WECHAT_APPSECRET")
        
        if missing_fields:
            raise ValueError(f"缺少必要的环境变量: {', '.join(missing_fields)}")
        
        return True

# 全局配置实例
config = Config()

# 向后兼容的变量导出
DASHSCOPE_API_KEY = config.DASHSCOPE_API_KEY
WECHAT_TOKEN = config.WECHAT_TOKEN
WECHAT_APPID = config.WECHAT_APPID
WECHAT_APPSECRET = config.WECHAT_APPSECRET
DEFAULT_CITY = config.DEFAULT_CITY