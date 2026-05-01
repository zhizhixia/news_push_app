"""
位置服务模块

该模块集成高德地图MCP服务，提供统一的地理位置服务接口。
支持的功能：
- 城市名称标准化
- 地理坐标查询
- 位置验证
- 地址解析
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from app.adapters.gaode_map_mcp import GaodeMapMCP
from app.utils.singleton import SingletonMeta

logger = logging.getLogger(__name__)

class LocationService(metaclass=SingletonMeta):
    """
    位置服务类（单例模式）
    
    集成高德地图MCP服务，提供统一的地理位置服务接口
    """
    
    def __init__(self):
        self.mcp_client = GaodeMapMCP()
        
        logger.info("位置服务初始化完成")
    
    def normalize_city_name(self, user_input: str) -> str:
        """
        标准化城市名称
        
        Args:
            user_input: 用户输入的城市名
            
        Returns:
            标准化后的城市名
        """
        try:
            normalized_city = self.mcp_client.normalize_city_name(user_input)
            logger.info(f"城市名标准化: {user_input} -> {normalized_city}")
            return normalized_city
        except Exception as e:
            logger.error(f"城市名标准化失败: {str(e)}")
            return user_input
    
    def validate_location(self, location: str) -> bool:
        """
        验证位置是否有效
        
        Args:
            location: 位置字符串
            
        Returns:
            位置是否有效
        """
        try:
            return self.mcp_client.validate_city_name(location)
        except Exception as e:
            logger.error(f"位置验证失败: {str(e)}")
            return False
    
    def get_city_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        """
        获取城市坐标
        
        Args:
            city: 城市名称
            
        Returns:
            城市坐标 (经度, 纬度)，如果未找到返回None
        """
        try:
            coordinates = self.mcp_client.get_city_coordinates(city)
            if coordinates:
                logger.info(f"获取{city}坐标: {coordinates}")
            return coordinates
        except Exception as e:
            logger.error(f"获取{city}坐标失败: {str(e)}")
            return None
    
    def get_city_info(self, city: str) -> Dict[str, Any]:
        """
        获取城市详细信息
        
        Args:
            city: 城市名称
            
        Returns:
            包含城市信息的字典
        """
        try:
            result = self.mcp_client.get_city_info(city)
            
            if result.get("status") == "success":
                logger.info(f"获取{city}详细信息成功")
                return result
            else:
                logger.error(f"获取{city}详细信息失败: {result.get('message')}")
                return {
                    "status": "error",
                    "message": f"获取{city}信息失败"
                }
                
        except Exception as e:
            logger.error(f"获取{city}信息服务异常: {str(e)}")
            return {
                "status": "error",
                "message": f"位置服务不可用: {str(e)}"
            }
    
    def search_cities(self, keyword: str) -> Dict[str, Any]:
        """
        搜索城市
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            包含搜索结果的字典
        """
        try:
            result = self.mcp_client.city_search(keyword)
            
            if result.get("status") == "success":
                logger.info(f"城市搜索'{keyword}'成功")
                return result
            else:
                logger.error(f"城市搜索'{keyword}'失败: {result.get('message')}")
                return {
                    "status": "error",
                    "message": f"搜索城市'{keyword}'失败"
                }
                
        except Exception as e:
            logger.error(f"城市搜索服务异常: {str(e)}")
            return {
                "status": "error",
                "message": f"搜索服务不可用: {str(e)}"
            }
    
    def geocode(self, address: str) -> Dict[str, Any]:
        """
        地址地理编码（地址转坐标）
        
        Args:
            address: 地址字符串
            
        Returns:
            包含坐标信息的字典
        """
        try:
            result = self.mcp_client.geocode(address)
            
            if result.get("status") == "success":
                logger.info(f"地址地理编码成功: {address}")
                return result
            else:
                logger.error(f"地址地理编码失败: {result.get('message')}")
                return {
                    "status": "error",
                    "message": f"地址'{address}'解析失败"
                }
                
        except Exception as e:
            logger.error(f"地理编码服务异常: {str(e)}")
            return {
                "status": "error",
                "message": f"地理编码服务不可用: {str(e)}"
            }
    
    def regeocode(self, lng: float, lat: float) -> Dict[str, Any]:
        """
        坐标逆地理编码（坐标转地址）
        
        Args:
            lng: 经度
            lat: 纬度
            
        Returns:
            包含地址信息的字典
        """
        try:
            result = self.mcp_client.regeocode(lng, lat)
            
            if result.get("status") == "success":
                logger.info(f"坐标逆地理编码成功: ({lng}, {lat})")
                return result
            else:
                logger.error(f"坐标逆地理编码失败: {result.get('message')}")
                return {
                    "status": "error",
                    "message": f"坐标({lng}, {lat})解析失败"
                }
                
        except Exception as e:
            logger.error(f"逆地理编码服务异常: {str(e)}")
            return {
                "status": "error",
                "message": f"逆地理编码服务不可用: {str(e)}"
            }
    
    def process_location_update(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户位置更新请求
        
        Args:
            user_input: 用户输入的位置信息
            
        Returns:
            处理结果字典，包含标准化的城市名和处理状态
        """
        try:
            # 去除多余空格
            location = user_input.strip()
            
            if not location:
                return {
                    "status": "error",
                    "message": "位置信息不能为空"
                }
            
            # 验证位置有效性
            if not self.validate_location(location):
                # 尝试搜索相似城市
                search_result = self.search_cities(location)
                
                if search_result.get("status") == "success":
                    cities = search_result.get("data", {}).get("cities", [])
                    if cities:
                        suggestions = [city["name"] for city in cities[:3]]
                        return {
                            "status": "error",
                            "message": f"无法识别位置'{location}'，您是否想要：{', '.join(suggestions)}？"
                        }
                
                return {
                    "status": "error",
                    "message": f"无法识别位置'{location}'，请提供正确的城市名称"
                }
            
            # 标准化城市名
            normalized_city = self.normalize_city_name(location)
            
            # 获取城市详细信息用于确认
            city_info_result = self.get_city_info(normalized_city)
            
            if city_info_result.get("status") == "success":
                city_data = city_info_result.get("data", {})
                province = city_data.get("province", "")
                
                return {
                    "status": "success",
                    "data": {
                        "original_input": user_input,
                        "normalized_city": normalized_city,
                        "province": province,
                        "location": city_data.get("location", {}),
                        "confirmation_message": f"位置已设置为：{province} {normalized_city}"
                    }
                }
            else:
                return {
                    "status": "success",
                    "data": {
                        "original_input": user_input,
                        "normalized_city": normalized_city,
                        "confirmation_message": f"位置已设置为：{normalized_city}"
                    }
                }
                
        except Exception as e:
            logger.error(f"处理位置更新失败: {str(e)}")
            return {
                "status": "error",
                "message": f"位置更新处理失败: {str(e)}"
            }
    
    def get_supported_cities(self) -> List[str]:
        """
        获取支持的城市列表
        
        Returns:
            支持的城市名称列表
        """
        try:
            return list(self.mcp_client.city_coordinates.keys())
        except Exception as e:
            logger.error(f"获取支持城市列表失败: {str(e)}")
            return []
    
    def health_check(self) -> bool:
        """
        检查位置服务健康状态
        
        Returns:
            服务是否可用
        """
        try:
            return self.mcp_client.health_check()
        except Exception as e:
            logger.error(f"位置服务健康检查失败: {str(e)}")
            return False

# 全局位置服务实例
location_service = LocationService()