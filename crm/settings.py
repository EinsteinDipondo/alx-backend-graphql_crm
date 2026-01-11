"""
CRM Settings for Django Crontab
"""

# Import from main settings if available
try:
    from alx_backend_graphql_crm.settings import *
except ImportError:
    # Fallback minimal settings
    import os
    from pathlib import Path
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-temp-key-for-cron')
    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
    
    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django_crontab',
        'crm',
    ]
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    
    TIME_ZONE = 'UTC'
    USE_TZ = True

# ============================================================================
# DJANGO-CRONTAB CONFIGURATION
# ============================================================================

# Heartbeat cron job - runs every 5 minutes
# Low stock update cron job - runs every 12 hours
CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]

# Optional settings
CRONTAB_COMMAND_SUFFIX = '2>&1'
# CRONTAB_DJANGO_SETTINGS_MODULE = 'crm.settings'
# CRONTAB_DJANGO_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat settings
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Celery Beat schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
        'args': (),
    },
    'test-task-every-minute': {
        'task': 'crm.tasks.test_celery_task',
        'schedule': crontab(minute='*/1'),  # For testing
        'args': (),
    },
}

# Add django_celery_beat to INSTALLED_APPS
INSTALLED_APPS = [
    # ... your existing apps ...
    'django_celery_beat',
    # ... your existing apps ...
]