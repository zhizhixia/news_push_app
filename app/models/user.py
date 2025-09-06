"""
用户数据模型

该模块定义用户数据结构和管理方法，支持：
- 用户基本信息管理
- 位置信息管理
- 个性化偏好设置
- 用户行为统计
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging
from config.config import config

logger = logging.getLogger(__name__)

class NotificationTime(str, Enum):
    """推送时间选项"""
    MORNING_8 = "08:00"
    MORNING_9 = "09:00"
    NOON_12 = "12:00"
    EVENING_18 = "18:00"
    EVENING_20 = "20:00"

class NewsCategory(str, Enum):
    """新闻类别选项"""
    HEADLINES = "headlines"
    POLITICS = "politics"
    ECONOMY = "economy"
    TECHNOLOGY = "technology"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    SOCIETY = "society"
    INTERNATIONAL = "international"
    MILITARY = "military"
    HEALTH = "health"

class UserPreferences(BaseModel):
    """用户偏好设置模型"""
    
    # 推送设置
    notification_enabled: bool = True
    notification_time: NotificationTime = NotificationTime.MORNING_8
    
    # 新闻偏好
    preferred_news_categories: List[NewsCategory] = Field(
        default=[NewsCategory.HEADLINES, NewsCategory.TECHNOLOGY, NewsCategory.SOCIETY]
    )
    news_count_limit: int = Field(default=5, ge=1, le=10)
    
    # 天气偏好
    weather_detailed: bool = False  # 是否显示详细天气信息
    weather_forecast_days: int = Field(default=3, ge=1, le=7)
    show_weather_indices: bool = True  # 是否显示生活指数
    
    # 交互偏好
    ai_chat_enabled: bool = True
    response_language: str = "zh"  # zh, en
    
    # 其他偏好
    interests: List[str] = Field(default=[])  # 用户兴趣标签
    timezone: str = Field(default="Asia/Shanghai")

class LocationInfo(BaseModel):
    """位置信息模型"""
    
    city: str
    province: Optional[str] = None
    country: str = "中国"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # 位置更新信息
    last_updated: datetime = Field(default_factory=datetime.now)
    update_source: str = "manual"  # manual, auto, gps
    
    # 位置验证状态
    is_verified: bool = False
    verification_method: Optional[str] = None

class UserStats(BaseModel):
    """用户统计信息模型"""
    
    # 基本统计
    total_interactions: int = 0
    total_push_received: int = 0
    last_active_time: Optional[datetime] = None
    
    # 交互统计
    weather_queries: int = 0
    news_queries: int = 0
    location_updates: int = 0
    ai_chat_count: int = 0
    
    # 时间统计
    first_interaction: Optional[datetime] = None
    registration_date: datetime = Field(default_factory=datetime.now)
    
    # 活跃度统计
    daily_interactions: Dict[str, int] = Field(default_factory=dict)  # {"2024-01-01": 5}
    weekly_active: bool = False
    monthly_active: bool = False

class User(BaseModel):
    """
    用户模型
    
    包含用户的所有信息和设置
    """
    
    # 基本信息
    openid: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # 位置信息
    location: LocationInfo = Field(
        default_factory=lambda: LocationInfo(city=config.DEFAULT_CITY)
    )
    
    # 偏好设置
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    # 统计信息
    stats: UserStats = Field(default_factory=UserStats)
    
    # 状态信息
    is_active: bool = True
    is_blocked: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 备注信息
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    @property
    def city(self) -> str:
        """向后兼容的city属性"""
        return self.location.city
    
    @city.setter
    def city(self, value: str):
        """向后兼容的city设置"""
        self.location.city = value
        self.location.last_updated = datetime.now()
        self.updated_at = datetime.now()
    
    def update_location(self, city: str, province: str = None, 
                       latitude: float = None, longitude: float = None,
                       source: str = "manual") -> bool:
        """
        更新用户位置信息
        
        Args:
            city: 城市名称
            province: 省份名称
            latitude: 纬度
            longitude: 经度
            source: 更新来源
            
        Returns:
            是否更新成功
        """
        try:
            self.location.city = city
            if province:
                self.location.province = province
            if latitude is not None:
                self.location.latitude = latitude
            if longitude is not None:
                self.location.longitude = longitude
            
            self.location.update_source = source
            self.location.last_updated = datetime.now()
            self.stats.location_updates += 1
            self.updated_at = datetime.now()
            
            logger.info(f"用户 {self.openid} 位置更新为 {city}")
            return True
            
        except Exception as e:
            logger.error(f"更新用户 {self.openid} 位置失败: {str(e)}")
            return False
    
    def update_preferences(self, **kwargs) -> bool:
        """
        更新用户偏好设置
        
        Args:
            **kwargs: 偏好设置参数
            
        Returns:
            是否更新成功
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.preferences, key):
                    setattr(self.preferences, key, value)
            
            self.updated_at = datetime.now()
            logger.info(f"用户 {self.openid} 偏好设置已更新")
            return True
            
        except Exception as e:
            logger.error(f"更新用户 {self.openid} 偏好设置失败: {str(e)}")
            return False
    
    def record_interaction(self, interaction_type: str):
        """
        记录用户交互
        
        Args:
            interaction_type: 交互类型 (weather, news, location, chat)
        """
        try:
            # 更新总交互数
            self.stats.total_interactions += 1
            self.stats.last_active_time = datetime.now()
            
            # 更新具体交互类型统计
            if interaction_type == "weather":
                self.stats.weather_queries += 1
            elif interaction_type == "news":
                self.stats.news_queries += 1
            elif interaction_type == "location":
                self.stats.location_updates += 1
            elif interaction_type == "chat":
                self.stats.ai_chat_count += 1
            
            # 更新日常交互统计
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in self.stats.daily_interactions:
                self.stats.daily_interactions[today] = 0
            self.stats.daily_interactions[today] += 1
            
            # 设置首次交互时间
            if not self.stats.first_interaction:
                self.stats.first_interaction = datetime.now()
            
            self.updated_at = datetime.now()
            
        except Exception as e:
            logger.error(f"记录用户 {self.openid} 交互失败: {str(e)}")
    
    def record_push_received(self):
        """记录推送接收"""
        self.stats.total_push_received += 1
        self.updated_at = datetime.now()
    
    def is_notification_time(self, current_time: datetime = None) -> bool:
        """
        检查是否为用户的推送时间
        
        Args:
            current_time: 当前时间，默认为现在
            
        Returns:
            是否为推送时间
        """
        if not self.preferences.notification_enabled:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        notification_hour, notification_minute = map(int, self.preferences.notification_time.value.split(":"))
        
        return (current_time.hour == notification_hour and 
                current_time.minute == notification_minute)
    
    def get_preferred_news_categories(self) -> List[str]:
        """获取用户偏好的新闻类别"""
        return [cat.value for cat in self.preferences.preferred_news_categories]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """从字典创建用户对象"""
        return cls(**data)

