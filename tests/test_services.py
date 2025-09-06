"""
单元测试模块

测试覆盖所有核心功能，包括：
- MCP服务适配器
- 业务逻辑服务
- 用户交互处理
- 数据模型操作
- 推送内容生成
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from app.services.push_service import push_service
from app.services.weather import weather_service
from app.services.news import news_service
from app.services.location import location_service
from app.services.llm import llm_service, UserIntent
from app.services.interaction import handle_user_interaction
from app.models.user import User, get_user, update_user_city, UserPreferences, LocationInfo
from app.adapters.moji_weather_mcp import MojiWeatherMCP
from app.adapters.city_news_mcp import CityNewsMCP
from app.adapters.gaode_map_mcp import GaodeMapMCP

class TestMCPAdapters(unittest.TestCase):
    """测试MCP服务适配器"""
    
    def test_moji_weather_mcp(self):
        """测试墨迹天气MCP适配器"""
        adapter = MojiWeatherMCP()
        
        # 测试获取当前天气
        result = adapter.get_current_weather("北京")
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        
        # 测试健康检查
        health = adapter.health_check()
        self.assertTrue(health)
    
    def test_city_news_mcp(self):
        """测试城市新闻MCP适配器"""
        adapter = CityNewsMCP()
        
        # 测试获取热点新闻
        result = adapter.get_hot_news(limit=5)
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        
        # 测试按类别获取新闻
        result = adapter.get_news_by_category("headlines", 3)
        self.assertEqual(result["status"], "success")
        
        # 测试健康检查
        health = adapter.health_check()
        self.assertTrue(health)
    
    def test_gaode_map_mcp(self):
        """测试高德地图MCP适配器"""
        adapter = GaodeMapMCP()
        
        # 测试城市名标准化
        normalized = adapter.normalize_city_name("北京市")
        self.assertEqual(normalized, "北京")
        
        # 测试城市信息获取
        result = adapter.get_city_info("上海")
        self.assertEqual(result["status"], "success")
        
        # 测试健康检查
        health = adapter.health_check()
        self.assertTrue(health)

class TestWeatherService(unittest.TestCase):
    """测试天气服务"""
    
    def test_get_current_weather(self):
        """测试获取当前天气"""
        result = weather_service.get_current_weather("北京")
        self.assertIn("status", result)
    
    def test_get_weather_summary(self):
        """测试获取天气摘要"""
        summary = weather_service.get_weather_summary("北京")
        self.assertIsInstance(summary, str)
        self.assertIn("北京", summary)
    
    def test_format_push_weather(self):
        """测试格式化推送天气"""
        push_content = weather_service.format_push_weather("北京")
        self.assertIsInstance(push_content, str)
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        # 清空缓存
        weather_service.clear_cache()
        
        # 第一次调用
        result1 = weather_service.get_current_weather("北京")
        
        # 第二次调用（应该使用缓存）
        result2 = weather_service.get_current_weather("北京")
        
        self.assertEqual(result1, result2)

class TestNewsService(unittest.TestCase):
    """测试新闻服务"""
    
    def test_get_hot_news(self):
        """测试获取热点新闻"""
        result = news_service.get_hot_news(limit=5)
        self.assertIn("status", result)
    
    def test_get_news_by_category(self):
        """测试按类别获取新闻"""
        result = news_service.get_news_by_category("headlines", 3)
        self.assertIn("status", result)
    
    def test_get_daily_news_summary(self):
        """测试获取日常新闻摘要"""
        summary = news_service.get_daily_news_summary()
        self.assertIsInstance(summary, str)
    
    def test_search_news(self):
        """测试新闻搜索"""
        result = news_service.search_news("科技")
        self.assertIn("status", result)

class TestLocationService(unittest.TestCase):
    """测试位置服务"""
    
    def test_normalize_city_name(self):
        """测试城市名标准化"""
        normalized = location_service.normalize_city_name("北京市")
        self.assertEqual(normalized, "北京")
        
        normalized = location_service.normalize_city_name("帝都")
        self.assertEqual(normalized, "北京")
    
    def test_validate_location(self):
        """测试位置验证"""
        valid = location_service.validate_location("北京")
        self.assertTrue(valid)
        
        invalid = location_service.validate_location("不存在的城市")
        self.assertFalse(invalid)
    
    def test_process_location_update(self):
        """测试位置更新处理"""
        result = location_service.process_location_update("上海")
        self.assertEqual(result["status"], "success")
        self.assertIn("normalized_city", result["data"])

class TestLLMService(unittest.TestCase):
    """测试LLM服务"""
    
    @patch('app.services.llm.Generation.call')
    def test_generate_response(self, mock_call):
        """测试生成AI响应"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output.text = "测试响应"
        mock_call.return_value = mock_response
        
        response = llm_service.generate_response("你好")
        self.assertEqual(response, "测试响应")
    
    def test_analyze_user_intent(self):
        """测试用户意图分析"""
        intent = llm_service.analyze_user_intent("更改城市 北京")
        self.assertIsInstance(intent, UserIntent)
        self.assertEqual(intent.intent_type, "update_location")
        
        intent = llm_service.analyze_user_intent("天气怎么样")
        self.assertEqual(intent.intent_type, "query_weather")
    
    def test_format_news_summary(self):
        """测试格式化新闻摘要"""
        news_data = [
            {"title": "测试新闻1", "summary": "摘要1"},
            {"title": "测试新闻2", "summary": "摘要2"}
        ]
        
        formatted = llm_service.format_news_summary(news_data)
        self.assertIsInstance(formatted, str)

