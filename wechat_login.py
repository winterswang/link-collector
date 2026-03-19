#!/usr/bin/env python3
"""
微信登录态管理脚本
- 首次运行: 弹出浏览器，用户扫码登录，自动保存登录态
- 后续运行: 自动加载登录态，无需扫码
"""

import os
import sys
import json
import re
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth as stealth_module

# 配置
STORAGE_FILE = Path(__file__).parent / "wechat_state.json"
LOGIN_URL = "https://web.wechat.com/"
WAIT_TIMEOUT = 120000  # 2分钟等待扫码


def get_qrcode():
    """获取登录二维码"""
    print("获取微信登录二维码...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        stealth_module.Stealth().apply_stealth_sync(page)
        
        page.goto(LOGIN_URL, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(3000)
        
        # 从页面提取二维码 URL
        html = page.content()
        match = re.search(r'mm-src="(https://login\.weixin\.qq\.com/qrcode/[^"]+)"', html)
        
        if match:
            qr_url = match.group(1)
            print(f"二维码 URL: {qr_url}")
            
            # 下载
            urllib.request.urlretrieve(qr_url, '/tmp/wechat_qr.png')
            print(f"✅ 二维码保存到: /tmp/wechat_qr.png")
        else:
            print("❌ 无法获取二维码")
            
        browser.close()


def is_logged_in(page) -> bool:
    """检查是否已登录"""
    try:
        # 检查是否有登录后的元素
        page.wait_for_selector('.avatar', timeout=5000)
        return True
    except:
        return False


def save_login_state():
    """首次登录：弹出浏览器让用户扫码，保存登录态"""
    print("=" * 50)
    print("微信扫码登录模式")
    print("=" * 50)
    print("请掏出手机扫码登录微信网页版...")
    print(f"登录成功后，登录态将保存到: {STORAGE_FILE}")
    print("下次运行将自动使用保存的登录态")
    print("=" * 50)
    
    with sync_playwright() as p:
        # 启动有头浏览器（必须）
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # 应用 stealth
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        # 应用 stealth 反检测
        stealth_module.Stealth().apply_stealth_sync(page)
        
        # 访问微信登录页
        page.goto(LOGIN_URL)
        
        try:
            # 等待用户扫码登录
            print("等待扫码中...")
            page.wait_for_url(lambda url: 'web.wechat.com' in url and 'login' not in url, timeout=WAIT_TIMEOUT)
            
            # 等待页面加载完成
            page.wait_for_load_state('networkidle')
            
            # 保存登录态
            context.storage_state(path=str(STORAGE_FILE))
            print(f"\n✅ 登录成功！登录态已保存到: {STORAGE_FILE}")
            
        except Exception as e:
            print(f"\n❌ 登录超时或失败: {e}")
            sys.exit(1)
        finally:
            browser.close()


def load_login_state():
    """后续运行：自动加载登录态"""
    if not STORAGE_FILE.exists():
        print(f"❌ 登录态文件不存在: {STORAGE_FILE}")
        print("请先运行 --login 进行扫码登录")
        sys.exit(1)
    
    print(f"加载登录态: {STORAGE_FILE}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # 可以用无头模式
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            storage_state=str(STORAGE_FILE),
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        
        try:
            page.goto(LOGIN_URL)
            page.wait_for_load_state('networkidle')
            
            if is_logged_in(page):
                print("✅ 自动登录成功！")
                return context, page
            else:
                print("❌ 登录态已过期，请重新扫码登录")
                print("删除旧登录态后重新运行: rm wechat_state.json")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ 加载登录态失败: {e}")
            sys.exit(1)


def test_login():
    """测试登录态是否有效"""
    context, page = load_login_state()
    print("✅ 登录态测试通过！")
    print(f"当前页面标题: {page.title()}")
    browser = page.context.browser
    browser.close()


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--login':
            save_login_state()
        elif sys.argv[1] == '--test':
            test_login()
        elif sys.argv[1] == '--reset':
            if STORAGE_FILE.exists():
                STORAGE_FILE.unlink()
                print(f"✅ 已删除登录态: {STORAGE_FILE}")
            else:
                print("没有找到登录态文件")
        elif sys.argv[1] == '--qrcode':
            get_qrcode()
        else:
            print("用法:")
            print("  python wechat_login.py          # 尝试自动登录")
            print("  python wechat_login.py --login  # 扫码登录")
            print("  python wechat_login.py --test   # 测试登录态")
            print("  python wechat_login.py --reset  # 重置登录态")
            print("  python wechat_login.py --qrcode # 获取登录二维码")
    else:
        # 默认：尝试自动登录
        test_login()


if __name__ == "__main__":
    main()