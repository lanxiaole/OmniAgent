# weather_tool.py - 天气查询工具
# 功能：城市名称智能解析 + 高德天气 API 调用
import requests
import json
import time
import os
from langchain_core.tools import tool
from agent_core.logger import get_logger
from agent_core.config.settings import get_amap_api_key

logger = get_logger(__name__)

# 城市编码映射表：城市全名 -> 行政区划代码（adcode），共 3202 个城市
CITY_ADCODE = {}
# 城市简称映射表：城市简称 -> 城市全名，共 3129 个别名（自动从 CITY_ADCODE 构建）
BARE_NAME_MAP = {}

# 常见行政区划后缀，用于剥离后缀生成简称
SUFFIXES = ['特别行政区', '自治州', '省', '市', '区', '县', '盟', '旗']

# 同名消歧优先级：当多个行政区简称相同时（如"朝阳"既有朝阳市又有朝阳区），
# 优先选择市级 > 省级 > 自治州 > 盟 > 区级 > 县级 > 旗 > 特别行政区
SUFFIX_PRIORITY = {
    '市': 1, '省': 2, '自治州': 3, '盟': 4,
    '区': 5, '县': 6, '旗': 7, '特别行政区': 8
}


def strip_suffix(name: str) -> tuple:
    """剥离城市名的行政区划后缀，返回 (简称, 后缀)。无后缀时返回 (原名, None)。"""
    for suf in SUFFIXES:
        if name.endswith(suf):
            return name[:-len(suf)], suf
    return name, None


def load_city_codes():
    """加载城市编码 JSON 文件并自动构建简称映射表。"""
    global CITY_ADCODE, BARE_NAME_MAP
    # 从 resources 目录加载城市编码数据
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "city_codes.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            CITY_ADCODE = json.load(f)
        logger.info(f"成功加载城市编码，共 {len(CITY_ADCODE)} 个城市")
    except Exception as e:
        logger.error(f"加载城市编码失败: {e}")
        CITY_ADCODE = {}
        BARE_NAME_MAP = {}
        return

    # 遍历所有城市，剥离后缀生成简称 -> 全名的映射
    # 对于同名冲突（如"朝阳"），选择优先级最高的（市级 > 区县级）
    bare_candidates = {}
    for full_name in CITY_ADCODE:
        bare, suffix = strip_suffix(full_name)
        if suffix is None:
            continue
        priority = SUFFIX_PRIORITY.get(suffix, 99)
        if bare not in bare_candidates or priority < bare_candidates[bare][0]:
            bare_candidates[bare] = (priority, full_name)

    BARE_NAME_MAP = {bare: full_name for bare, (_, full_name) in bare_candidates.items()}
    logger.info(f"构建城市别名映射，共 {len(BARE_NAME_MAP)} 个别名")


# 模块加载时自动初始化城市数据
load_city_codes()


def extract_city_name(input_city):
    """将用户输入的城市名（可能带省份前缀或无后缀）解析为 CITY_ADCODE 中的标准城市全名。

    匹配策略（按优先级）：
    1. 精确匹配 CITY_ADCODE（如"东莞市"）
    2. 简称匹配 BARE_NAME_MAP（如"东莞" -> "东莞市"）
    3. 按行政区划后缀分割后，从右向左尝试匹配（如"云南昆明市" -> 按"市"分割 -> "昆明" -> "昆明市"）
    4. 子串匹配：尝试匹配分割后的子串尾部（处理如"东莞城市"这类情况）
    5. 全串子串回退：从输入字符串中逐步截取尾部尝试匹配
    """
    if not input_city or not input_city.strip():
        return input_city

    input_city = input_city.strip()

    # 策略1: 精确匹配城市全名
    if input_city in CITY_ADCODE:
        return input_city

    # 策略2: 通过简称映射表匹配（如 "东莞" -> "东莞市"）
    if input_city in BARE_NAME_MAP:
        return BARE_NAME_MAP[input_city]

    # 策略3: 按常见行政区划后缀分割，从右向左查找（如"云南昆明市"分割为["云南昆明", ""]，取"云南昆明"再查）
    for sep in ['省', '市', '区', '县', '自治州', '盟', '旗']:
        if sep in input_city:
            parts = input_city.split(sep)
            for i in range(len(parts) - 1, -1, -1):
                sub_city = parts[i].strip()
                if not sub_city:
                    continue
                # 直接匹配分割后的片段
                if sub_city in CITY_ADCODE:
                    return sub_city
                if sub_city in BARE_NAME_MAP:
                    return BARE_NAME_MAP[sub_city]
                # 子串回退：尝试从片段尾部逐步截取匹配
                for start in range(1, len(sub_city)):
                    suffix = sub_city[start:]
                    if suffix in BARE_NAME_MAP:
                        return BARE_NAME_MAP[suffix]
                    if suffix in CITY_ADCODE:
                        return suffix

    # 策略4: 全串子串回退，从未匹配到的场景做最终兜底
    for start in range(1, len(input_city)):
        suffix = input_city[start:]
        if suffix in BARE_NAME_MAP:
            return BARE_NAME_MAP[suffix]
        if suffix in CITY_ADCODE:
            return suffix

    # 所有策略均失败，返回原始输入
    return input_city


# 天气数据缓存：避免短时间内重复请求同一城市 API
_cache = {}
CACHE_EXPIRY = 600  # 缓存有效期 10 分钟


