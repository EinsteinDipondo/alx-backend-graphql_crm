#!/usr/bin/env python3
"""
GraphQL-Based Order Reminder Script
Queries pending orders from the last 7 days and logs reminders
"""

import asyncio
import sys
import os
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
# GRAPHQL QUERY
# ============================================================================

# Define the GraphQL query
# Adjust this query based on your actual GraphQL schema
GRAPHQL_QUERY = """
query GetRecentOrders($daysAgo: Int!) {
  # This query depends on your GraphQL schema
  # Example structure - UPDATE BASED ON YOUR SCHEMA:
  orders(where: {
    order_date_gte: $daysAgo,
    status: "pending"
  }) {
    id
    orderDate
    customer {
      email
      name
    }
    totalAmount
  }
}

# Alternative query if your schema is different:
# query GetRecentOrders($startDate: String!) {
#   orders(filter: {orderDate: {gte: $startDate}, status: "PENDING"}) {
#     edges {
#       node {
#         id
#         orderDate
#         customerEmail
#         customerName
#       }
#     }
#   }
# }
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_start_date(days_back: int) -> str:
    """Calculate date string for X days ago"""
    start_date = datetime.now() - timedelta(days=days_back)
    # Format as ISO string (adjust based on your GraphQL schema requirements)
    return start_date.strftime("%Y-%m-%dT%H:%M:%S")

def write_log(message: str):
    """Write message to log file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_message + "\n")
        print(log_message)  # Also print to console
    except Exception as e:
        print(f"ERROR: Could not write to log file: {e}")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    """Main async function to fetch and log order reminders"""
    
    write_log("Starting order reminder processing...")
    
    try:
        # Create transport
        transport = AIOHTTPTransport(url=GRAPHQL_ENDPOINT)
        
        # Create GraphQL client
        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as session:
            
            # Calculate date for query
            # Adjust based on your GraphQL schema variable requirements
            start_date = get_start_date(DAYS_BACK)
            
            # Prepare query variables
            # This depends on how your GraphQL query accepts parameters
            variables = {
                "daysAgo": DAYS_BACK,
                # OR "startDate": start_date, depending on your schema
            }
            
            # Execute query
            write_log(f"Querying GraphQL endpoint: {GRAPHQL_ENDPOINT}")
            write_log(f"Looking for orders from last {DAYS_BACK} days")
            
            query = gql(GRAPHQL_QUERY)
            result = await session.execute(query, variable_values=variables)
            
            # Process results
            # Adjust this based on your actual GraphQL response structure
            
            orders = result.get('orders', [])
            
            if not orders:
                write_log("No recent pending orders found")
            else:
                write_log(f"Found {len(orders)} recent pending orders")
                
                # Log each order
                for order in orders:
                    try:
                        order_id = order.get('id', 'N/A')
                        # Adjust based on your schema structure
                        customer_email = order.get('customer', {}).get('email', 'N/A')
                        order_date = order.get('orderDate', 'N/A')
                        
                        log_message = (
                            f"Order ID: {order_id}, "
                            f"Customer Email: {customer_email}, "
                            f"Order Date: {order_date}"
                        )
                        write_log(log_message)
                        
                    except Exception as order_error:
                        write_log(f"Error processing order: {order_error}")
            
            # Success message
            write_log("Order reminders processed!")
            print("Order reminders processed!")  # As per requirements
            
    except Exception as e:
        error_msg = f"ERROR: Failed to process order reminders: {str(e)}"
        write_log(error_msg)
        print(error_msg)
        sys.exit(1)

# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
    
    # Add separator for log readability
    try:
        with open(LOG_FILE, 'a') as f:
            f.write("=" * 50 + "\n")
    except:
        pass
