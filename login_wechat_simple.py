#!/usr/bin/env python3
"""
微信公众平台登录 - 生成登录二维码
"""
import json
import time
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIE_FILE = Path('/root/.openclaw/workspace/link-collector/cookies/wechat.json')

def get_qrcode_and_login():
    """获取登录二维码并保存 cookie"""
    COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        # 尝试使用已有的浏览器或启动新的
        try:
            browser = p.chromium.launch(headless=False)
        except Exception as e:
            print(f"启动浏览器失败: {e}")
            print("尝试使用系统浏览器...")
            browser = p.chromium.launch(headless=False, channel="chrome")
        
        context = browser.new_context(viewport={'width': 400, 'height': 600})
        page = context.new_page()
        
        print("1. 访问微信公众平台登录页...")
        page.goto('https://mp.weixin.qq.com/')
        
        # 等待二维码加载
        print("2. 等待二维码加载...")
        time.sleep(3)
        
        # 尝试找到二维码图片
        qr_img = page.query_selector('.qrcode img, .qrcode canvas, img.qrcode')
        
        if qr_img:
            print("   找到二维码!")
            # 获取页面截图（二维码在页面上）
            screenshot_file = COOKIE_FILE.parent / 'wechat_qrcode.png'
            page.screenshot(path=str(screenshot_file), full_page=False)
            print(f"   二维码截图已保存: {screenshot_file}")
            print("   请用微信扫描二维码登录")
        else:
            print("   未找到二维码，尝试截图...")
            screenshot_file = COOKIE_FILE.parent / 'wechat_login.png'
            page.screenshot(path=str(screenshot_file))
            print(f"   截图: {screenshot_file}")
        
        # 等待用户扫码登录
        print("3. 等待扫码登录（最多 120 秒）...")
        
        try:
            # 等待 URL 变化或用户信息出现
            page.wait_for_url('**/cgi-bin/home**', timeout=120000)
            print("   ✅ 登录成功!")
        except Exception as e:
            print(f"   等待超时: {e}")
            # 尝试其他方式检测登录
            try:
                page.wait_for_selector('.account_info, .user_info', timeout=10000)
                print("   ✅ 检测到登录")
            except:
                print("   ❌ 未能检测到登录成功")
                browser.close()
                return
        
        time.sleep(3)
        
        # 保存 Cookie
        print("4. 保存 Cookie...")
        cookies = context.cookies()
        
        with open(COOKIE_FILE, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print(f"   ✅ Cookie 已保存到: {COOKIE_FILE}")
        
        # 测试访问
        print("5. 测试访问...")
        test_url = 'https://mp.weixin.qq.com/s?__biz=MzUxNjg4NDEzNA==&mid=2247532272&idx=1&sn=e4ea5c1fecc792467f63a79691a37359'
        page.goto(test_url)
        time.sleep(5)
        
        title = page.title()
        print(f"   页面标题: {title}")
        
        if '环境异常' in title or '验证' in title:
            print("   ⚠️ 仍需验证，Cookie 可能不够")
        else:
            print("   ✅ 访问成功!")
        
        browser.close()
        print("\n完成!")

if __name__ == '__main__':
    get_qrcode_and_login()