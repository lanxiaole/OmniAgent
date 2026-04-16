import requests
import json
import time
import os
from langchain_core.tools import tool
from logger import get_logger
from config.settings import AMAP_API_KEY

# 创建 logger
logger = get_logger(__name__)

# 加载城市编码映射表
CITY_ADCODE = {}

# 加载城市编码从 JSON 文件
def load_city_codes():
    global CITY_ADCODE
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "city_codes.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            CITY_ADCODE = json.load(f)
        logger.info(f"成功加载城市编码，共 {len(CITY_ADCODE)} 个城市")
    except Exception as e:
        logger.error(f"加载城市编码失败: {e}")
        # 如果加载失败，使用默认的城市编码
        CITY_ADCODE = {
            "北京": "110000",
            "上海": "310000",
            "广州": "440100",
            "深圳": "440300",
            "杭州": "330100",
            "南京": "320100",
            "武汉": "420100",
            "成都": "510100",
            "重庆": "500000",
            "西安": "610100",
            "长沙": "430100",
            "沈阳": "210100",
            "哈尔滨": "230100",
            "济南": "370100",
            "青岛": "370200",
            "大连": "210200",
            "厦门": "350200",
            "福州": "350100",
            "宁波": "330200",
            "苏州": "320500",
            "天津": "120000",
            "郑州": "410100",
            "昆明": "530100",
            "贵阳": "520100",
            "南宁": "450100",
            "南昌": "360100",
            "合肥": "340100",
            "太原": "140100",
            "石家庄": "130100",
            "乌鲁木齐": "650100",
            "兰州": "620100",
            "西宁": "630100",
            "银川": "640100",
            "拉萨": "540100",
            "海口": "460100",
            "呼和浩特": "150100"
        }

# 加载城市编码
load_city_codes()

# 城市名称映射，将简洁城市名映射到完整城市名
CITY_NAME_MAPPING = {
    "北京": "北京市",
    "上海": "上海市",
    "天津": "天津市",
    "重庆": "重庆市",
    "广州": "广州市",
    "深圳": "深圳市",
    "杭州": "杭州市",
    "南京": "南京市",
    "武汉": "武汉市",
    "成都": "成都市",
    "西安": "西安市",
    "长沙": "长沙市",
    "沈阳": "沈阳市",
    "哈尔滨": "哈尔滨市",
    "济南": "济南市",
    "青岛": "青岛市",
    "大连": "大连市",
    "厦门": "厦门市",
    "福州": "福州市",
    "宁波": "宁波市",
    "苏州": "苏州市",
    "郑州": "郑州市",
    "昆明": "昆明市",
    "贵阳": "贵阳市",
    "南宁": "南宁市",
    "南昌": "南昌市",
    "合肥": "合肥市",
    "太原": "太原市",
    "石家庄": "石家庄市",
    "乌鲁木齐": "乌鲁木齐市",
    "兰州": "兰州市",
    "西宁": "西宁市",
    "银川": "银川市",
    "拉萨": "拉萨市",
    "海口": "海口市",
    "呼和浩特": "呼和浩特市"
}

# 处理用户输入的城市名，提取出最具体的地名
def extract_city_name(input_city):
    # 首先尝试直接匹配
    if input_city in CITY_ADCODE:
        return input_city
    
    # 尝试匹配映射后的城市名
    mapped_city = CITY_NAME_MAPPING.get(input_city, input_city)
    if mapped_city in CITY_ADCODE:
        return mapped_city
    
    # 尝试提取最后一个地名（例如"昆明市呈贡区" -> "呈贡区"）
    parts = input_city.split(" ")
    for i in range(len(parts) - 1, -1, -1):
        sub_city = " ".join(parts[i:])
        if sub_city in CITY_ADCODE:
            return sub_city
        # 尝试映射后的城市名
        mapped_sub_city = CITY_NAME_MAPPING.get(sub_city, sub_city)
        if mapped_sub_city in CITY_ADCODE:
            return mapped_sub_city
    
    # 尝试按常见分隔符分割（如"市"、"区"、"县"等）
    separators = ["市", "区", "县", "省", "州", "盟", "旗"]
    for sep in separators:
        if sep in input_city:
            # 提取分隔符后面的部分
            parts = input_city.split(sep)
            for i in range(len(parts) - 1, -1, -1):
                sub_city = parts[i].strip()
                if sub_city:
                    if sub_city in CITY_ADCODE:
                        return sub_city
                    mapped_sub_city = CITY_NAME_MAPPING.get(sub_city, sub_city)
                    if mapped_sub_city in CITY_ADCODE:
                        return mapped_sub_city
    
    # 如果都找不到，返回原始输入
    return input_city

# 缓存字典，格式: {city: (result, timestamp)}
_cache = {}
# 缓存有效期（秒）
CACHE_EXPIRY = 600

