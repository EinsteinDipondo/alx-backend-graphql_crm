#!/bin/bash

# Customer Cleanup Script
# This script deletes customers who haven't placed orders in the past year
# Runs every Sunday at 2:00 AM

# Log file location
LOG_FILE="/tmp/customer_cleanup_log.txt"

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Start logging
echo "[$TIMESTAMP] Starting customer cleanup..." >> "$LOG_FILE"

# Navigate to the Django project directory (adjust this path as needed)
cd /home/ubuntu/alx-backend-graphql_crm || {
    echo "[$TIMESTAMP] ERROR: Could not navigate to project directory" >> "$LOG_FILE"
    exit 1
}

# Execute Django shell command to delete inactive customers
# The Python code finds and deletes customers with no orders in the past year
python3 manage.py shell << EOF 2>&1 >> "$LOG_FILE"
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from django.utils import timezone
from crm.models import Customer, Order

try:
    # Calculate date one year ago
    one_year_ago = timezone.now() - timedelta(days=365)
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Looking for customers with no orders since: {one_year_ago}")
    
    # Find customers who have never placed an order
    customers_no_orders = Customer.objects.filter(order__isnull=True)
    
    # Find customers whose last order was more than a year ago
    # First, get all customers
    all_customers = Customer.objects.all()
    
    # Then filter those with orders older than a year
    old_customers = []
    for customer in all_customers:
        # Get the most recent order for this customer
        latest_order = customer.order_set.order_by('-order_date').first()
        if latest_order:
            if latest_order.order_date < one_year_ago:
                old_customers.append(customer.id)
    
    # Combine both sets of customers
    customers_to_delete_ids = list(customers_no_orders.values_list('id', flat=True)) + old_customers
    customers_to_delete_ids = list(set(customers_to_delete_ids))  # Remove duplicates
    
    # Count before deletion
    count = len(customers_to_delete_ids)
    
    if count > 0:
        # Delete the customers
        deleted_count, _ = Customer.objects.filter(id__in=customers_to_delete_ids).delete()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Successfully deleted {count} inactive customers")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No inactive customers found to delete")
    
except Exception as e:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR during customer cleanup: {str(e)}")
    import traceback
    traceback.print_exc()
EOF

# Log completion
END_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$END_TIMESTAMP] Customer cleanup completed" >> "$LOG_FILE"
echo "--------------------------------------------------" >> "$LOG_FILE"
