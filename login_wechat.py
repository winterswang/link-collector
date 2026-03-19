#!/usr/bin/env python3
"""
微信自动登录脚本
使用 Playwright 模拟登录并保存 Cookie
"""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# Cookie 保存路径
COOKIE_FILE = Path('/root/.openclaw/workspace/link-collector/cookies/wechat.json')

def login_wechat():
    """登录微信公众平台并保存 Cookie"""
    
    COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        # 启动浏览器（需要非无头模式才能看到二维码）
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("1. 访问微信公众平台...")
        page.goto('https://mp.weixin.qq.com/')
        time.sleep(3)
        
        print("2. 请在浏览器中扫码登录微信公众平台...")
        print("   等待登录完成（最多 120 秒）...")
        
        # 等待用户扫码登录，最多 120 秒
        # 检测登录成功的标志：页面跳转到后台主页或出现用户信息
        try:
            page.wait_for_url('**/cgi-bin/home*', timeout=120000)
            print("   ✅ 检测到登录成功，跳转到后台")
        except Exception as e:
            print(f"   ⚠️ 等待超时: {e}")
            # 尝试检测其他登录成功标志
            try:
                page.wait_for_selector('.account_info', timeout=10000)
                print("   ✅ 检测到用户信息，登录成功")
            except:
                print("   ❌ 未检测到登录成功")
        
        time.sleep(3)
        
        # 保存 Cookie
        print("3. 保存 Cookie...")
        cookies = context.cookies()
        
        with open(COOKIE_FILE, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print(f"   ✅ Cookie 已保存到: {COOKIE_FILE}")
        
        # 测试访问文章页面
        print("4. 测试访问文章页面...")
        test_url = 'https://mp.weixin.qq.com/s?__biz=MzUxNjg4NDEzNA==&mid=2247532272&idx=1&sn=e4ea5c1fecc792467f63a79691a37359'
        page.goto(test_url)
        time.sleep(5)
        
        # 截图
        screenshot_file = COOKIE_FILE.parent / 'wechat_test.png'
        page.screenshot(path=str(screenshot_file))
        print(f"   截图已保存: {screenshot_file}")
        
        # 获取页面标题和内容
        title = page.title()
        print(f"   页面标题: {title}")
        
        # 检查是否需要验证
        if '环境异常' in title or '验证' in title:
            print("   ⚠️ 仍然需要验证，可能 cookie 不够")
        else:
            print("   ✅ 访问成功")
        
        browser.close()
        print("\n登录流程完成！")

if __name__ == '__main__':
    login_wechat()