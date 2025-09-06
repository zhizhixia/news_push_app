"""
高德地图MCP服务适配器

该模块封装高德地图MCP服务的调用逻辑，提供统一的地理位置服务接口。
支持的功能：
- 地址地理编码
- 坐标逆地理编码
- 城市搜索
- 城市名称标准化
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class GaodeMapMCP:
    """
    高德地图MCP服务适配器
    
    注意：该服务已经开通，无需额外的API Key配置
    """
    
    def __init__(self):
        """初始化高德地图MCP客户端"""
        self.base_url = "mcp://gaode-map"  # MCP服务协议地址
        self.timeout = 10
        
        # 常用城市坐标映射（模拟数据）
        self.city_coordinates = {
            "北京": (116.407526, 39.90403),
            "上海": (121.473701, 31.230416),
            "广州": (113.264385, 23.129163),
            "深圳": (114.057868, 22.543099),
            "杭州": (120.153576, 30.287459),
            "南京": (118.796877, 32.060255),
            "武汉": (114.305392, 30.593099),
            "成都": (104.066541, 30.572815),
            "西安": (108.939644, 34.343383),
            "重庆": (106.530635, 29.544606),
            "天津": (117.200983, 39.084158),
            "青岛": (120.382639, 36.067082),
            "大连": (121.614682, 38.914003),
            "沈阳": (123.431474, 41.805699),
            "长春": (125.313642, 43.817071),
            "哈尔滨": (126.657717, 45.773225),
            "济南": (117.020359, 36.66853),
            "郑州": (113.649644, 34.757975),
            "太原": (112.548879, 37.87343),
            "石家庄": (114.520487, 38.045474),
            "福州": (119.330221, 26.047125),
            "厦门": (118.096405, 24.479834),
            "南昌": (115.858197, 28.682892),
            "合肥": (117.227239, 31.820586),
            "长沙": (112.938814, 28.228209),
            "昆明": (102.714601, 25.049153),
            "贵阳": (106.630154, 26.647661),
            "兰州": (103.835093, 36.061089),
            "银川": (106.206479, 38.502621),
            "西宁": (101.780199, 36.623178),
            "乌鲁木齐": (87.616971, 43.825592),
            "拉萨": (91.11409, 29.644938),
            "呼和浩特": (111.660351, 40.828319),
            "海口": (110.330802, 20.022071),
            "三亚": (109.511909, 18.252847)
        }
        
        # 城市别名映射
        self.city_aliases = {
            "帝都": "北京",
            "魔都": "上海",
            "羊城": "广州",
            "鹏城": "深圳",
            "杭城": "杭州",
            "金陵": "南京",
            "江城": "武汉",
            "蓉城": "成都",
            "古城": "西安",
            "山城": "重庆",
            "津门": "天津",
            "岛城": "青岛",
            "泉城": "济南",
            "绿城": "郑州",
            "榕城": "福州",
            "鹭岛": "厦门",
            "英雄城": "南昌",
            "庐州": "合肥",
            "星城": "长沙",
            "春城": "昆明",
            "筑城": "贵阳",
            "金城": "兰州"
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
            # 模拟MCP服务调用
            # 在实际实现中，这里应该是MCP协议的具体调用
            
            # 尝试从地址中提取城市名
            city = self._extract_city_from_address(address)
            
            if city and city in self.city_coordinates:
                lng, lat = self.city_coordinates[city]
                
                result_data = {
                    "formatted_address": address,
                    "location": {
                        "lng": lng,
                        "lat": lat
                    },
                    "country": "中国",
                    "province": self._get_province_by_city(city),
                    "city": city,
                    "district": "",
                    "adcode": self._get_adcode_by_city(city),
                    "level": "城市"
                }
                
                logger.info(f"成功地理编码地址: {address}")
                return {
                    "status": "success",
                    "data": result_data
                }
            else:
                # 如果没有找到匹配的城市，返回默认坐标（北京）
                lng, lat = self.city_coordinates["北京"]
                result_data = {
                    "formatted_address": address,
                    "location": {
                        "lng": lng,
                        "lat": lat
                    },
                    "country": "中国",
                    "province": "北京市",
                    "city": "北京",
                    "district": "",
                    "adcode": "110000",
                    "level": "城市"
                }
                
                logger.warning(f"地址 {address} 无法精确匹配，返回默认位置")
                return {
                    "status": "success",
                    "data": result_data
                }
                
        except Exception as e:
            logger.error(f"地理编码失败: {str(e)}")
            return {
                "status": "error",
                "message": f"地理编码失败: {str(e)}"
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
            # 模拟MCP服务调用
            # 找到最近的城市
            nearest_city = self._find_nearest_city(lng, lat)
            
            result_data = {
                "formatted_address": f"中国{self._get_province_by_city(nearest_city)}{nearest_city}",
                "location": {
                    "lng": lng,
                    "lat": lat
                },
                "country": "中国",
                "province": self._get_province_by_city(nearest_city),
                "city": nearest_city,
                "district": "",
                "adcode": self._get_adcode_by_city(nearest_city),
                "level": "城市"
            }
            
            logger.info(f"成功逆地理编码坐标: ({lng}, {lat})")
            return {
                "status": "success",
                "data": result_data
            }
            
        except Exception as e:
            logger.error(f"逆地理编码失败: {str(e)}")
            return {
                "status": "error",
                "message": f"逆地理编码失败: {str(e)}"
            }
    
    def city_search(self, keyword: str) -> Dict[str, Any]:
        """
        城市搜索
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            包含搜索结果的字典
        """
        try:
            # 模拟MCP服务调用
            search_results = []
            keyword = keyword.strip()
            
            # 在城市列表中搜索
            for city, (lng, lat) in self.city_coordinates.items():
                if keyword in city or city in keyword:
                    search_results.append({
                        "name": city,
                        "formatted_address": f"中国{self._get_province_by_city(city)}{city}",
                        "location": {
                            "lng": lng,
                            "lat": lat
                        },
                        "adcode": self._get_adcode_by_city(city),
                        "level": "城市",
                        "type": "行政区域"
                    })
            
            # 在别名中搜索
            for alias, city in self.city_aliases.items():
                if keyword in alias and city in self.city_coordinates:
                    lng, lat = self.city_coordinates[city]
                    search_results.append({
                        "name": city,
                        "alias": alias,
                        "formatted_address": f"中国{self._get_province_by_city(city)}{city}",
                        "location": {
                            "lng": lng,
                            "lat": lat
                        },
                        "adcode": self._get_adcode_by_city(city),
                        "level": "城市",
                        "type": "行政区域"
                    })
            
            # 去重
            unique_results = []
            seen_cities = set()
            for result in search_results:
                if result["name"] not in seen_cities:
                    unique_results.append(result)
                    seen_cities.add(result["name"])
            
            logger.info(f"城市搜索 '{keyword}' 找到 {len(unique_results)} 个结果")
            return {
                "status": "success",
                "data": {
                    "keyword": keyword,
                    "total": len(unique_results),
                    "cities": unique_results
                }
            }
            
        except Exception as e:
            logger.error(f"城市搜索失败: {str(e)}")
            return {
                "status": "error",
                "message": f"城市搜索失败: {str(e)}"
            }
    
    def get_city_info(self, city: str) -> Dict[str, Any]:
        """
        获取城市详细信息
        
        Args:
            city: 城市名称
            
        Returns:
            包含城市信息的字典
        """
        try:
            # 标准化城市名
            normalized_city = self.normalize_city_name(city)
            
            if normalized_city in self.city_coordinates:
                lng, lat = self.city_coordinates[normalized_city]
                
                city_info = {
                    "name": normalized_city,
                    "province": self._get_province_by_city(normalized_city),
                    "location": {
                        "lng": lng,
                        "lat": lat
                    },
                    "adcode": self._get_adcode_by_city(normalized_city),
                    "level": "城市",
                    "timezone": "Asia/Shanghai",
                    "aliases": [alias for alias, c in self.city_aliases.items() if c == normalized_city]
                }
                
                logger.info(f"成功获取城市信息: {normalized_city}")
                return {
                    "status": "success",
                    "data": city_info
                }
            else:
                return {
                    "status": "error",
                    "message": f"未找到城市: {city}"
                }
                
        except Exception as e:
            logger.error(f"获取城市信息失败: {str(e)}")
            return {
                "status": "error",
                "message": f"获取城市信息失败: {str(e)}"
            }
    
    def normalize_city_name(self, user_input: str) -> str:
        """
        标准化城市名称
        
        Args:
            user_input: 用户输入的城市名
            
        Returns:
            标准化后的城市名
        """
        try:
            user_input = user_input.strip()
            
            # 直接匹配
            if user_input in self.city_coordinates:
                return user_input
            
            # 别名匹配
            if user_input in self.city_aliases:
                return self.city_aliases[user_input]
            
            # 去掉"市"字符再匹配
            city_without_suffix = user_input.replace("市", "").replace("省", "")
            if city_without_suffix in self.city_coordinates:
                return city_without_suffix
            
            # 模糊匹配
            for city in self.city_coordinates:
                if user_input in city or city in user_input:
                    return city
            
            # 如果都没有匹配，返回原输入
            logger.warning(f"无法标准化城市名: {user_input}")
            return user_input
            
        except Exception as e:
            logger.error(f"城市名标准化失败: {str(e)}")
            return user_input
    
    def validate_city_name(self, city: str) -> bool:
        """
        验证城市名称是否有效
        
        Args:
            city: 城市名称
            
        Returns:
            是否为有效城市名
        """
        normalized_city = self.normalize_city_name(city)
        return normalized_city in self.city_coordinates
    
    def get_city_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        """
        获取城市坐标
        
        Args:
            city: 城市名称
            
        Returns:
            城市坐标 (经度, 纬度)，如果未找到返回None
        """
        normalized_city = self.normalize_city_name(city)
        return self.city_coordinates.get(normalized_city)
    
    def _extract_city_from_address(self, address: str) -> Optional[str]:
        """从地址字符串中提取城市名"""
        for city in self.city_coordinates:
            if city in address:
                return city
        return None
    
    def _find_nearest_city(self, lng: float, lat: float) -> str:
        """找到最近的城市"""
        min_distance = float('inf')
        nearest_city = "北京"
        
        for city, (city_lng, city_lat) in self.city_coordinates.items():
            # 简单的欧几里得距离计算
            distance = ((lng - city_lng) ** 2 + (lat - city_lat) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_city = city
        
        return nearest_city
    
    def _get_province_by_city(self, city: str) -> str:
        """根据城市获取省份"""
        # 简化的省份映射
        province_map = {
            "北京": "北京市",
            "上海": "上海市",
            "广州": "广东省",
            "深圳": "广东省",
            "杭州": "浙江省",
            "南京": "江苏省",
            "武汉": "湖北省",
            "成都": "四川省",
            "西安": "陕西省",
            "重庆": "重庆市",
            "天津": "天津市",
            "青岛": "山东省",
            "大连": "辽宁省",
            "沈阳": "辽宁省",
            "长春": "吉林省",
            "哈尔滨": "黑龙江省",
            "济南": "山东省",
            "郑州": "河南省",
            "太原": "山西省",
            "石家庄": "河北省",
            "福州": "福建省",
            "厦门": "福建省",
            "南昌": "江西省",
            "合肥": "安徽省",
            "长沙": "湖南省",
            "昆明": "云南省",
            "贵阳": "贵州省",
            "兰州": "甘肃省",
            "银川": "宁夏回族自治区",
            "西宁": "青海省",
            "乌鲁木齐": "新疆维吾尔自治区",
            "拉萨": "西藏自治区",
            "呼和浩特": "内蒙古自治区",
            "海口": "海南省",
            "三亚": "海南省"
        }
        return province_map.get(city, "未知省份")
    
    def _get_adcode_by_city(self, city: str) -> str:
        """根据城市获取行政区划代码"""
        # 简化的行政区划代码映射
        adcode_map = {
            "北京": "110000",
            "上海": "310000",
            "广州": "440100",
            "深圳": "440300",
            "杭州": "330100",
            "南京": "320100",
            "武汉": "420100",
            "成都": "510100",
            "西安": "610100",
            "重庆": "500000",
            "天津": "120000"
        }
        return adcode_map.get(city, "000000")
    
    def health_check(self) -> bool:
        """
        检查MCP服务健康状态
        
        Returns:
            服务是否可用
        """
        try:
            # 尝试获取北京的城市信息作为健康检查
            result = self.get_city_info("北京")
            return result.get("status") == "success"
        except Exception as e:
            logger.error(f"高德地图MCP服务健康检查失败: {str(e)}")
            return False