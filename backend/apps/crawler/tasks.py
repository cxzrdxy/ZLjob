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
    text = salary_text.lower().replace(" ", "").replace("·13薪", "").replace("·14薪", "")
    if "k" not in text:
        return 0, 0
    if "-" in text:
        left, right = text.split("-", 1)
        try:
            min_v = int(float(left.replace("k", "")) * 1000)
            max_v = int(float(right.replace("k", "")) * 1000)
            return min_v, max_v
        except ValueError:
            return 0, 0
    try:
        v = int(float(text.replace("k", "")) * 1000)
        return v, v
    except ValueError:
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
