"""
新闻服务模块

该模块集成城市热点新闻MCP服务，提供统一的新闻数据接口。
"""

from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta
from app.adapters.city_news_mcp import CityNewsMCP
from config.config import config
from app.utils.singleton import SingletonMeta

logger = logging.getLogger(__name__)

class NewsService(metaclass=SingletonMeta):
    """
    新闻服务类（单例模式）
    """
    
    def __init__(self):
        self.mcp_client = CityNewsMCP()
        self.cache_duration = config.NEWS_CACHE_DURATION
        self.news_cache = {}
        
        logger.info("新闻服务初始化完成")
    
    def get_hot_news(self, city: str = None, limit: int = 10, use_cache: bool = True) -> Dict[str, Any]:
        """获取热点新闻"""
        try:
            cache_key = f"hot_{city or 'national'}_{limit}"
            
            if use_cache and self._is_cache_valid(cache_key):
                logger.info(f"从缓存获取热点新闻")
                return self.news_cache[cache_key]['data']
            
            result = self.mcp_client.get_hot_news(city, limit)
            
            if result.get("status") == "success":
                self.news_cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                logger.info(f"成功获取热点新闻")
                return result
            else:
                logger.error(f"获取热点新闻失败: {result.get('message')}")
                return {
                    "status": "error",
                    "message": "获取热点新闻失败"
                }
                
        except Exception as e:
            logger.error(f"获取热点新闻服务异常: {str(e)}")
            return {
                "status": "error",
                "message": f"新闻服务不可用: {str(e)}"
            }
    
    def get_news_by_category(self, category: str, limit: int = 5, use_cache: bool = True) -> Dict[str, Any]:
        """按类别获取新闻"""
        try:
            cache_key = f"category_{category}_{limit}"
            
            if use_cache and self._is_cache_valid(cache_key):
                logger.info(f"从缓存获取{category}类别新闻")
                return self.news_cache[cache_key]['data']
            
            result = self.mcp_client.get_news_by_category(category, limit)
            
            if result.get("status") == "success":
                self.news_cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                logger.info(f"成功获取{category}类别新闻")
                return result
            else:
                logger.error(f"获取{category}类别新闻失败: {result.get('message')}")
                return {
                    "status": "error",
                    "message": f"获取{category}类别新闻失败"
                }
                
        except Exception as e:
            logger.error(f"获取{category}类别新闻服务异常: {str(e)}")
            return {
                "status": "error",
                "message": f"新闻服务不可用: {str(e)}"
            }
    
    def get_daily_news_summary(self, city: str = None) -> str:
        """获取日常新闻摘要"""
        try:
            result = self.mcp_client.get_news_summary(5)
            
            if result.get("status") == "success":
                summary_data = result.get("data", {}).get("summary", [])
                
                if not summary_data:
                    return "暂无新闻数据"
                
                news_parts = []
                news_parts.append("📰 今日新闻摘要")
                news_parts.append("")
                
                for i, news in enumerate(summary_data, 1):
                    title = news.get('title', '无标题')
                    category = news.get('category', '')
                    source = news.get('source', '')
                    
                    news_line = f"{i}. 【{category}】{title}"
                    if source:
                        news_line += f" - {source}"
                    
                    news_parts.append(news_line)
                
                return "\n".join(news_parts)
            else:
                return "获取新闻摘要失败"
                
        except Exception as e:
            logger.error(f"生成新闻摘要失败: {str(e)}")
            return "新闻服务不可用"
    
    def search_news(self, keyword: str, limit: int = 10) -> Dict[str, Any]:
        """搜索新闻"""
        try:
            result = self.mcp_client.search_news(keyword, limit)
            
            if result.get("status") == "success":
                logger.info(f"成功搜索关键词'{keyword}'的新闻")
                return result
            else:
                logger.error(f"搜索新闻失败: {result.get('message')}")
                return {
                    "status": "error",
                    "message": f"搜索关键词'{keyword}'的新闻失败"
                }
                
        except Exception as e:
            logger.error(f"搜索新闻服务异常: {str(e)}")
            return {
                "status": "error",
                "message": f"新闻搜索服务不可用: {str(e)}"
            }
    
    def get_breaking_news(self, limit: int = 5) -> Dict[str, Any]:
        """获取突发新闻"""
        try:
            result = self.mcp_client.get_breaking_news(limit)
            
            if result.get("status") == "success":
                logger.info(f"成功获取突发新闻")
                return result
            else:
                logger.error(f"获取突发新闻失败: {result.get('message')}")
                return {
                    "status": "error",
                    "message": "获取突发新闻失败"
                }
                
        except Exception as e:
            logger.error(f"获取突发新闻服务异常: {str(e)}")
            return {
                "status": "error",
                "message": f"新闻服务不可用: {str(e)}"
            }
    
    def format_push_news(self, limit: int = 5) -> str:
        """格式化推送用新闻信息"""
        try:
            return self.get_daily_news_summary()
        except Exception as e:
            logger.error(f"格式化推送新闻失败: {str(e)}")
            return "新闻信息获取失败。"
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.news_cache:
            return False
        
        cache_entry = self.news_cache[key]
        cache_time = cache_entry['timestamp']
        
        return (datetime.now() - cache_time).total_seconds() < self.cache_duration
    
    def clear_cache(self):
        """清空所有缓存"""
        self.news_cache.clear()
        logger.info("已清空新闻服务缓存")
    
    def health_check(self) -> bool:
        """检查新闻服务健康状态"""
        try:
            return self.mcp_client.health_check()
        except Exception as e:
            logger.error(f"新闻服务健康检查失败: {str(e)}")
            return False

# 全局新闻服务实例
news_service = NewsService()