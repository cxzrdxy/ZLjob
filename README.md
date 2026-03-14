# 智联招聘职位爬取与分析平台

基于 Django + DRF + Celery + Scrapy + Vue3 的职位采集、分析与可视化平台。

## 目录结构

```text
ZLjob/
├── backend/                 # Django后端
├── crawler/                 # Scrapy爬虫
├── frontend/                # Vue3前端
├── docker/                  # Docker配置
├── docker-compose.yml
└── .env.example
```

## 快速开始

1. 复制环境变量

```bash
cp .env.example .env
```

2. 使用 Docker 启动

```bash
docker compose up -d --build
```

3. 访问服务

- 前端: http://localhost:5173
- 后端API: http://localhost:8000/api/

## 核心能力

- 职位列表与详情查询
- JWT 注册登录认证
- 采集任务创建与列表查询
- 薪资与热门技能统计接口
- 趋势统计接口与折线图展示
- 采集任务触发爬虫并同步数据到 PostgreSQL

## 默认 API 路径

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/jobs`
- `GET /api/jobs/{id}`
- `GET /api/statistics/salary`
- `GET /api/statistics/hot`
- `GET /api/statistics/trend`
- `POST /api/crawl/tasks`
- `GET /api/crawl/tasks`

## 开发说明

- 后端依赖位于 `backend/requirements.txt`
- 爬虫依赖位于 `crawler/requirements.txt`
- 前端依赖位于 `frontend/package.json`
- 首次启动前请执行数据库迁移 `python manage.py migrate`

## 智联登录态刷新

- Windows 双击运行 `scripts/refresh_zhaopin_auth.bat`
- 或命令行运行 `python scripts/refresh_zhaopin_auth.py`
- 登录完成后会写入 `crawler/auth_zhaopin.json`，Docker 任务通过 `ZHAOPIN_STORAGE_STATE=/app/crawler/auth_zhaopin.json` 复用该登录态
- 会话目录持久化在 `crawler/.pw-zhaopin-user-data`，通过 `ZHAOPIN_USER_DATA_DIR=/app/crawler/.pw-zhaopin-user-data` 启用
- 若运行中提示 `session_expired` 或 `login_required`，刷新登录态后重新触发任务

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | Vue3 + Element Plus + ECharts | 用户界面与数据可视化 |
| 后端 | Django + Django REST Framework | API 服务 |
| 爬虫 | Scrapy + Playwright | 数据采集 |
| 任务队列 | Celery + Redis | 异步任务处理 |
| 数据库 | PostgreSQL + MongoDB | 数据存储 |
| 部署 | Docker + Docker Compose | 容器化部署 |

## 项目特点

- 支持智联招聘网站职位数据采集
- 支持多城市、多关键词职位搜索
- 实时薪资统计与热门技能分析
- 职位趋势可视化展示
- 完整的用户认证与权限管理
