#!/usr/bin/env python3
# 解析城市编码 Excel 文件

import pandas as pd
import json

# 读取 Excel 文件
excel_path = r"c:\Users\lanxiaole\Desktop\project\OmniAgent\resources\AMap_adcode_citycode.xlsx"
df = pd.read_excel(excel_path)

# 查看前几行数据，了解数据结构
print("Excel 文件前 5 行数据：")
print(df.head())

# 查看列名
print("\nExcel 列名：")
print(df.columns.tolist())

# 提取城市名称和编码
city_codes = {}

# 使用正确的列名 '中文名' 和 'adcode'
if '中文名' in df.columns and 'adcode' in df.columns:
    for index, row in df.iterrows():
        city_name = str(row['中文名']).strip()
        adcode = str(row['adcode']).strip()
        if city_name and adcode and city_name != '中国':  # 跳过中国
            city_codes[city_name] = adcode
else:
    # 尝试其他可能的列名
    print("\n尝试自动识别列名...")
    for col in df.columns:
        print(f"列名: {col}, 示例值: {df[col].iloc[0] if len(df) > 0 else '无'}")

# 保存为 JSON 文件
output_json = r"c:\Users\lanxiaole\Desktop\project\OmniAgent\resources\city_codes.json"
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(city_codes, f, ensure_ascii=False, indent=2)

print(f"\n解析完成，共提取 {len(city_codes)} 个城市编码")
print(f"城市编码已保存到: {output_json}")

# 查看前 20 个城市编码
print("\n前 20 个城市编码：")
for i, (city, code) in enumerate(list(city_codes.items())[:20]):
    print(f"{i+1}. {city}: {code}")
