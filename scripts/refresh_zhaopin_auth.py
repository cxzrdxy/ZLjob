import os
import sys

from playwright.sync_api import sync_playwright


def run():
    root_dir = os.path.dirname(os.path.dirname(__file__))
    auth_path = os.path.join(root_dir, "crawler", "auth_zhaopin.json")
    user_data_dir = os.path.join(root_dir, "crawler", ".pw-zhaopin-user-data")
    os.makedirs(os.path.dirname(auth_path), exist_ok=True)
    os.makedirs(user_data_dir, exist_ok=True)
    print(f"目标登录态文件: {auth_path}")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            slow_mo=50,
            viewport={"width": 1366, "height": 900},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        page = context.new_page() if len(context.pages) == 0 else context.pages[0]
        page.goto("https://landing.zhaopin.com/", wait_until="domcontentloaded", timeout=60000)
        print("请在浏览器中完成智联登录。")
        input("登录完成后按回车继续...")
        page.goto("https://xiaoyuan.zhaopin.com/search/index", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1200)
        page.goto("https://sou.zhaopin.com/?kw=python", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1200)
        input("已完成页面预热，按回车保存登录态并退出...")
        context.storage_state(path=auth_path)
        context.close()
    print("已保存智联登录态。")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        sys.exit(130)
