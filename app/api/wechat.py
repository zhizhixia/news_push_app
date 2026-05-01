"""
微信API模块

处理微信公众号的消息接收、验证和回复功能。
"""

from fastapi import APIRouter, Request, Response, HTTPException
from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from app.services.interaction import handle_user_interaction
from app.models.user import get_user
from config.config import config
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/wechat")
def wechat_verification(request: Request):
    """
    微信服务器验证
    """
    try:
        signature = request.query_params.get("signature", "")
        timestamp = request.query_params.get("timestamp", "")
        nonce = request.query_params.get("nonce", "")
        echostr = request.query_params.get("echostr", "")
        
        check_signature(config.WECHAT_TOKEN, signature, timestamp, nonce)
        logger.info("微信验证成功")
        return Response(content=echostr)
        
    except InvalidSignatureException:
        logger.error("微信签名验证失败")
        return Response(content="Invalid signature", status_code=403)
    except Exception as e:
        logger.error(f"微信验证异常: {str(e)}")
        return Response(content="Verification failed", status_code=500)

@router.post("/wechat")
async def wechat_message(request: Request):
    """
    处理微信消息
    """
    try:
        body = await request.body()
        msg = parse_message(body)
        
        # 获取用户信息
        user = get_user(msg.source)
        
        if msg.type == 'text':
            # 记录用户交互
            user.record_interaction("chat")
            
            # 处理文本消息
            response_text = handle_user_interaction(msg.source, msg.content)
            reply = create_reply(response_text, msg)
        else:
            reply = create_reply("对不起，目前只能处理文本消息", msg)
        
        return Response(content=reply.render(), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"处理微信消息失败: {str(e)}")
        return Response(content="处理失败", status_code=500)