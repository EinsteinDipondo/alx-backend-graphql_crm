# CRM — Celery Setup Guide ✅

A concise guide to configure Celery and Celery Beat for generating weekly CRM reports in this project.

---

## Prerequisites

- **Python** 3.8+
- **Django** 3.2+
- **Redis** (used as Celery broker and result backend)

---

## Quick Overview 🔧

1. Install Redis and Python dependencies
2. Configure Celery settings and add `django_celery_beat` to `INSTALLED_APPS`
3. Create Celery files and tasks (`celery.py`, `tasks.py`, `__init__.py`)
4. Run migrations for `django_celery_beat`
5. Start Django, Celery worker, and Celery Beat

---

## 1. Install Redis and Dependencies

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### macOS (Homebrew)

```bash
brew install redis
brew services start redis
```

### Windows

Download a Redis release for Windows (or use WSL):
https://github.com/microsoftarchive/redis/releases

Verify Redis is running:

```bash
redis-cli ping
# => PONG
```

### Python dependencies

Add to `requirements.txt`:

```txt
celery
django-celery-beat
redis
requests
```

Install them:

```bash
pip install -r requirements.txt
```

---

## 2. Update Django Settings

Edit `crm/settings.py`:

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps ...
    'django_celery_beat',
]

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'UTC'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
```

Add a beat schedule (example):

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report_task',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
```

---

## 3. Required Files

Ensure these exist in `crm/`:

- `crm/celery.py` — Celery app configuration
- `crm/tasks.py` — `generate_crm_report` task implementation
- `crm/__init__.py` — import/initialize Celery app: `from .celery import app as celery_app`

---

## 4. Run Migrations

```bash
python manage.py migrate django_celery_beat
```

---

## 5. Run the Services

Start Django server:

```bash
python manage.py runserver
```

Start a Celery worker (new terminal):

```bash
celery -A crm worker -l info --concurrency=4
```

Start Celery Beat (new terminal):

```bash
celery -A crm beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Testing & Verification ✅

- Test Redis:

```bash
redis-cli ping
# => PONG
```

- Test GraphQL endpoint:

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query": "query { customers { id } orders { id totalAmount } }"}'
```

- Manually run the task in Django shell:

```bash
python manage.py shell -c "\
from crm.tasks import generate_crm_report\
result = generate_crm_report()\
print('Report generated:', result)\
"
```

- Confirm logs (example file):

```bash
cat /tmp/crm_report_log.txt
# Example entry:
# 2026-01-13 06:00:00 - Report: 25 customers, 150 orders, 12500.50 revenue
```

---

## Task Details

**generate_crm_report** task:

- Fetches CRM stats via GraphQL (customers, orders, totals)
- Logs a summary to `/tmp/crm_report_log.txt`
- Scheduled to run every Monday at 06:00 (example schedule shown above)

Example GraphQL query:

```graphql
query GetCRMStats {
  customers { id }
  orders { id totalAmount }
}
```

---

## Troubleshooting ⚠️

- Redis connection errors: start Redis (e.g., `redis-server`) or check host/port
- ModuleNotFoundError for `celery`: ensure dependencies installed (`pip install -r requirements.txt`)
- Migration errors: run `python manage.py migrate`
- Worker not starting: verify `crm/__init__.py` contains `from .celery import app as celery_app`

---

## Monitoring

- Inspect worker stats:

```bash
celery -A crm inspect stats
```

- List active tasks:

```bash
celery -A crm inspect active
```

- List scheduled tasks:

```bash
celery -A crm inspect scheduled
```

---

## Project File Structure (overview)

```
alx-backend-graphql_crm/
├── crm/
│   ├── celery.py
│   ├── tasks.py
│   ├── __init__.py
│   ├── settings.py
│   └── README.md
├── requirements.txt
└── manage.py
```

---

If you want, I can also add a short example `celery.py` template or add badges (build/coverage) to this README. Let me know which you'd prefer.