@tool
def get_weather(city: str) -> str:
    """获取指定城市的当前天气和未来3天预报。支持城市全名（如"东莞市"）和简称（如"东莞"）。"""
    try:
        # 检查缓存：10分钟内直接返回之前的查询结果
        current_time = time.time()
        if city in _cache:
            cached_result, timestamp = _cache[city]
            if current_time - timestamp < CACHE_EXPIRY:
                logger.debug(f"使用缓存的天气数据: {city}")
                return cached_result

        api_key = get_amap_api_key()
        if not api_key:
            return "错误：未配置 AMAP_API_KEY 环境变量"

        # 将用户输入的城市名解析为标准城市全名
        processed_city = extract_city_name(city)

        # 通过城市全名获取 adcode（行政区划代码）
        adcode = CITY_ADCODE.get(processed_city)
        if not adcode:
            logger.warning(f"城市未找到: 原始输入='{city}', 处理后='{processed_city}'")
            return "暂不支持该城市"

        # 构造两个 API URL：base（实时天气）和 all（预报天气）
        base_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={api_key}&extensions=base"
        all_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={api_key}&extensions=all"

        # 设置请求头，模拟浏览器请求
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # 并行请求实时天气数据
        base_response = requests.get(base_url, headers=headers, timeout=5)
        base_data = base_response.json()

        # 并行请求预报天气数据
        all_response = requests.get(all_url, headers=headers, timeout=5)
        all_data = all_response.json()

        # 检查 API 返回状态（status=1 表示成功）
        if base_data.get("status") != "1":
            return f"获取天气失败：{base_data.get('info', '未知错误')}"
        if all_data.get("status") != "1":
            return f"获取天气失败：{all_data.get('info', '未知错误')}"

        # 解析实时天气数据
        lives = base_data.get("lives", [])
        current_weather = ""
        if lives:
            live_data = lives[0]
            province = live_data.get("province", "未知")      # 省份
            city_name = live_data.get("city", "未知")        # 城市名称
            weather = live_data.get("weather", "未知")      # 天气现象
            temperature = live_data.get("temperature", "未知")  # 温度（字符串）
            winddirection = live_data.get("winddirection", "未知")  # 风向
            windpower = live_data.get("windpower", "未知")    # 风力
            humidity = live_data.get("humidity", "未知")      # 湿度
            reporttime = live_data.get("reporttime", "未知")  # 数据发布时间
            temperature_float = live_data.get("temperature_float", "未知")  # 温度（浮点）
            humidity_float = live_data.get("humidity_float", "未知")  # 湿度（浮点）

            # 格式化实时天气信息
            current_weather = f"{city}当前天气：\n"
            current_weather += f"省份：{province}\n"
            current_weather += f"城市：{city_name}\n"
            current_weather += f"天气现象：{weather}\n"
            current_weather += f"实时温度：{temperature}°C ({temperature_float}°C)\n"
            current_weather += f"风向：{winddirection}\n"
            current_weather += f"风力：{windpower}级\n"
            current_weather += f"空气湿度：{humidity}% ({humidity_float}%)\n"
            current_weather += f"数据发布时间：{reporttime}\n"

        # 解析未来三天预报数据
        forecast_lines = []
        forecasts = all_data.get("forecasts", [])
        if forecasts:
            forecast_data = forecasts[0]
            forecast_city = forecast_data.get("city", "未知")      # 预报城市
            forecast_province = forecast_data.get("province", "未知")  # 预报省份
            forecast_reporttime = forecast_data.get("reporttime", "未知")  # 预报发布时间

            casts = forecast_data.get("casts", [])
            if casts:
                forecast_lines.append(f"\n未来三天预报（{forecast_province} {forecast_city}）：\n")
                forecast_lines.append(f"预报发布时间：{forecast_reporttime}\n")

                # casts 数组中 casts[0] 是今天，casts[1-3] 是未来3天
                for i in range(1, min(4, len(casts))):
                    cast = casts[i]
                    date = cast.get("date", "未知")           # 日期
                    week = cast.get("week", "未知")           # 星期
                    dayweather = cast.get("dayweather", "未知")  # 白天天气
                    nightweather = cast.get("nightweather", "未知")  # 夜间天气
                    daytemp = cast.get("daytemp", "未知")      # 白天温度
                    nighttemp = cast.get("nighttemp", "未知")  # 夜间温度
                    daywind = cast.get("daywind", "未知")     # 白天风向
                    nightwind = cast.get("nightwind", "未知")  # 夜间风向
                    daypower = cast.get("daypower", "未知")   # 白天风力
                    nightpower = cast.get("nightpower", "未知")  # 夜间风力

                    # 格式化每一天的预报信息
                    forecast_line = f"{date}（周{week}）：\n"
                    forecast_line += f"  白天：{dayweather}，{daywind}风{daypower}级，温度{daytemp}°C\n"
                    forecast_line += f"  夜间：{nightweather}，{nightwind}风{nightpower}级，温度{nighttemp}°C\n"
                    forecast_lines.append(forecast_line)

        # 合并实时天气和预报结果
        result = current_weather
        if forecast_lines:
            result += "".join(forecast_lines)

        # 写入缓存
        _cache[city] = (result, current_time)

        logger.debug(f"获取天气成功: {result}")
        return result

    # 异常处理：分别处理不同类型的错误
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