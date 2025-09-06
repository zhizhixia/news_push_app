"""
主应用入口

基于MCP架构的新闻天气推送应用主程序。
集成阿里云百炼大模型、墨迹天气、城市新闻、高德地图MCP服务。
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api import wechat
from app.services.scheduler import scheduler_service
from config.config import config
import logging
import uvicorn

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="新闻天气推送服务",
    description="基于MCP架构的智能新闻天气推送应用",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(wechat.router, prefix="/api", tags=["微信接口"])

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    try:
        logger.info("应用启动中...")
        
        # 验证配置
        config.validate_config()
        logger.info("配置验证通过")
        
        # 启动任务调度器
        scheduler_service.start_scheduler()
        logger.info("任务调度器启动完成")
        
        logger.info("应用启动成功")
        
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    try:
        logger.info("应用关闭中...")
        
        # 停止任务调度器
        scheduler_service.stop_scheduler()
        logger.info("任务调度器已停止")
        
        logger.info("应用关闭完成")
        
    except Exception as e:
        logger.error(f"应用关闭异常: {str(e)}")

@app.get("/", tags=["系统信息"])
def read_root():
    """系统信息接口"""
    return {
        "message": "欢迎使用新闻天气推送服务",
        "version": "1.0.0",
        "description": "基于MCP架构的智能新闻天气推送应用",
        "features": [
            "阿里云百炼大模型集成",
            "墨迹天气MCP服务",
            "城市热点新闻MCP服务",
            "高德地图MCP服务",
            "智能用户交互",
            "定时推送服务"
        ]
    }

@app.get("/health", tags=["系统信息"])
def health_check():
    """健康检查接口"""
    try:
        # 检查调度器状态
        scheduler_status = scheduler_service.get_scheduler_status()
        
        return {
            "status": "healthy",
            "timestamp": logging.Formatter().formatTime(logging.LogRecord(
                "", 0, "", 0, "", (), None
            )),
            "scheduler": scheduler_status
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail="系统异常")

if __name__ == "__main__":
    logger.info("启动应用...")
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        reload=config.RELOAD,
        log_level=config.LOG_LEVEL.lower()
    )