class TestPushService(unittest.TestCase):
    """测试推送服务"""
    
    def test_generate_daily_push_content(self):
        """测试生成每日推送内容"""
        content = push_service.generate_daily_push_content("北京")
        self.assertIsInstance(content, str)
        self.assertIn("北京", content)
    
    def test_generate_weather_push(self):
        """测试生成天气推送"""
        content = push_service.generate_weather_push("北京")
        self.assertIsInstance(content, str)
    
    def test_generate_news_push(self):
        """测试生成新闻推送"""
        content = push_service.generate_news_push(5)
        self.assertIsInstance(content, str)
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        push_service.clear_cache()
        
        # 测试缓存生效
        content1 = push_service.generate_daily_push_content("北京")
        content2 = push_service.generate_daily_push_content("北京")
        
        self.assertEqual(content1, content2)

class TestUserModel(unittest.TestCase):
    """测试用户数据模型"""
    
    def test_user_creation(self):
        """测试用户创建"""
        user = User(openid="test_user")
        self.assertEqual(user.openid, "test_user")
        self.assertEqual(user.location.city, "北京")  # 默认城市
        self.assertTrue(user.preferences.notification_enabled)
    
    def test_user_location_update(self):
        """测试用户位置更新"""
        user = User(openid="test_user")
        success = user.update_location("上海", "上海市")
        
        self.assertTrue(success)
        self.assertEqual(user.location.city, "上海")
        self.assertEqual(user.location.province, "上海市")
    
    def test_user_preferences_update(self):
        """测试用户偏好更新"""
        user = User(openid="test_user")
        success = user.update_preferences(
            notification_enabled=False,
            news_count_limit=8
        )
        
        self.assertTrue(success)
        self.assertFalse(user.preferences.notification_enabled)
        self.assertEqual(user.preferences.news_count_limit, 8)
    
    def test_record_interaction(self):
        """测试记录用户交互"""
        user = User(openid="test_user")
        initial_count = user.stats.total_interactions
        
        user.record_interaction("weather")
        
        self.assertEqual(user.stats.total_interactions, initial_count + 1)
        self.assertEqual(user.stats.weather_queries, 1)
    
    def test_get_user_function(self):
        """测试获取用户函数"""
        user = get_user("test_openid")
        self.assertEqual(user.openid, "test_openid")
        
        # 再次获取应该返回同一个用户
        user2 = get_user("test_openid")
        self.assertEqual(user.openid, user2.openid)
    
    def test_update_user_city_function(self):
        """测试更新用户城市函数"""
        success = update_user_city("test_openid", "深圳")
        self.assertTrue(success)
        
        user = get_user("test_openid")
        self.assertEqual(user.city, "深圳")

class TestUserInteraction(unittest.TestCase):
    """测试用户交互处理"""
    
    def test_help_command(self):
        """测试帮助命令"""
        response = handle_user_interaction("test_openid", "帮助")
        self.assertIn("欢迎使用", response)
        self.assertIn("智能新闻助手", response)
    
    def test_location_update_command(self):
        """测试位置更新命令"""
        response = handle_user_interaction("test_openid", "更改城市 广州")
        self.assertIn("位置已", response)
        
        # 验证城市已更新
        user = get_user("test_openid")
        self.assertEqual(user.city, "广州")
    
    def test_weather_query(self):
        """测试天气查询"""
        response = handle_user_interaction("test_openid", "天气")
        self.assertIsInstance(response, str)
    
    def test_news_query(self):
        """测试新闻查询"""
        response = handle_user_interaction("test_openid", "今日新闻")
        self.assertIsInstance(response, str)
    
    @patch('app.services.llm.llm_service.generate_response')
    def test_general_chat(self, mock_generate):
        """测试一般对话"""
        mock_generate.return_value = "AI回复"
        
        response = handle_user_interaction("test_openid", "你好")
        self.assertEqual(response, "AI回复")

class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_complete_user_workflow(self):
        """测试完整的用户工作流程"""
        # 1. 新用户交互
        user_id = "integration_test_user"
        
        # 2. 位置设置
        response = handle_user_interaction(user_id, "更改城市 杭州")
        self.assertIn("杭州", response)
        
        # 3. 天气查询
        response = handle_user_interaction(user_id, "天气")
        self.assertIsInstance(response, str)
        
        # 4. 新闻查询
        response = handle_user_interaction(user_id, "新闻")
        self.assertIsInstance(response, str)
        
        # 5. 验证用户数据
        user = get_user(user_id)
        self.assertEqual(user.city, "杭州")
        self.assertGreater(user.stats.total_interactions, 0)
    
    def test_service_health_checks(self):
        """测试所有服务健康检查"""
        # 测试各服务健康状态
        weather_health = weather_service.health_check()
        news_health = news_service.health_check()
        location_health = location_service.health_check()
        push_health = push_service.health_check()
        llm_health = llm_service.health_check()
        
        # 至少基本功能应该可用
        self.assertTrue(any([weather_health, news_health, location_health, push_health, llm_health]))

if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)