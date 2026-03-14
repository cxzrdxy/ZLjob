import os
from datetime import datetime, timezone

from pymongo import MongoClient
from scrapy.exceptions import DropItem


class MongoPipeline:
    def __init__(self):
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/job_platform")
        self.client = MongoClient(uri)
        self.db = self.client.get_default_database()
        self.col = self.db.get_collection("jobs")

    def process_item(self, item, spider):
        data = self._normalize_item(dict(item), spider)
        source_url = data.get("source_url")
        crawl_task_id = data.get("crawl_task_id")
        if not source_url:
            raise DropItem("missing_source_url")
        if not crawl_task_id:
            raise DropItem("missing_crawl_task_id")
        now = datetime.now(timezone.utc).isoformat()
        data["updated_at"] = now
        if not data.get("crawled_at"):
            data["crawled_at"] = now
        self.col.update_one(
            {"source_url": source_url, "crawl_task_id": crawl_task_id},
            {
                "$set": data,
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        return data

    def _normalize_item(self, data, spider):
        normalized = {}
        for key, value in data.items():
            if isinstance(value, str):
                normalized[key] = " ".join(value.split())
                continue
            if isinstance(value, list):
                cleaned = []
                seen = set()
                for element in value:
                    if isinstance(element, str):
                        element = " ".join(element.split())
                    if element in ("", None):
                        continue
                    marker = str(element)
                    if marker in seen:
                        continue
                    seen.add(marker)
                    cleaned.append(element)
                normalized[key] = cleaned
                continue
            normalized[key] = value
        normalized.setdefault("error_message", "")
        normalized.setdefault("latest_step", "")
        if "source_site" not in normalized or not normalized.get("source_site"):
            spider_name = getattr(spider, "name", "")
            if spider_name:
                normalized["source_site"] = spider_name.replace("_jobs", "").replace("jobs_", "")
            else:
                normalized["source_site"] = "unknown"
        return normalized