# 内存中的用户数据存储
user_db: Dict[str, User] = {}

def get_user(openid: str) -> User:
    """
    获取或创建用户
    
    Args:
        openid: 微信用户唯一标识
        
    Returns:
        用户对象
    """
    if openid not in user_db:
        user_db[openid] = User(openid=openid)
        logger.info(f"创建新用户: {openid}")
    
    return user_db[openid]

def update_user_city(openid: str, city: str) -> bool:
    """
    更新用户城市（向后兼容函数）
    
    Args:
        openid: 微信用户唯一标识
        city: 城市名称
        
    Returns:
        是否更新成功
    """
    try:
        user = get_user(openid)
        return user.update_location(city)
    except Exception as e:
        logger.error(f"更新用户 {openid} 城市失败: {str(e)}")
        return False

def get_all_users() -> List[User]:
    """
    获取所有用户
    
    Returns:
        用户列表
    """
    return list(user_db.values())

def get_active_users() -> List[User]:
    """
    获取活跃用户
    
    Returns:
        活跃用户列表
    """
    return [user for user in user_db.values() if user.is_active and not user.is_blocked]

def get_users_by_city(city: str) -> List[User]:
    """
    按城市获取用户
    
    Args:
        city: 城市名称
        
    Returns:
        该城市的用户列表
    """
    return [user for user in user_db.values() if user.location.city == city]

def get_users_for_notification(current_time: datetime = None) -> List[User]:
    """
    获取需要接收推送的用户
    
    Args:
        current_time: 当前时间
        
    Returns:
        需要推送的用户列表
    """
    if current_time is None:
        current_time = datetime.now()
    
    return [
        user for user in get_active_users()
        if user.is_notification_time(current_time)
    ]

def get_user_stats() -> Dict[str, Any]:
    """
    获取用户统计信息
    
    Returns:
        统计信息字典
    """
    total_users = len(user_db)
    active_users = len(get_active_users())
    
    # 计算各城市用户数
    city_stats = {}
    for user in user_db.values():
        city = user.location.city
        city_stats[city] = city_stats.get(city, 0) + 1
    
    # 计算交互统计
    total_interactions = sum(user.stats.total_interactions for user in user_db.values())
    total_push_received = sum(user.stats.total_push_received for user in user_db.values())
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "blocked_users": total_users - active_users,
        "city_distribution": city_stats,
        "total_interactions": total_interactions,
        "total_push_received": total_push_received,
        "average_interactions_per_user": total_interactions / total_users if total_users > 0 else 0
    }