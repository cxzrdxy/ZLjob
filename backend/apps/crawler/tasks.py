from datetime import datetime
import os
import subprocess
import sys

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from pymongo import MongoClient

from apps.jobs.models import Job
from .models import CrawlTask


def parse_salary_range(salary_text):
    if not salary_text:
        return 0, 0
    import re
    text = salary_text.lower().replace(" ", "").replace("·13薪", "").replace("·14薪", "").replace("·16薪", "")
    
    # 匹配 "1.7-2.2万" 格式
    match = re.search(r'(\d+\.?\d*)-(\d+\.?\d*)万', text)
    if match:
        try:
            min_v = int(float(match.group(1)) * 10000)
            max_v = int(float(match.group(2)) * 10000)
            return min_v, max_v
        except ValueError:
            return 0, 0
    
    # 匹配 "9000-15000元" 格式
    match = re.search(r'(\d+)-(\d+)元', text)
    if match:
        try:
            min_v = int(match.group(1))
            max_v = int(match.group(2))
            return min_v, max_v
        except ValueError:
            return 0, 0
    
    # 匹配 "15k-20k" 格式
    if "k" in text:
        match = re.search(r'(\d+\.?\d*)k?-(\d+\.?\d*)k?', text)
        if match:
            try:
                min_v = int(float(match.group(1)) * 1000)
                max_v = int(float(match.group(2)) * 1000)
                return min_v, max_v
            except ValueError:
                return 0, 0
        # 单个数值如 "20k"
        match = re.search(r'(\d+\.?\d*)k', text)
        if match:
            try:
                v = int(float(match.group(1)) * 1000)
                return v, v
            except ValueError:
                return 0, 0
    
    return 0, 0


def parse_publish_time(text):
    if not text:
        return None
    raw = str(text).strip()
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def sync_jobs_from_mongo(task_id):
    client = MongoClient(settings.MONGO_URI)
    db = client.get_default_database()
    rows = list(db.jobs.find({"crawl_task_id": str(task_id)}))
    synced = 0
    failed = 0
    for row in rows:
        source_url = row.get("source_url") or ""
        if not source_url:
            failed += 1
            continue
        min_salary, max_salary = parse_salary_range(row.get("salary"))
        defaults = {
            "title": row.get("title", ""),
            "company": row.get("company", ""),
            "salary": row.get("salary", ""),
            "salary_min": min_salary,
            "salary_max": max_salary,
            "city": row.get("location", ""),
            "industry": row.get("industry", ""),
            "experience": row.get("experience", ""),
            "education": row.get("education", ""),
            "description": row.get("description", ""),
            "tags": row.get("tags") or [],
            "welfare": row.get("welfare") or [],
            "publish_time": parse_publish_time(row.get("publish_time")),
            "source_url": source_url,
        }
        Job.objects.update_or_create(source_url=source_url, defaults=defaults)
        synced += 1
    return len(rows), synced, failed


@shared_task
def run_crawl_task(task_id):
    task = CrawlTask.objects.filter(id=task_id).first()
    if not task:
        return {"status": "not_found"}
    task.status = "running"
    task.started_at = timezone.now()
    task.save(update_fields=["status", "started_at"])
    crawler_dir = settings.BASE_DIR.parent / "crawler"
    command = [
        sys.executable,
        "-m",
        "scrapy",
        "crawl",
        "zhaopin_jobs",
        "-a",
        f"keyword={task.keyword}",
        "-a",
        f"city={task.city}",
        "-a",
        f"crawl_task_id={task.id}",
        "-a",
        f"max_pages={task.max_pages}",
    ]
    env = os.environ.copy()
    env["MONGO_URI"] = settings.MONGO_URI
    try:
        proc = subprocess.run(
            command,
            cwd=str(crawler_dir),
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            task.status = "failed"
            task.fail_count = 1
            task.completed_at = timezone.now()
            task.save(update_fields=["status", "fail_count", "completed_at"])
            return {"status": "failed", "task_id": task_id}
        total, success, failed = sync_jobs_from_mongo(task.id)
        task.total_count = total
        task.success_count = success
        task.fail_count = failed
        task.status = "success"
        task.completed_at = timezone.now()
        task.save(
            update_fields=[
                "total_count",
                "success_count",
                "fail_count",
                "status",
                "completed_at",
            ]
        )
        return {"status": "success", "task_id": task_id, "total_count": total}
    except Exception:
        task.status = "failed"
        task.fail_count = 1
        task.completed_at = timezone.now()
        task.save(update_fields=["status", "fail_count", "completed_at"])
        return {"status": "failed", "task_id": task_id}
