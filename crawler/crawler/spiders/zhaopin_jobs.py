import json
import os
import random
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin

import scrapy
from scrapy.exceptions import CloseSpider

from ..items import JobItem


class ZhaopinJobsSpider(scrapy.Spider):
    name = "zhaopin_jobs"
    allowed_domains = ["zhaopin.com"]

    def __init__(
        self,
        keyword="Python",
        city="",
        crawl_task_id="",
        max_pages=1,
        max_scroll_rounds=40,
        no_growth_limit=3,
        scroll_min_ms=1000,
        scroll_max_ms=1800,
        login_wait_seconds=30,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.keyword = keyword
        self.city = city
        self.crawl_task_id = str(crawl_task_id)
        self.max_pages = max(1, int(max_pages))
        self.max_scroll_rounds = max(1, int(max_scroll_rounds))
        self.no_growth_limit = max(1, int(no_growth_limit))
        self.scroll_min_ms = int(scroll_min_ms)
        self.scroll_max_ms = int(scroll_max_ms)
        self.login_wait_seconds = max(1, int(login_wait_seconds))
        self.storage_state_path = (
            os.getenv("ZHAOPIN_STORAGE_STATE", "").strip()
            or os.getenv("BOSS_STORAGE_STATE", "").strip()
        )
        self.user_data_dir = os.getenv("ZHAOPIN_USER_DATA_DIR", "").strip()
        self._step = "boot_context"
        self._playwright_context = (
            f"zhaopin-{self.crawl_task_id}" if self.crawl_task_id else "zhaopin-default"
        )
        self._login_retry_count = 0
        self.logged_in_selectors = [
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
        self.login_selectors = [
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
        self.start_urls = ["https://landing.zhaopin.com/"]
        self.start_urls.append("https://xiaoyuan.zhaopin.com/search/index")
        self.start_urls.extend([self._list_url(page) for page in range(1, self.max_pages + 1)])

    def _list_url(self, page):
        kw = quote_plus(self.keyword.strip())
        if self.city and self.city.strip():
            jl = quote_plus(self.city.strip())
            return f"https://sou.zhaopin.com/?kw={kw}&jl={jl}&p={page}"
        return f"https://sou.zhaopin.com/?kw={kw}&p={page}"

    def start_requests(self):
        context_kwargs = {}
        if self.user_data_dir:
            context_kwargs["user_data_dir"] = self.user_data_dir
        if self.storage_state_path and os.path.exists(self.storage_state_path):
            context_kwargs["storage_state"] = self.storage_state_path
        for url in self.start_urls:
            meta = {
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": self._playwright_context,
            }
            if context_kwargs:
                meta["playwright_context_kwargs"] = context_kwargs
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                errback=self.errback_close_page,
                meta=meta,
            )

    async def parse_list(self, response):
        page = response.meta["playwright_page"]
        self._set_step("check_login")
        try:
            login_ok = await self._ensure_login(page)
            if not login_ok:
                raise CloseSpider("login_required")
            await self._save_storage_state(page)
            self._set_step("load_list")
            await page.wait_for_timeout(1200)
            detail_urls = self._collect_detail_urls_from_state(response.text, response.url)
            if not detail_urls:
                self._set_step("scrolling")
                detail_urls = await self._collect_detail_urls(page, response.url)
            for url in detail_urls:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    errback=self.errback_close_page,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_context": self._playwright_context,
                    },
                )
        finally:
            await page.close()

    async def parse_detail(self, response):
        page = response.meta["playwright_page"]
        self._set_step("parse_detail")
        try:
            await page.wait_for_timeout(800)
            if not await self._is_logged_in(page):
                self._set_step("session_expired")
                raise CloseSpider("session_expired")
            title = self._extract_first(response, "h1::text, .job-name::text, .position-name::text")
            company = self._extract_first(
                response,
                ".company-name::text, .company-title a::text, .company-info__name::text",
            )
            salary = self._extract_first(
                response,
                ".salary::text, .job-salary::text, .position-salary::text",
            )
            location = self._extract_first(
                response,
                ".job-address::text, .position-label li::text, .job-area::text",
            )
            experience = self._extract_first(
                response,
                ".job-require li:nth-child(1)::text, .position-label li:nth-child(2)::text",
            )
            education = self._extract_first(
                response,
                ".job-require li:nth-child(2)::text, .position-label li:nth-child(3)::text",
            )
            description_blocks = response.css(
                ".job-detail__content::text, .describtion__detail-content::text, .job-desc::text"
            ).getall()
            if not description_blocks:
                description_blocks = response.xpath("//body//text()").getall()[:200]
            description = " ".join([t.strip() for t in description_blocks if t and t.strip()])[:6000]
            tags = [
                t.strip()
                for t in response.css(
                    ".job-tags span::text, .position-label li::text, .highlights span::text"
                ).getall()
                if t and t.strip()
            ]
            welfare = [
                t.strip()
                for t in response.css(
                    ".welfare-tab-box span::text, .company-welfare li::text, .welfare__item::text"
                ).getall()
                if t and t.strip()
            ]
            publish_time = self._extract_first(
                response,
                ".time::text, .job-publish-time::text, .position-publish-time::text",
            )
            if not title and not company and not salary:
                return
            yield JobItem(
                job_id=response.url,
                crawl_task_id=self.crawl_task_id,
                title=title,
                company=company,
                salary=salary,
                location=location,
                experience=experience,
                education=education,
                description=description,
                tags=tags,
                welfare=welfare,
                publish_time=publish_time,
                source_url=response.url,
                latest_step=self._step,
                crawled_at=datetime.now(timezone.utc).isoformat(),
                source_site="zhaopin",
                error_message="",
            )
        finally:
            await page.close()

    async def _ensure_login(self, page):
        if await self._is_logged_in(page):
            return True
        self._set_step("do_login")
        try:
            self.logger.info("login_required wait_seconds=%s url=%s", self.login_wait_seconds, page.url)
        except Exception:
            pass
        await page.wait_for_timeout(self.login_wait_seconds * 1000)
        if await self._is_logged_in(page):
            await self._save_storage_state(page)
            return True
        if self._login_retry_count < 1:
            self._login_retry_count += 1
            await page.reload(wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            if await self._is_logged_in(page):
                await self._save_storage_state(page)
                return True
        return False

    async def _is_logged_in(self, page):
        for selector in self.logged_in_selectors:
            if await page.query_selector(selector):
                return True
        has_login_btn = False
        for selector in self.login_selectors:
            if await page.query_selector(selector):
                has_login_btn = True
                break
        return not has_login_btn

    async def _save_storage_state(self, page):
        if not self.storage_state_path:
            return
        directory = os.path.dirname(self.storage_state_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        await page.context.storage_state(path=self.storage_state_path)

    def _collect_detail_urls_from_state(self, text, base_url):
        data = self._extract_initial_data(text)
        if not data:
            return []
        urls = set()
        for url in self._walk_for_urls(data):
            normalized = self._normalize_url(url, base_url)
            if normalized:
                urls.add(normalized)
        return sorted(urls)

    def _extract_initial_data(self, text):
        if not text:
            return None
        marker = "window.__INITIAL_DATA__"
        idx = text.find(marker)
        if idx < 0:
            return None
        start = text.find("{", idx)
        if start < 0:
            return None
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    raw = text[start : i + 1]
                    try:
                        return json.loads(raw)
                    except Exception:
                        return None
        return None

    def _walk_for_urls(self, node):
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, str):
                    if "zhaopin.com" in value and "javascript:" not in value:
                        yield value
                if isinstance(value, (dict, list)):
                    yield from self._walk_for_urls(value)
                if isinstance(key, str) and "url" in key.lower() and isinstance(value, str):
                    yield value
        elif isinstance(node, list):
            for item in node:
                yield from self._walk_for_urls(item)

    def _normalize_url(self, url, base_url):
        if not url:
            return ""
        if url.startswith("//"):
            url = f"https:{url}"
        if url.startswith("http://") or url.startswith("https://"):
            return url.split("#")[0]
        return urljoin(base_url, url).split("#")[0]

    async def _collect_detail_urls(self, page, base_url):
        urls = set()
        no_growth = 0
        previous_count = 0
        selectors = [
            "a[href*='jobs.zhaopin.com']",
            "a[href*='/job/']",
            "a[href*='position']",
            "a[href*='sou.zhaopin.com/jobs']",
            "a[href*='xiaoyuan.zhaopin.com']",
        ]
        for _ in range(self.max_scroll_rounds):
            try:
                for selector in selectors:
                    links = await page.eval_on_selector_all(
                        selector,
                        "elements => elements.map(el => el.href).filter(Boolean)",
                    )
                    urls.update(self._normalize_detail_urls(links, base_url))
                all_links = await page.eval_on_selector_all(
                    "a[href]",
                    "elements => elements.map(el => el.href).filter(Boolean)",
                )
                urls.update(self._normalize_detail_urls(all_links, base_url))
                current_count = len(urls)
                if current_count <= previous_count:
                    no_growth += 1
                else:
                    no_growth = 0
                    previous_count = current_count
                if no_growth >= self.no_growth_limit:
                    break
                await page.evaluate("window.scrollBy(0, Math.max(window.innerHeight * 0.9, 700))")
                await page.wait_for_timeout(random.randint(self.scroll_min_ms, self.scroll_max_ms))
            except Exception as exc:
                self.logger.warning("collect_detail_urls_interrupted=%s", exc)
                break
        return sorted(urls)

    async def errback_close_page(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error(
            "request_failed task=%s step=%s error=%s",
            self.crawl_task_id,
            self._step,
            str(failure.value),
        )

    def _normalize_detail_urls(self, links, base_url):
        normalized = set()
        for link in links:
            if not link:
                continue
            if link.startswith("//"):
                link = f"https:{link}"
            if not link.startswith("http://") and not link.startswith("https://"):
                link = urljoin(base_url, link)
            if "zhaopin.com" not in link:
                continue
            if "javascript:" in link:
                continue
            if "/job/" not in link and "jobs.zhaopin.com" not in link and "sou.zhaopin.com/jobs" not in link:
                continue
            normalized.add(link.split("#")[0])
        return normalized

    def _extract_first(self, response, selector):
        value = response.css(selector).get(default="")
        return value.strip()

    def _set_step(self, step):
        self._step = step
        self.crawler.stats.set_value("latest_step", step)
        self.crawler.stats.set_value("crawl_task_id", self.crawl_task_id)
