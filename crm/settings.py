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