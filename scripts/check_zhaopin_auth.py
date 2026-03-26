import argparse
import json
import os
import sys
from datetime import datetime
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


LOGGED_IN_SELECTORS = [
    ".nav-userinfo",
    ".user-login",
    ".zp-user-info",
    ".user-center",
    ".user-menu",
    ".zp-header__user",
    ".user-name",
    ".page-header__menu",
    ".page-header__menu__item",
    ".page-header__logo",
    "a[href*='xiaoyuan.zhaopin.com']",
]

LOGIN_SELECTORS = [
    "a[href*='login']",
    ".login",
    ".btn-login",
    ".login-btn",
    "#zp-login-widget-c-container",
    ".zp-login__wrap",
    ".zppp-submit",
    ".zppp-sms__send",
    ".nc-container",
    "input[id^='input_']",
]

CHECK_URLS = [
    "https://landing.zhaopin.com/",
    "https://xiaoyuan.zhaopin.com/search/index",
    "https://sou.zhaopin.com/?kw=python",
]


def _count_cookies_in_state(auth_path):
    try:
        with open(auth_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        cookies = payload.get("cookies") if isinstance(payload, dict) else None
        if isinstance(cookies, list):
            return len(cookies)
    except Exception:
        return None
    return None


def _is_logged_in(page, context):
    for selector in LOGGED_IN_SELECTORS:
        element = page.query_selector(selector)
        if element:
            return True
    cookies = context.cookies()
    cookie_map = {cookie.get("name"): cookie.get("value") for cookie in cookies}
    if cookie_map.get("at") and cookie_map.get("rt"):
        return True
    if cookie_map.get("zp_passport_deepknow_sessionId"):
        return True
    has_visible_login_btn = False
    for selector in LOGIN_SELECTORS:
        element = page.query_selector(selector)
        if not element:
            continue
        try:
            if element.is_visible():
                has_visible_login_btn = True
                break
        except Exception:
            has_visible_login_btn = True
            break
    return not has_visible_login_btn


def _is_zhaopin_domain(url):
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return hostname == "zhaopin.com" or hostname.endswith(".zhaopin.com")


def check_auth(auth_path, headless=True, timeout_ms=60000):
    result = {
        "auth_path": auth_path,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "cookie_count_in_state": _count_cookies_in_state(auth_path),
        "checks": [],
        "usable": False,
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            storage_state=auth_path,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            viewport={"width": 1366, "height": 900},
        )
        page = context.new_page()
        for url in CHECK_URLS:
            entry = {
                "url": url,
                "ok": False,
                "logged_in": False,
                "domain_ok": False,
                "final_url": "",
                "error": "",
            }
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(1200)
                entry["final_url"] = page.url
                entry["logged_in"] = _is_logged_in(page, context)
                entry["domain_ok"] = _is_zhaopin_domain(page.url)
                entry["ok"] = True
            except Exception as e:
                entry["error"] = str(e)
                entry["final_url"] = page.url
                entry["domain_ok"] = _is_zhaopin_domain(page.url)
            result["checks"].append(entry)
        browser.close()
    result["usable"] = any(item["logged_in"] and item["domain_ok"] for item in result["checks"])
    return result


def main():
    root_dir = os.path.dirname(os.path.dirname(__file__))
    default_auth = os.path.join(root_dir, "crawler", "auth_zhaopin.json")
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth", default=default_auth)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=60000)
    args = parser.parse_args()

    auth_path = os.path.abspath(args.auth)
    if not os.path.exists(auth_path):
        print(json.dumps({"usable": False, "error": f"文件不存在: {auth_path}"}, ensure_ascii=False))
        sys.exit(1)

    report = check_auth(auth_path=auth_path, headless=not args.headed, timeout_ms=args.timeout_ms)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["usable"] else 2)


if __name__ == "__main__":
    main()
