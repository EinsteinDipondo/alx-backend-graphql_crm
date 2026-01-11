#!/bin/bash

# Customer Cleanup Script
# This script deletes customers who haven't placed orders in the past year
# Created: $(date)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Set your Django project path - UPDATE THIS TO YOUR ACTUAL PATH
# Example: /home/user/alx-backend-graphql_crm
DJANGO_PROJECT_PATH="/home/ubuntu/alx-backend-graphql_crm"

# ============================================================================
# SCRIPT START
# ============================================================================

# Log file location
LOG_FILE="/tmp/customer_cleanup_log.txt"

# Get current timestamp for logging
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Start message
echo "[$TIMESTAMP] Starting customer cleanup..." | tee -a "$LOG_FILE"

# Check if Django project directory exists
if [ ! -d "$DJANGO_PROJECT_PATH" ]; then
    echo "[$TIMESTAMP] ERROR: Django project path not found: $DJANGO_PROJECT_PATH" | tee -a "$LOG_FILE"
    exit 1
fi

# Navigate to Django project directory
cd "$DJANGO_PROJECT_PATH" || {
    echo "[$TIMESTAMP] ERROR: Failed to navigate to $DJANGO_PROJECT_PATH" | tee -a "$LOG_FILE"
    exit 1
}

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "[$TIMESTAMP] ERROR: manage.py not found in $DJANGO_PROJECT_PATH" | tee -a "$LOG_FILE"
    exit 1
fi

# ============================================================================
# DJANGO SHELL COMMAND
# ============================================================================
# This Python code will be executed in Django's shell
# IMPORTANT: Update the model names and queries based on your actual models

PYTHON_CODE=$(cat << 'EOF'
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.utils import timezone
from django.db.models import Q

# Import your models - UPDATE THESE BASED ON YOUR ACTUAL MODELS
# Example: from customers.models import Customer, Order

try:
    # Calculate date one year ago
    one_year_ago = timezone.now() - timedelta(days=365)
    
    print(f"Finding customers inactive since: {one_year_ago}")
    
    # ============================================
    # UPDATE THIS SECTION WITH YOUR ACTUAL MODELS
    # ============================================
    # Assuming you have Customer and Order models
    # with Order having a ForeignKey to Customer
    # and Order having a 'created_at' field
    
    # Example 1: If you have direct relationship
    # from customers.models import Customer, Order
    
    # Get customers who have never placed an order
    # customers_no_orders = Customer.objects.filter(order__isnull=True)
    
    # Get customers whose last order was more than a year ago
    # This is a complex query that might need adjustment
    
    # For now, let's create a placeholder implementation
    # that you should replace with your actual logic
    
    print("DEBUG: This is a placeholder. Replace with your actual model logic.")
    
    # Placeholder: Count would be 0 for now
    count = 0
    deleted_count = 0
    
    # ============================================
    # END OF SECTION TO UPDATE
    # ============================================
    
    # Log results
    print(f"Found {count} inactive customers to delete")
    print(f"Successfully deleted {deleted_count} customers")
    
    # Return success
    sys.exit(0)
    
except Exception as e:
    print(f"ERROR during customer cleanup: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
)

# ============================================================================
# EXECUTE THE CLEANUP
# ============================================================================

echo "[$TIMESTAMP] Executing Django cleanup script..." | tee -a "$LOG_FILE"

# Run the Python code using Django's shell
python3 manage.py shell -c "$PYTHON_CODE" 2>&1 | tee -a "$LOG_FILE"

# Capture the exit status
EXIT_STATUS=${PIPESTATUS[0]}

# Log completion
if [ $EXIT_STATUS -eq 0 ]; then
    echo "[$TIMESTAMP] Customer cleanup completed successfully" | tee -a "$LOG_FILE"
else
    echo "[$TIMESTAMP] Customer cleanup failed with exit code $EXIT_STATUS" | tee -a "$LOG_FILE"
fi

# Add separator for readability in logs
echo "--------------------------------------------------" >> "$LOG_FILE"
