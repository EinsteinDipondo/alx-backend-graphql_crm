#!/usr/bin/env python3
"""
GraphQL-Based Order Reminder Script
Queries pending orders from the last 7 days and logs reminders.
Runs daily at 8:00 AM.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# ============================================================================
# CONFIGURATION
# ============================================================================

# GraphQL endpoint URL
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"

# Log file location
LOG_FILE = "/tmp/order_reminders_log.txt"

# Number of days to look back for orders
DAYS_BACK = 7

# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    """Main async function to fetch and log order reminders"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Create transport
        transport = AIOHTTPTransport(url=GRAPHQL_ENDPOINT)
        
        # Create GraphQL client
        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as session:
            
            # Calculate date for query
            since_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")
            
            # Define GraphQL query based on your schema
            # Adjust this query based on your actual GraphQL schema
            query = gql("""
                query GetRecentOrders($since: String!) {
                    # Adjust this query based on your actual schema
                    # Example: query orders with order_date within last 7 days
                    orders(orderDate_Gte: $since) {
                        edges {
                            node {
                                id
                                orderDate
                                status
                                customer {
                                    email
                                    name
                                }
                            }
                        }
                    }
                }
            """)
            
            # Execute query
            variables = {"since": since_date}
            result = await session.execute(query, variable_values=variables)
            
            # Process results based on your schema structure
            orders = result.get('orders', {}).get('edges', [])
            
            if not orders:
                log_message = f"[{timestamp}] No orders found from the last {DAYS_BACK} days\n"
            else:
                log_message = f"[{timestamp}] Found {len(orders)} orders from the last {DAYS_BACK} days:\n"
                
                # Log each order's ID and customer email
                for order_edge in orders:
                    order = order_edge['node']
                    order_id = order.get('id', 'N/A')
                    order_date = order.get('orderDate', 'N/A')
                    customer_email = order.get('customer', {}).get('email', 'N/A')
                    customer_name = order.get('customer', {}).get('name', 'N/A')
                    status = order.get('status', 'N/A')
                    
                    log_message += f"  Order ID: {order_id}, Date: {order_date}, Status: {status}, Customer: {customer_name} ({customer_email})\n"
            
            log_message += "=" * 60 + "\n"
            
            # Write to log file
            with open(LOG_FILE, 'a') as f:
                f.write(log_message)
            
            # Print success message to console (required by instructions)
            print("Order reminders processed!")
            
            return True
            
    except Exception as e:
        error_msg = f"[{timestamp}] ERROR: {str(e)}\n"
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(error_msg)
        except:
            print(error_msg)
        
        print("Order reminders processed! (with errors)")
        return False

# ============================================================================
# ALTERNATIVE: Synchronous version (if async doesn't work)
# ============================================================================

def send_order_reminders_sync():
    """Synchronous version of order reminder script"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        from gql import gql, Client
        from gql.transport.requests import RequestsHTTPTransport
        
        # Setup GraphQL client
        transport = RequestsHTTPTransport(
            url=GRAPHQL_ENDPOINT,
            verify=True,
        )
        
        client = Client(
            transport=transport,
            fetch_schema_from_transport=True,
        )
        
        # Calculate date
        since_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")
        
        # Define GraphQL query - adjust based on your schema
        query = gql("""
            query GetRecentOrders($since: String!) {
                # Try different query formats based on your schema
                allOrders(orderDate_Gte: $since) {
                    id
                    orderDate
                    status
                    customer {
                        email
                        name
                    }
                }
            }
        """)
        
        # Execute query
        variables = {"since": since_date}
        result = client.execute(query, variable_values=variables)
        
        # Process results
        orders = result.get('allOrders', [])
        
        if not orders:
            log_message = f"[{timestamp}] No orders found from the last {DAYS_BACK} days\n"
        else:
            log_message = f"[{timestamp}] Found {len(orders)} orders from the last {DAYS_BACK} days:\n"
            
            for order in orders:
                order_id = order.get('id', 'N/A')
                order_date = order.get('orderDate', 'N/A')
                customer_email = order.get('customer', {}).get('email', 'N/A')
                customer_name = order.get('customer', {}).get('name', 'N/A')
                
                log_message += f"  Order ID: {order_id}, Customer Email: {customer_email}, Date: {order_date}\n"
        
        log_message += "=" * 60 + "\n"
        
        # Write to log file
        with open(LOG_FILE, 'a') as f:
            f.write(log_message)
        
        print("Order reminders processed!")
        return True
        
    except Exception as e:
        error_msg = f"[{timestamp}] ERROR: {str(e)}\n"
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(error_msg)
        except:
            print(error_msg)
        
        print("Order reminders processed! (with errors)")
        return False

# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Try async version first, fall back to sync if needed
    try:
        # Run async main function
        asyncio.run(main())
    except Exception as e:
        print(f"Async version failed, trying sync: {e}")
        send_order_reminders_sync()
