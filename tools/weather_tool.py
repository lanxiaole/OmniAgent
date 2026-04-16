import requests
from langchain_core.tools import tool
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)

# 常用城市拼音映射
CITY_PINYIN_MAP = {
    "北京": "beijing",
    "上海": "shanghai",
    "广州": "guangzhou",
    "深圳": "shenzhen",
    "昆明": "kunming",
    "成都": "chengdu",
    "重庆": "chongqing",
    "杭州": "hangzhou",
    "南京": "nanjing",
    "武汉": "wuhan",
    "西安": "xian",
    "长沙": "changsha",
    "沈阳": "shenyang",
    "哈尔滨": "haerbin",
    "郑州": "zhengzhou",
    "济南": "jinan",
    "青岛": "qingdao",
    "苏州": "suzhou",
    "福州": "fuzhou",
    "厦门": "xiamen"
}

@tool
def get_weather(city: str) -> str:
    """获取指定城市的当前天气状况和温度。用户询问天气时调用此工具。"""
    try:
        # 将中文城市名转换为拼音
        city_pinyin = CITY_PINYIN_MAP.get(city, city.lower())
        
        # 构造 URL
        url = f"http://wttr.in/{city_pinyin}?format=%C+%t"
        
        # 设置请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 发送 GET 请求
        response = requests.get(url, headers=headers, timeout=5)
        
        # 检查响应状态码
        if response.status_code == 200:
            # 去除换行并返回
            weather_info = response.text.strip()
            logger.debug(f"获取天气成功: {city} - {weather_info}")
            return weather_info
        else:
            logger.error(f"获取天气失败，状态码: {response.status_code}")
            return f"抱歉，无法获取 {city} 的天气信息。"
    except requests.exceptions.Timeout:
        logger.error("获取天气超时")
        return "抱歉，获取天气超时，请稍后再试。"
    except requests.exceptions.ConnectionError:
        logger.error("获取天气连接错误")
        return "抱歉，无法连接到天气服务器，请检查网络连接。"
    except Exception as e:
        logger.error(f"获取天气错误: {e}")
        return "抱歉，获取天气信息时出错。"
