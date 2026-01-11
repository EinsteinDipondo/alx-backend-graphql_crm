"""
Celery tasks for CRM application
"""

from celery import shared_task
from datetime import datetime
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@shared_task(bind=True)
def generate_crm_report(self):
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
        # Import GraphQL client
        from gql import gql, Client
        from gql.transport.requests import RequestsHTTPTransport
        
        # Setup GraphQL client
        transport = RequestsHTTPTransport(
            url='http://localhost:8000/graphql',
            verify=True,
            timeout=10,
        )
        
        client = Client(
            transport=transport,
            fetch_schema_from_transport=True,
        )
        
        # Define GraphQL query to get CRM statistics
        query = gql("""
            query GetCRMStats {
                # Get total customers
                customers {
                    id
                }
                
                # Get total orders with their total amounts
                orders {
                    id
                    totalAmount
                }
            }
        """)
        
        # Execute query
        result = client.execute(query)
        
        # Extract data
        customers = result.get('customers', [])
        orders = result.get('orders', [])
        
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
        return {
            'status': 'success',
            'message': report,
            'data': {
                'customers': total_customers,
                'orders': total_orders,
                'revenue': total_revenue
            }
        }
        
    except Exception as e:
        error_msg = f"{timestamp} - ERROR generating CRM report: {str(e)}"
        
        # Log error
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(error_msg + "\n")
        except:
            pass
        
        # Retry the task after 5 minutes if it fails
        raise self.retry(exc=e, countdown=300)


@shared_task
def test_celery_task():
    """Simple test task to verify Celery is working"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"{timestamp} - Celery test task executed successfully"
    
    with open("/tmp/celery_test.log", 'a') as f:
        f.write(message + "\n")
    
    return message