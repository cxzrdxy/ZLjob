import scrapy


class JobItem(scrapy.Item):
    job_id = scrapy.Field()
    crawl_task_id = scrapy.Field()
    title = scrapy.Field()
    company = scrapy.Field()
    salary = scrapy.Field()
    location = scrapy.Field()
    experience = scrapy.Field()
    education = scrapy.Field()
    description = scrapy.Field()
    tags = scrapy.Field()
    welfare = scrapy.Field()
    publish_time = scrapy.Field()
    source_url = scrapy.Field()
    latest_step = scrapy.Field()
    crawled_at = scrapy.Field()
    source_site = scrapy.Field()
    error_message = scrapy.Field()
