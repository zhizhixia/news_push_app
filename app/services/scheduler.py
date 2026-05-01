"""
任务调度服务模块

该模块负责管理和执行各种定时任务，包括：
- 每日新闻天气推送
- 数据缓存刷新
- 系统健康检查
- 日志清理
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from wechatpy import WeChatClient
from typing import Dict, List, Any
import logging
import asyncio
from datetime import datetime, timedelta
from app.services.push_service import push_service
from app.services.weather import weather_service
from app.services.news import news_service
from app.services.llm import llm_service
from app.services.location import location_service
from app.models.user import user_db
from config.config import config
from app.utils.singleton import SingletonMeta

logger = logging.getLogger(__name__)

class SchedulerService(metaclass=SingletonMeta):
    """
    任务调度服务类（单例模式）
    """
    
    def __init__(self):
        # 时区配置：优先使用 pytz，如不可用则使用默认时区
        tzinfo = None
        try:
            import pytz  # 可选依赖：若不存在则使用默认时区
            tzinfo = pytz.timezone(config.SCHEDULER_TIMEZONE)
        except Exception:
            logger.warning(f"未安装或无法加载时区库，使用默认时区: {config.SCHEDULER_TIMEZONE}")
        self.scheduler = AsyncIOScheduler(timezone=tzinfo) if tzinfo else AsyncIOScheduler()
        self.wechat_client = None
        self.push_service = push_service
        self.weather_service = weather_service
        self.news_service = news_service
        self.llm_service = llm_service
        self.location_service = location_service
        
        # 任务统计
        self.task_stats = {
            'daily_push_count': 0,
            'cache_refresh_count': 0,
            'health_check_count': 0,
            'last_error': None
        }
        
        logger.info("任务调度服务初始化完成")
    
    def initialize_wechat_client(self):
        """
        初始化微信客户端
        """
        try:
            if config.WECHAT_APPID and config.WECHAT_APPSECRET:
                self.wechat_client = WeChatClient(config.WECHAT_APPID, config.WECHAT_APPSECRET)
                logger.info("微信客户端初始化成功")
            else:
                logger.warning("微信配置不完整，无法初始化微信客户端")
        except Exception as e:
            logger.error(f"微信客户端初始化失败: {str(e)}")
    
    def start_scheduler(self):
        """
        启动任务调度器
        """
        try:
            # 初始化微信客户端
            self.initialize_wechat_client()
            
            # 添加所有任务
            self._add_all_jobs()
            
            # 启动调度器
            self.scheduler.start()
            logger.info("任务调度器启动成功")
            
        except Exception as e:
            logger.error(f"任务调度器启动失败: {str(e)}")
            raise
    
    def stop_scheduler(self):
        """
        停止任务调度器
        """
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("任务调度器已停止")
        except Exception as e:
            logger.error(f"停止任务调度器失败: {str(e)}")
    
    def _add_all_jobs(self):
        """
        添加所有调度任务
        """
        # 1. 每日新闻天气推送任务
        self.scheduler.add_job(
            self.send_daily_push,
            CronTrigger(
                hour=config.PUSH_TIME_HOUR,
                minute=config.PUSH_TIME_MINUTE
            ),
            id='daily_news_weather_push',
            name='每日新闻天气推送',
            replace_existing=True,
            max_instances=1
        )
        
        # 2. 新闻缓存刷新任务
        self.scheduler.add_job(
            self.refresh_news_cache,
            IntervalTrigger(hours=2),
            id='news_cache_refresh',
            name='新闻缓存刷新',
            replace_existing=True,
            max_instances=1
        )
        
        # 3. 天气缓存刷新任务
        self.scheduler.add_job(
            self.refresh_weather_cache,
            IntervalTrigger(hours=1),
            id='weather_cache_refresh',
            name='天气缓存刷新',
            replace_existing=True,
            max_instances=1
        )
        
        # 4. 系统健康检查任务
        self.scheduler.add_job(
            self.system_health_check,
            IntervalTrigger(minutes=30),
            id='system_health_check',
            name='系统健康检查',
            replace_existing=True,
            max_instances=1
        )
        
        # 5. 缓存清理任务
        self.scheduler.add_job(
            self.cleanup_expired_cache,
            CronTrigger(hour=2, minute=0),  # 每日凌晨2点
            id='cache_cleanup',
            name='缓存清理',
            replace_existing=True,
            max_instances=1
        )
        
        # 6. 推送统计报告任务（每周一次）
        self.scheduler.add_job(
            self.generate_weekly_report,
            CronTrigger(day_of_week='mon', hour=9, minute=0),  # 每周一早上9点
            id='weekly_report',
            name='周报生成',
            replace_existing=True,
            max_instances=1
        )
        
        logger.info("所有调度任务添加完成")
    
    async def send_daily_push(self):
        """
        发送每日推送
        """
        try:
            logger.info("开始执行每日推送任务")
            
            if not self.wechat_client:
                logger.error("微信客户端未初始化，无法发送推送")
                return
            
            success_count = 0
            error_count = 0
            
            # 遍历所有用户
            for user in user_db.values():
                try:
                    # 生成个性化推送内容
                    content = self.push_service.generate_daily_push_content(user.city)
                    
                    # 发送消息
                    self.wechat_client.message.send_text(user.openid, content)
                    
                    success_count += 1
                    logger.debug(f"成功发送推送给用户 {user.openid}")
                    
                    # 避免发送过快，稍微延迟
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"发送推送给用户 {user.openid} 失败: {str(e)}")
            
            # 更新统计
            self.task_stats['daily_push_count'] += 1
            
            logger.info(f"每日推送任务完成，成功: {success_count}, 失败: {error_count}")
            
        except Exception as e:
            logger.error(f"每日推送任务执行失败: {str(e)}")
            self.task_stats['last_error'] = str(e)
    
    async def refresh_news_cache(self):
        """
        刷新新闻缓存
        """
        try:
            logger.info("开始刷新新闻缓存")
            
            # 预加载热点新闻
            categories = ['headlines', 'technology', 'economy', 'society']
            
            for category in categories:
                try:
                    self.news_service.get_news_by_category(category, 10, use_cache=False)
                    await asyncio.sleep(0.5)  # 避免请求过快
                except Exception as e:
                    logger.error(f"刷新{category}类别新闻失败: {str(e)}")
            
            # 预加载热点新闻
            self.news_service.get_hot_news(limit=15, use_cache=False)
            
            self.task_stats['cache_refresh_count'] += 1
            logger.info("新闻缓存刷新完成")
            
        except Exception as e:
            logger.error(f"刷新新闻缓存失败: {str(e)}")
    
    async def refresh_weather_cache(self):
        """
        刷新天气缓存
        """
        try:
            logger.info("开始刷新天气缓存")
            
            # 获取用户所在城市列表
            user_cities = set(user.city for user in user_db.values())
            
            # 添加默认城市
            user_cities.add(config.DEFAULT_CITY)
            
            for city in user_cities:
                try:
                    # 刷新当前天气
                    self.weather_service.get_current_weather(city, use_cache=False)
                    
                    # 刷新天气预报
                    self.weather_service.get_weather_forecast(city, 7, use_cache=False)
                    
                    await asyncio.sleep(0.3)  # 避免请求过快
                except Exception as e:
                    logger.error(f"刷新{city}天气缓存失败: {str(e)}")
            
            logger.info("天气缓存刷新完成")
            
        except Exception as e:
            logger.error(f"刷新天气缓存失败: {str(e)}")
    
    async def system_health_check(self):
        """
        系统健康检查
        """
        try:
            logger.debug("开始系统健康检查")
            
            health_status = {
                'weather_service': self.weather_service.health_check(),
                'news_service': self.news_service.health_check(),
                'llm_service': self.llm_service.health_check(),
                'location_service': self.location_service.health_check(),
                'push_service': self.push_service.health_check()
            }
            
            # 检查结果
            unhealthy_services = [service for service, status in health_status.items() if not status]
            
            if unhealthy_services:
                logger.warning(f"检测到服务异常: {unhealthy_services}")
                self.task_stats['last_error'] = f"服务异常: {unhealthy_services}"
            else:
                logger.debug("所有服务运行正常")
            
            self.task_stats['health_check_count'] += 1
            
        except Exception as e:
            logger.error(f"系统健康检查失败: {str(e)}")
    
    async def cleanup_expired_cache(self):
        """
        清理过期缓存
        """
        try:
            logger.info("开始清理过期缓存")
            
            # 清理各个服务的过期缓存
            self.weather_service.clear_expired_cache() if hasattr(self.weather_service, 'clear_expired_cache') else None
            self.news_service.clear_cache() if hasattr(self.news_service, 'clear_cache') else None
            self.push_service.clear_cache() if hasattr(self.push_service, 'clear_cache') else None
            
            logger.info("过期缓存清理完成")
            
        except Exception as e:
            logger.error(f"清理过期缓存失败: {str(e)}")
    
    async def generate_weekly_report(self):
        """
        生成周报
        """
        try:
            logger.info("开始生成周报")
            
            # 统计数据
            user_count = len(user_db)
            daily_push_count = self.task_stats.get('daily_push_count', 0)
            cache_refresh_count = self.task_stats.get('cache_refresh_count', 0)
            health_check_count = self.task_stats.get('health_check_count', 0)
            last_error = self.task_stats.get('last_error')
            
            # 生成报告内容
            report_parts = []
            report_parts.append("📊 系统运行周报")
            report_parts.append("="*20)
            report_parts.append(f"👥 活跃用户数: {user_count}")
            report_parts.append(f"📧 每日推送次数: {daily_push_count}")
            report_parts.append(f"🔄 缓存刷新次数: {cache_refresh_count}")
            report_parts.append(f"⚕️ 健康检查次数: {health_check_count}")
            
            if last_error:
                report_parts.append(f"⚠️ 最近错误: {last_error}")
            else:
                report_parts.append("✅ 本周无错误")
            
            report_content = "\n".join(report_parts)
            
            # 这里可以发送给管理员或记录到日志
            logger.info(f"周报生成完成:\n{report_content}")
            
            # 重置部分统计
            self.task_stats['daily_push_count'] = 0
            self.task_stats['cache_refresh_count'] = 0
            self.task_stats['health_check_count'] = 0
            self.task_stats['last_error'] = None
            
        except Exception as e:
            logger.error(f"生成周报失败: {str(e)}")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        获取调度器状态
        
        Returns:
            调度器状态信息
        """
        try:
            jobs = self.scheduler.get_jobs()
            
            job_info = []
            for job in jobs:
                job_info.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            
            return {
                'running': self.scheduler.running,
                'job_count': len(jobs),
                'jobs': job_info,
                'task_stats': self.task_stats
            }
            
        except Exception as e:
            logger.error(f"获取调度器状态失败: {str(e)}")
            return {
                'running': False,
                'error': str(e)
            }
    
    def trigger_manual_push(self):
        """
        手动触发推送
        """
        try:
            logger.info("手动触发推送任务")
            # 创建异步任务
            asyncio.create_task(self.send_daily_push())
        except Exception as e:
            logger.error(f"手动触发推送失败: {str(e)}")

# 全局调度器服务实例
scheduler_service = SchedulerService()