import os
import random
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin

import scrapy
from scrapy.exceptions import CloseSpider

from ..items import JobItem


class BossJobsSpider(scrapy.Spider):
    name = "boss_jobs"
    allowed_domains = ["zhipin.com"]

    def __init__(
        self,
        keyword="Python",
        city="101010100",
        crawl_task_id="",
        max_pages=1,
        max_scroll_rounds=80,
        no_growth_limit=4,
        scroll_min_ms=800,
        scroll_max_ms=1500,
        login_wait_seconds=30,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.keyword = keyword
        self.city = city
        self.crawl_task_id = str(crawl_task_id)
        self.max_pages = int(max_pages)
        self.max_scroll_rounds = int(max_scroll_rounds)
        self.no_growth_limit = int(no_growth_limit)
        self.scroll_min_ms = int(scroll_min_ms)
        self.scroll_max_ms = int(scroll_max_ms)
        self.login_wait_seconds = int(login_wait_seconds)
        self.storage_state_path = os.getenv("BOSS_STORAGE_STATE", "").strip()
        self._step = "boot_context"
        self._login_retry_count = 0
        self._playwright_context = f"boss-{self.crawl_task_id}" if self.crawl_task_id else "boss-default"
        self.start_urls = [self._list_url(page) for page in range(1, self.max_pages + 1)]
        self.logged_in_selectors = [
            "a[ka='header-username']",
            ".user-nav",
            ".nav-figure",
            ".avatar",
        ]
        self.login_selectors = [
            "a[href*='login']",
            ".btn-sign",
            ".login-btn",
        ]

    def _list_url(self, page):
        keyword = quote_plus(self.keyword)
        return (
            "https://www.zhipin.com/web/geek/job"
            f"?query={keyword}&city={self.city}&page={page}"
        )

    def start_requests(self):
        context_kwargs = {}
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
            self._set_step("load_list")
            await page.wait_for_timeout(1000)
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
            await page.wait_for_timeout(500)
            title = response.css("h1::text, .job-title::text").get(default="").strip()
            company = response.css(".company-name::text, .name::text").get(default="").strip()
            salary = response.css(".salary::text, .job-salary::text").get(default="").strip()
            location = response.css(".job-location::text, .location-address::text, .job-area::text").get(default="").strip()
            experience = response.css(".job-limit.clearfix p::text, .job-experience::text").get(default="").strip()
            education = response.css(".job-limit.clearfix p:nth-child(2)::text, .job-education::text").get(default="").strip()
            description = " ".join(
                t.strip() for t in response.css(".job-sec-text::text, .job-detail-section .text::text").getall() if t.strip()
            )
            tags = [t.strip() for t in response.css(".job-tags span::text, .tag-list li::text").getall() if t.strip()]
            welfare = [t.strip() for t in response.css(".welfare-list li::text, .job-benefit-tag span::text").getall() if t.strip()]
            publish_time = response.css(".job-time::text, .job-publish-time::text").get(default="").strip()
            item = JobItem(
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
                source_site="boss",
                error_message="",
            )
            yield item
        finally:
            await page.close()

    async def errback_close_page(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error("request_failed task=%s step=%s error=%s", self.crawl_task_id, self._step, str(failure.value))

    async def _ensure_login(self, page):
        if await self._is_logged_in(page):
            return True
        self._set_step("do_login")
        await page.wait_for_timeout(max(1, self.login_wait_seconds) * 1000)
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

    async def _collect_detail_urls(self, page, base_url):
        urls = set()
        no_growth = 0
        previous_count = 0
        for _ in range(self.max_scroll_rounds):
            try:
                links = await page.eval_on_selector_all(
                    "a[href*='/job_detail/']",
                    "elements => elements.map(el => el.href).filter(Boolean)",
                )
                urls.update(self._normalize_detail_urls(links, base_url))
                current_count = len(urls)
                if current_count <= previous_count:
                    no_growth += 1
                else:
                    no_growth = 0
                    previous_count = current_count
                if no_growth >= self.no_growth_limit:
                    break
                reached_end = await page.evaluate(
                    "() => document.body && document.body.innerText && (document.body.innerText.includes('没有更多') || document.body.innerText.includes('到底了'))"
                )
                if reached_end:
                    break
                await page.evaluate("window.scrollBy(0, window.innerHeight * 0.9)")
                await page.wait_for_timeout(random.randint(self.scroll_min_ms, self.scroll_max_ms))
            except Exception as e:
                self.logger.warning(f"Scroll round interrupted: {e}")
                break
        return sorted(urls)

    def _normalize_detail_urls(self, links, base_url):
        normalized = []
        for link in links:
            if not link:
                continue
            if link.startswith("http://") or link.startswith("https://"):
                normalized.append(link)
                continue
            normalized.append(urljoin(base_url, link))
        return normalized

    def _set_step(self, step):
        self._step = step
        self.crawler.stats.set_value("latest_step", step)
        self.crawler.stats.set_value("crawl_task_id", self.crawl_task_id)
