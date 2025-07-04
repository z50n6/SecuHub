import json
import re

# 读取原始数据
with open('website.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

result = []

for block in data:
    type1 = block.get('type1', '').strip()
    for item in block.get('items', []):
        type2 = item.get('type2', '').strip()
        category = f"{type1}/{type2}"
        for entry in item.get('list', []):
            name = entry.get('name', '')
            remark = entry.get('remark', '')
            url = entry.get('url', '')
            # 去除&LinkId=xxx及其后内容
            url = re.sub(r'&LinkId=\d+.*$', '', url)
            icon = entry.get('icon', '')
            result.append({
                'category': category,
                'name': name,
                'remark': remark,
                'url': url,
                'icon': icon
            })

# 输出到新文件
with open('website_flat.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2) 