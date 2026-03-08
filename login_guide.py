#!/usr/bin/env python3
"""
网站 Cookie 配置工具

支持配置多个网站的 Cookie，用于爬取需要登录的内容。
"""
import json
from pathlib import Path

# Cookie 配置文件路径
COOKIE_DIR = Path('/root/.openclaw/workspace/link-collector/cookies')
COOKIE_DIR.mkdir(parents=True, exist_ok=True)

# 网站配置
SITES = {
    'xueqiu': {
        'name': '雪球',
        'login_url': 'https://xueqiu.com/',
        'guide': '''
如何获取雪球 Cookie：
1. 在浏览器中打开 https://xueqiu.com/
2. 登录你的账号
3. 按 F12 打开开发者工具
4. 切换到 "网络" (Network) 标签
5. 刷新页面
6. 点击任意一个请求
7. 在右侧找到 "请求头" (Request Headers)
8. 复制 Cookie 字段的值
'''
    },
    'dianping': {
        'name': '大众点评',
        'login_url': 'https://www.dianping.com/',
        'guide': '''
如何获取大众点评 Cookie：
1. 在浏览器中打开 https://www.dianping.com/
2. 登录你的账号
3. 按 F12 打开开发者工具
4. 切换到 "网络" (Network) 标签
5. 刷新页面
6. 点击任意一个请求
7. 在右侧找到 "请求头" (Request Headers)
8. 复制 Cookie 字段的值
'''
    },
    'xiaohongshu': {
        'name': '小红书',
        'login_url': 'https://www.xiaohongshu.com/',
        'guide': '''
如何获取小红书 Cookie：
1. 在浏览器中打开 https://www.xiaohongshu.com/
2. 登录你的账号
3. 按 F12 打开开发者工具
4. 切换到 "网络" (Network) 标签
5. 刷新页面
6. 点击任意一个请求
7. 在右侧找到 "请求头" (Request Headers)
8. 复制 Cookie 字段的值
'''
    }
}


def save_cookie(site: str, cookie_str: str):
    """保存 Cookie"""
    if site not in SITES:
        print(f"❌ 不支持的网站: {site}")
        print(f"   支持的网站: {', '.join(SITES.keys())}")
        return
    
    # 解析 Cookie 字符串
    cookies = []
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': SITES[site]['login_url'].split('//')[1].split('/')[0]
            })
    
    # 保存
    cookie_file = COOKIE_DIR / f'{site}.json'
    with open(cookie_file, 'w') as f:
        json.dump(cookies, f, indent=2)
    
    print(f"✅ {SITES[site]['name']} Cookie 已保存")
    print(f"   文件: {cookie_file}")


def load_cookie(site: str) -> list:
    """加载 Cookie"""
    cookie_file = COOKIE_DIR / f'{site}.json'
    if cookie_file.exists():
        with open(cookie_file, 'r') as f:
            return json.load(f)
    return []


def show_guide(site: str = None):
    """显示获取 Cookie 的指南"""
    if site and site in SITES:
        print(f"\n{'='*60}")
        print(f"  {SITES[site]['name']} Cookie 获取指南")
        print(f"{'='*60}")
        print(SITES[site]['guide'])
    else:
        print("\n支持的网站:")
        for key, info in SITES.items():
            cookie_file = COOKIE_DIR / f'{key}.json'
            status = "✅ 已配置" if cookie_file.exists() else "❌ 未配置"
            print(f"  - {info['name']} ({key}): {status}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        show_guide()
        print("\n使用方法:")
        print("  python login_guide.py <网站> <Cookie字符串>")
        print("  python login_guide.py guide <网站>")
        print("\n示例:")
        print("  python login_guide.py xueqiu 'xq_a_token=xxx; xq_r_token=xxx'")
        print("  python login_guide.py guide xueqiu")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == 'guide' and len(sys.argv) >= 3:
        show_guide(sys.argv[2])
    elif command in SITES and len(sys.argv) >= 3:
        save_cookie(command, sys.argv[2])
    else:
        print(f"❌ 未知命令或参数不足")
        show_guide()