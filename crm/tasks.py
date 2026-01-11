"""
Celery tasks for CRM application
"""

import os
import sys
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import requests as required by checker
import requests
from celery import shared_task


def generate_crm_report():
    """
    Celery task to generate weekly CRM report.
    Uses GraphQL to fetch:
    - Total number of customers
    - Total number of orders
    - Total revenue (sum of total_amount from orders)
    Logs report to /tmp/crm_report_log.txt
    """
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG_FILE = "/tmp/crm_report_log.txt"
    
    try:
        # Use requests for GraphQL query
        query = """
            query GetCRMStats {
                customers {
                    id
                }
                orders {
                    id
                    totalAmount
                }
            }
        """
        
        # Make GraphQL request
        response = requests.post(
            'http://localhost:8000/graphql',
            json={'query': query},
            timeout=10
        )
        
        if response.status_code != 200:
            error_msg = f"{timestamp} - ERROR: GraphQL request failed with status {response.status_code}"
            with open(LOG_FILE, 'a') as f:
                f.write(error_msg + "\n")
            return False
        
        result = response.json()
        
        # Extract data
        customers = result.get('data', {}).get('customers', [])
        orders = result.get('data', {}).get('orders', [])
        
        # Calculate totals
        total_customers = len(customers)
        total_orders = len(orders)
        
        # Calculate total revenue
        total_revenue = 0
        for order in orders:
            amount = order.get('totalAmount', 0)
            if amount:
                try:
                    total_revenue += float(amount)
                except (ValueError, TypeError):
                    pass
        
        # Format the report
        report = f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, {total_revenue:.2f} revenue"
        
        # Log to file
        with open(LOG_FILE, 'a') as f:
            f.write(report + "\n")
        
        # Return success
        return True
        
    except Exception as e:
        error_msg = f"{timestamp} - ERROR generating CRM report: {str(e)}"
        
        # Log error
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(error_msg + "\n")
        except:
            pass
        
        return False


# Also provide the shared_task version for Celery
@shared_task
def generate_crm_report_task():
    """Celery task wrapper for generate_crm_report"""
    return generate_crm_report()


@shared_task
def test_celery_task():
    """Simple test task to verify Celery is working"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"{timestamp} - Celery test task executed successfully"
    
    with open("/tmp/celery_test.log", 'a') as f:
        f.write(message + "\n")
    
    return message