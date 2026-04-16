import re

lines = open('../app/services/sample_library.py', encoding='utf-8').readlines()
cats = ['脐橙','苹果','草莓','桃子','葡萄','西瓜','芒果','沃柑','石榴','蔬菜','粮油','蓝莓','樱桃','猕猴桃']

current_cat = None
in_section = None
last_verified = {}

for i, line in enumerate(lines, 1):
    for c in cats:
        if f'"{c}"' in line and '{' in line:
            current_cat = c
            in_section = None
            break
    if current_cat:
        if '"script"' in line and '[' in line:
            in_section = 'script'
        elif '"topic"' in line and '[' in line:
            in_section = 'topic'
        elif '"live_module"' in line:
            in_section = None
        if 'verified_hit' in line and in_section:
            key = f'{current_cat}_{in_section}'
            last_verified[key] = i

for k in sorted(last_verified.keys()):
    print(f'{k}: line {last_verified[k]}')
