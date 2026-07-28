import requests
import json
import time
import os
from langchain_core.tools import tool
from agent_core.logger import get_logger
from agent_core.config.settings import AMAP_API_KEY

logger = get_logger(__name__)

CITY_ADCODE = {}
BARE_NAME_MAP = {}

SUFFIXES = ['特别行政区', '自治州', '省', '市', '区', '县', '盟', '旗']

SUFFIX_PRIORITY = {
    '市': 1, '省': 2, '自治州': 3, '盟': 4,
    '区': 5, '县': 6, '旗': 7, '特别行政区': 8
}


def strip_suffix(name: str) -> tuple:
    for suf in SUFFIXES:
        if name.endswith(suf):
            return name[:-len(suf)], suf
    return name, None


def load_city_codes():
    global CITY_ADCODE, BARE_NAME_MAP
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


load_city_codes()


def extract_city_name(input_city):
    if not input_city or not input_city.strip():
        return input_city

    input_city = input_city.strip()

    if input_city in CITY_ADCODE:
        return input_city

    if input_city in BARE_NAME_MAP:
        return BARE_NAME_MAP[input_city]

    for sep in ['省', '市', '区', '县', '自治州', '盟', '旗']:
        if sep in input_city:
            parts = input_city.split(sep)
            for i in range(len(parts) - 1, -1, -1):
                sub_city = parts[i].strip()
                if not sub_city:
                    continue
                if sub_city in CITY_ADCODE:
                    return sub_city
                if sub_city in BARE_NAME_MAP:
                    return BARE_NAME_MAP[sub_city]
                for start in range(1, len(sub_city)):
                    suffix = sub_city[start:]
                    if suffix in BARE_NAME_MAP:
                        return BARE_NAME_MAP[suffix]
                    if suffix in CITY_ADCODE:
                        return suffix

    for start in range(1, len(input_city)):
        suffix = input_city[start:]
        if suffix in BARE_NAME_MAP:
            return BARE_NAME_MAP[suffix]
        if suffix in CITY_ADCODE:
            return suffix

    return input_city


_cache = {}
CACHE_EXPIRY = 600


@tool
def get_weather(city: str) -> str:
    """获取指定城市的当前天气和未来3天预报。支持城市全名（如"东莞市"）和简称（如"东莞"）。"""
    try:
        current_time = time.time()
        if city in _cache:
            cached_result, timestamp = _cache[city]
            if current_time - timestamp < CACHE_EXPIRY:
                logger.debug(f"使用缓存的天气数据: {city}")
                return cached_result

        api_key = AMAP_API_KEY
        if not api_key:
            return "错误：未配置 AMAP_API_KEY 环境变量"

        processed_city = extract_city_name(city)

        adcode = CITY_ADCODE.get(processed_city)
        if not adcode:
            logger.warning(f"城市未找到: 原始输入='{city}', 处理后='{processed_city}'")
            return "暂不支持该城市"

        base_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={api_key}&extensions=base"
        all_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={api_key}&extensions=all"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        base_response = requests.get(base_url, headers=headers, timeout=5)
        base_data = base_response.json()

        all_response = requests.get(all_url, headers=headers, timeout=5)
        all_data = all_response.json()

        if base_data.get("status") != "1":
            return f"获取天气失败：{base_data.get('info', '未知错误')}"
        if all_data.get("status") != "1":
            return f"获取天气失败：{all_data.get('info', '未知错误')}"

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

        result = current_weather
        if forecast_lines:
            result += "".join(forecast_lines)

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