@tool
def get_weather(city: str) -> str:
    """获取指定城市的当前天气和未来3天预报"""
    try:
        # 检查缓存
        current_time = time.time()
        if city in _cache:
            cached_result, timestamp = _cache[city]
            if current_time - timestamp < CACHE_EXPIRY:
                logger.debug(f"使用缓存的天气数据: {city}")
                return cached_result
        
        # 使用从 settings.py 导入的 API key
        api_key = AMAP_API_KEY
        if not api_key:
            return "错误：未配置 AMAP_API_KEY 环境变量"
        
        # 处理用户输入的城市名，提取出最具体的地名
        processed_city = extract_city_name(city)
        
        # 将城市名转换为 adcode
        adcode = CITY_ADCODE.get(processed_city)
        if not adcode:
            return "暂不支持该城市"
        
        # 构造 URL，先获取实时天气数据（extensions=base）
        base_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={api_key}&extensions=base"
        # 构造 URL，获取预报天气数据（extensions=all）
        all_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={api_key}&extensions=all"
        
        # 设置请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 发送 GET 请求获取实时天气
        base_response = requests.get(base_url, headers=headers, timeout=5)
        base_data = base_response.json()
        
        # 发送 GET 请求获取预报天气
        all_response = requests.get(all_url, headers=headers, timeout=5)
        all_data = all_response.json()
        
        # 检查 status 是否为 "1"
        if base_data.get("status") != "1":
            return f"获取天气失败：{base_data.get('info', '未知错误')}"
        if all_data.get("status") != "1":
            return f"获取天气失败：{all_data.get('info', '未知错误')}"
        
        # 提取实时天气信息
        lives = base_data.get("lives", [])
        current_weather = ""
        if lives:
            live_data = lives[0]
            province = live_data.get("province", "未知")
            city_name = live_data.get("city", "未知")
            weather = live_data.get("weather", "未知")
            temperature = live_data.get("temperature", "未知")
            winddirection = live_data.get("winddirection", "未知")
            windpower = live_data.get("windpower", "未知")
            humidity = live_data.get("humidity", "未知")
            reporttime = live_data.get("reporttime", "未知")
            temperature_float = live_data.get("temperature_float", "未知")
            humidity_float = live_data.get("humidity_float", "未知")
            
            current_weather = f"{city}当前天气：\n"
            current_weather += f"省份：{province}\n"
            current_weather += f"城市：{city_name}\n"
            current_weather += f"天气现象：{weather}\n"
            current_weather += f"实时温度：{temperature}°C ({temperature_float}°C)\n"
            current_weather += f"风向：{winddirection}\n"
            current_weather += f"风力：{windpower}级\n"
            current_weather += f"空气湿度：{humidity}% ({humidity_float}%)\n"
            current_weather += f"数据发布时间：{reporttime}\n"
        
        # 提取未来3天预报
        forecast_lines = []
        forecasts = all_data.get("forecasts", [])
        if forecasts:
            forecast_data = forecasts[0]
            forecast_city = forecast_data.get("city", "未知")
            forecast_province = forecast_data.get("province", "未知")
            forecast_reporttime = forecast_data.get("reporttime", "未知")
            
            casts = forecast_data.get("casts", [])
            if casts:
                forecast_lines.append(f"\n未来三天预报（{forecast_province} {forecast_city}）：\n")
                forecast_lines.append(f"预报发布时间：{forecast_reporttime}\n")
                
                # 取 casts[1], casts[2], casts[3] 作为未来3天预报
                for i in range(1, min(4, len(casts))):
                    cast = casts[i]
                    date = cast.get("date", "未知")
                    week = cast.get("week", "未知")
                    dayweather = cast.get("dayweather", "未知")
                    nightweather = cast.get("nightweather", "未知")
                    daytemp = cast.get("daytemp", "未知")
                    nighttemp = cast.get("nighttemp", "未知")
                    daywind = cast.get("daywind", "未知")
                    nightwind = cast.get("nightwind", "未知")
                    daypower = cast.get("daypower", "未知")
                    nightpower = cast.get("nightpower", "未知")
                    
                    forecast_line = f"{date}（周{week}）：\n"
                    forecast_line += f"  白天：{dayweather}，{daywind}风{daypower}级，温度{daytemp}°C\n"
                    forecast_line += f"  夜间：{nightweather}，{nightwind}风{nightpower}级，温度{nighttemp}°C\n"
                    forecast_lines.append(forecast_line)
        
        # 格式化为字符串
        result = current_weather
        if forecast_lines:
            result += "".join(forecast_lines)
        
        # 更新缓存
        _cache[city] = (result, current_time)
        
        logger.debug(f"获取天气成功: {result}")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"请求天气 API 失败: {e}")
        return "抱歉，获取天气信息时网络错误，请稍后再试"
    except json.JSONDecodeError:
        logger.error("解析天气数据失败")
        return "抱歉，解析天气数据失败，请稍后再试"
    except KeyError as e:
        logger.error(f"天气数据缺少必要字段: {e}")
        return "抱歉，天气数据格式错误，请稍后再试"
    except Exception as e:
        logger.error(f"获取天气时发生未知错误: {e}")
        return "抱歉，获取天气信息时出错，请稍后再试"
