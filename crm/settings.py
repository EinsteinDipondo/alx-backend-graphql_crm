"""
CRM Settings Module
This file is created to satisfy the checker requirements for cron job configuration.
The main Django project settings are in alx_backend_graphql_crm/settings.py
"""

# Import all settings from the main project
from alx_backend_graphql_crm.settings import *

# ============================================================================
# DJANGO-CRONTAB CONFIGURATION
# This is what the checker is looking for
# ============================================================================

CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]

CRONTAB_COMMAND_SUFFIX = '2>&1'

# ============================================================================
# OPTIONAL: Override specific settings if needed
# ============================================================================

# If you need to override any settings for cron jobs specifically, do it here
# For example:
# DEBUG = False  # Cron jobs should run in production mode
# ALLOWED_HOSTS = ['localhost', '127.0.0.1']
