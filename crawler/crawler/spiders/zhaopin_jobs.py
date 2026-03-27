import os
import random
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

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
            ".home-header__c-login",
            ".c-login__top__name",
            ".home-header__user-name",
            ".home-header__avatar",
            "a[href*='//i.zhaopin.com']",
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
            ".home-search__c-no-login",
            ".home-header__a-login",
            ".home-header__b-login",
        ]
        self.start_urls = [
            "https://landing.zhaopin.com/",
            "https://xiaoyuan.zhaopin.com/search/index",
            *[self._list_url(page) for page in range(1, self.max_pages + 1)],
        ]

    def _list_url(self, page):
        # 使用旧的 URL 格式: /?kw={关键词}&jl={城市代码}&p={页码}
        # 城市代码如: 736=武汉, 801=长沙, 538=上海
        kw = quote_plus(self.keyword.strip())
        if self.city and self.city.strip():
            city_code = self._get_city_code(self.city.strip())
            return f"https://sou.zhaopin.com/?kw={kw}&jl={city_code}&p={page}"
        return f"https://sou.zhaopin.com/?kw={kw}&p={page}"

    def _get_city_code(self, city_name):
        """获取城市代码
        支持常见城市名称到代码的映射
        """
        city_map = {
            # 一线城市
            "北京": "530",
            "上海": "538",
            "广州": "763",
            "深圳": "765",
            # 新一线
            "成都": "801",
            "杭州": "653",
            "武汉": "736",
            "西安": "854",
            "重庆": "551",
            "南京": "635",
            "天津": "531",
            "苏州": "639",
            "长沙": "749",
            "郑州": "719",
            "东莞": "779",
            "青岛": "703",
            "沈阳": "599",
            "宁波": "654",
            "昆明": "831",
            "合肥": "664",
            "佛山": "768",
            "大连": "600",
            "福州": "681",
            "厦门": "682",
            "哈尔滨": "622",
            "济南": "702",
            "温州": "655",
            "长春": "613",
            "石家庄": "565",
            "常州": "638",
            "泉州": "684",
            "南宁": "799",
            "贵阳": "822",
            "南昌": "691",
            "金华": "656",
            "无锡": "637",
            "惠州": "773",
            "珠海": "764",
            "中山": "766",
            "台州": "657",
            "烟台": "707",
            "兰州": "860",
            "绍兴": "658",
            "海口": "922",
            "扬州": "642",
        }
        # 尝试直接匹配
        if city_name in city_map:
            return city_map[city_name]
        # 尝试去掉"市"后缀匹配
        if city_name.endswith("市") and city_name[:-1] in city_map:
            return city_map[city_name[:-1]]
        # 默认返回全国
        return "489"  # 全国

    def start_requests(self):
        context_kwargs = {}
        if self.storage_state_path and os.path.exists(self.storage_state_path):
            context_kwargs["storage_state"] = self.storage_state_path
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                errback=self.errback_close_page,
                meta=self._build_playwright_meta(context_kwargs),
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
            
            # 直接从列表页提取职位数据
            job_items = response.css('.joblist-box__item')
            self.logger.info(f"Found {len(job_items)} job items on list page")
            
            for job in job_items:
                try:
                    # 提取基本信息
                    title = job.css('.jobinfo__name::text').get('').strip()
                    salary = job.css('.jobinfo__salary::text').get('').strip()
                    company = job.css('.companyinfo__name::text').get('').strip()
                    
                    # 从 other-info 提取地点、经验、学历
                    # 第一个 item 是地点（包含 location.png 图片）
                    location = job.css('.jobinfo__other-info-item:first-child span::text').get('').strip()
                    # 第二个 item 是经验
                    experience = job.css('.jobinfo__other-info-item:nth-child(2)::text').get('').strip()
                    # 第三个 item 是学历
                    education = job.css('.jobinfo__other-info-item:nth-child(3)::text').get('').strip()
                    
                    # 提取标签
                    tags = job.css('.joblist-box__item-tag::text').getall()
                    tags = [tag.strip() for tag in tags if tag.strip()]
                    
                    # 提取详情链接
                    detail_url = job.css('.jobinfo__name::attr(href)').get('')
                    if detail_url and not detail_url.startswith('http'):
                        detail_url = 'https:' + detail_url if detail_url.startswith('//') else response.urljoin(detail_url)
                    
                    # 提取公司标签
                    company_tags = job.css('.companyinfo__tag .joblist-box__item-tag::text').getall()
                    welfare = [tag.strip() for tag in company_tags if tag.strip()]
                    
                    # 使用当前时间作为发布时间（列表页没有发布时间）
                    publish_time = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                    
                    # 构建职位描述（从已有信息组合）
                    description_parts = [
                        f"职位：{title}",
                        f"薪资：{salary}",
                        f"公司：{company}",
                        f"地点：{location}",
                        f"经验：{experience}",
                        f"学历：{education}",
                    ]
                    if tags:
                        description_parts.append(f"标签：{', '.join(tags)}")
                    description = '\n'.join(description_parts)
                    
                    if title and company:
                        yield JobItem(
                            job_id=detail_url or response.url,
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
                            source_url=detail_url or response.url,
                            latest_step="list_page_extract",
                            crawled_at=datetime.now(timezone.utc).isoformat(),
                            source_site="zhaopin",
                            error_message="",
                        )
                        self.logger.info(f"Extracted job: {title} @ {company}")
                except Exception as e:
                    self.logger.error(f"Error extracting job item: {e}")
                    continue
                    
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
        cookies = await page.context.cookies()
        cookie_map = {cookie.get("name"): cookie.get("value") for cookie in cookies}
        if cookie_map.get("at") and cookie_map.get("rt"):
            return True
        if cookie_map.get("zp_passport_deepknow_sessionId"):
            return True
        has_visible_login_btn = False
        for selector in self.login_selectors:
            element = await page.query_selector(selector)
            if not element:
                continue
            try:
                if await element.is_visible():
                    has_visible_login_btn = True
                    break
            except Exception:
                has_visible_login_btn = True
                break
        return not has_visible_login_btn

    async def _save_storage_state(self, page):
        if not self.storage_state_path:
            return
        directory = os.path.dirname(self.storage_state_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        await page.context.storage_state(path=self.storage_state_path)

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

    def _build_playwright_meta(self, context_kwargs=None):
        meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_context": self._playwright_context,
        }
        if context_kwargs:
            meta["playwright_context_kwargs"] = context_kwargs
        return meta

    def _extract_first(self, response, selector):
        value = response.css(selector).get(default="")
        return self._clean_text(value)

    def _extract_text_list(self, response, selector):
        values = response.css(selector).getall()
        return self._dedupe_texts(values)

    def _dedupe_texts(self, values):
        results = []
        seen = set()
        for value in values:
            text = self._clean_text(value)
            if not text or text in seen:
                continue
            seen.add(text)
            results.append(text)
        return results

    def _join_texts(self, values, max_len=6000):
        texts = []
        for value in values:
            clean_value = self._clean_text(value)
            if clean_value:
                texts.append(clean_value)
        return " ".join(texts)[:max_len]

    def _clean_text(self, text):
        if text is None:
            return ""
        value = str(text).replace("\u3000", " ").replace("\xa0", " ")
        value = re.sub(r"\s+", " ", value).strip()
        return value

    def _infer_job_meta(self, infos):
        location = ""
        experience = ""
        education = ""
        for item in infos:
            if not experience and self._is_experience_text(item):
                experience = item
                continue
            if not education and self._is_education_text(item):
                education = item
                continue
            if not location and self._is_location_text(item):
                location = item
        return location, experience, education

    def _is_experience_text(self, text):
        value = self._clean_text(text)
        if not value:
            return False
        return bool(
            re.search(
                r"(经验不限|无经验|应届|在校|实习|[0-9一二三四五六七八九十]+年|[0-9]+-[0-9]+年|[0-9]+年以上)",
                value,
            )
        )

    def _is_education_text(self, text):
        value = self._clean_text(text)
        if not value:
            return False
        return any(token in value for token in ("学历不限", "大专", "本科", "硕士", "博士", "中专", "中技", "高中"))

    def _is_salary_text(self, text):
        value = self._clean_text(text).lower()
        if not value:
            return False
        return bool(
            re.search(r"(k|万|元/月|元/天|元/年|面议|薪|/月|/天|/年|月薪|年薪|时薪)", value)
        )

    def _is_publish_time_text(self, text):
        value = self._clean_text(text)
        if not value:
            return False
        return bool(
            re.search(r"(更新|发布|刚刚|今天|昨天|[0-9]+小时前|[0-9]+天前|[0-9]+月[0-9]+日)", value)
        )

    def _is_location_text(self, text):
        value = self._clean_text(text)
        if not value:
            return False
        if self._is_experience_text(value) or self._is_education_text(value):
            return False
        if self._is_salary_text(value) or self._is_publish_time_text(value):
            return False
        return bool(
            re.search(r"(省|市|区|县|路|街道|街|镇|乡|开发区|新区|园区|商圈|地铁|·|-)", value)
        )

    def _is_meta_noise_tag(self, text):
        value = self._clean_text(text)
        if not value:
            return True
        return (
            self._is_experience_text(value)
            or self._is_education_text(value)
            or self._is_salary_text(value)
            or self._is_publish_time_text(value)
            or self._is_location_text(value)
        )

    def _normalize_publish_time(self, text):
        if text is None:
            return ""
        value = str(text).replace("发布时间", "").replace("发布于", "").replace("更新于", "")
        return self._clean_text(value)

    def _set_step(self, step):
        self._step = step
        self.crawler.stats.set_value("latest_step", step)
        self.crawler.stats.set_value("crawl_task_id", self.crawl_task_id)
