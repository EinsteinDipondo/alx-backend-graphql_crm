"""
CRM Heartbeat Logger Cron Job
Logs heartbeat every 5 minutes with GraphQL endpoint verification
"""

import os
import sys
from datetime import datetime

# Add project to path for Django imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def log_crm_heartbeat():
    """
    Logs heartbeat message every 5 minutes.
    Format: DD/MM/YYYY-HH:MM:SS CRM is alive
    Also verifies GraphQL endpoint by querying the hello field.
    """
    
    # Get timestamp in required format
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    
    # Base message
    message = f"{timestamp} CRM is alive"
    
    try:
        # ============================================
        # GRAPHQL ENDPOINT VERIFICATION
        # Using gql library as requested
        # ============================================
        try:
            # Import GraphQL client - THESE IMPORTS ARE REQUIRED
            from gql import gql, Client
            from gql.transport.requests import RequestsHTTPTransport
            
            # Configure GraphQL client
            transport = RequestsHTTPTransport(
                url='http://localhost:8000/graphql',
                verify=True,
                retries=3,
            )
            
            client = Client(
                transport=transport,
                fetch_schema_from_transport=True,
            )
            
            # Define query for hello field
            # Note: Your schema must have a 'hello' field in your GraphQL schema
            query = gql("""
                query {
                    hello
                }
            """)
            
            # Execute query
            result = client.execute(query)
            
            if result and 'hello' in result:
                graphql_status = f"GraphQL: {result['hello']}"
            else:
                graphql_status = "GraphQL: No hello field in response"
                
        except Exception as graphql_error:
            graphql_status = f"GraphQL Error: {str(graphql_error)[:100]}"
        
        # Add GraphQL status to message
        message += f" | {graphql_status}"
        
        # ============================================
        # LOG TO FILE
        # ============================================
        
        log_file_path = "/tmp/crm_heartbeat_log.txt"
        
        # Append to log file (creates if doesn't exist)
        with open(log_file_path, 'a') as log_file:
            log_file.write(message + "\n")
        
        # Print to console for debugging
        print(f"Heartbeat logged: {message}")
        
        return True
        
    except Exception as e:
        # Error handling
        error_message = f"{timestamp} ERROR: {str(e)}"
        
        try:
            with open("/tmp/crm_heartbeat_log.txt", 'a') as log_file:
                log_file.write(error_message + "\n")
        except:
            # Last resort: print to stderr
            sys.stderr.write(error_message + "\n")
        
        return False


# ============================================================================
# ALTERNATIVE: If you don't have a 'hello' field in your schema
# ============================================================================

def log_crm_heartbeat_alternative():
    """
    Alternative version if your GraphQL schema doesn't have a 'hello' field.
    Uses introspection instead.
    """
    
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{timestamp} CRM is alive"
    
    try:
        # GraphQL verification
        try:
            from gql import gql, Client
            from gql.transport.requests import RequestsHTTPTransport
            
            transport = RequestsHTTPTransport(
                url='http://localhost:8000/graphql',
                verify=True,
            )
            
            client = Client(
                transport=transport,
                fetch_schema_from_transport=True,
            )
            
            # Use introspection query instead of 'hello'
            query = gql("""
                query {
                    __schema {
                        queryType {
                            name
                        }
                    }
                }
            """)
            
            result = client.execute(query)
            
            if result and '__schema' in result:
                graphql_status = "GraphQL: Endpoint responsive"
            else:
                graphql_status = "GraphQL: No response"
                
        except Exception as e:
            graphql_status = f"GraphQL: {str(e)[:50]}"
        
        message += f" | {graphql_status}"
        
        # Log to file
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(message + "\n")
        
        print(f"Heartbeat: {message}")
        return True
        
    except Exception as e:
        error_msg = f"{timestamp} ERROR: {str(e)}"
        try:
            with open("/tmp/crm_heartbeat_log.txt", "a") as f:
                f.write(error_msg + "\n")
        except:
            print(error_msg)
        return False


# ============================================================================
# TEST FUNCTION
# ============================================================================

if __name__ == "__main__":
    """Test the function directly"""
    print("Testing CRM heartbeat logger...")
    
    # Set up Django if needed
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
    
    try:
        import django
        django.setup()
    except Exception as e:
        print(f"Django setup warning: {e}")
    
    # Run the heartbeat function
    success = log_crm_heartbeat()
    
    if success:
        print("✓ Heartbeat logged successfully")
        
        # Show the log file
        try:
            with open("/tmp/crm_heartbeat_log.txt", 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"Last entry: {lines[-1].strip()}")
        except:
            pass
    else:
        print("✗ Failed to log heartbeat")
    
    sys.exit(0 if success else 1)
"""
Add to your existing crm/cron.py file
"""

def update_low_stock():
    """
    Cron job that runs every 12 hours to update low-stock products.
    Executes GraphQL mutation to increment stock for products with stock < 10.
    """
    
    from datetime import datetime
    import sys
    
    # Get timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Log file
    LOG_FILE = "/tmp/low_stock_updates_log.txt"
    
    try:
        # ============================================
        # EXECUTE GRAPHQL MUTATION
        # ============================================
        try:
            from gql import gql, Client
            from gql.transport.requests import RequestsHTTPTransport
            
            # Setup GraphQL client
            transport = RequestsHTTPTransport(
                url='http://localhost:8000/graphql',
                verify=True,
            )
            
            client = Client(
                transport=transport,
                fetch_schema_from_transport=True,
            )
            
            # Define the mutation
            # Adjust based on your actual mutation name and structure
            mutation = gql("""
                mutation UpdateLowStock($incrementBy: Int = 10) {
                    updateLowStockProducts(incrementBy: $incrementBy) {
                        message
                        count
                        updatedProducts {
                            product {
                                id
                                name
                                sku
                                stock
                            }
                            previousStock
                            newStock
                        }
                    }
                }
            """)
            
            # Execute mutation
            variables = {"incrementBy": 10}
            result = client.execute(mutation, variable_values=variables)
            
            mutation_result = result.get('updateLowStockProducts', {})
            
            # Log the results
            message = mutation_result.get('message', 'No message')
            count = mutation_result.get('count', 0)
            updated_products = mutation_result.get('updatedProducts', [])
            
            # Prepare log entry
            log_entry = f"[{timestamp}] {message}\n"
            
            if updated_products:
                log_entry += f"Updated {count} products:\n"
                for item in updated_products:
                    product = item.get('product', {})
                    product_name = product.get('name', 'Unknown Product')
                    product_sku = product.get('sku', 'N/A')
                    previous_stock = item.get('previousStock', 'N/A')
                    new_stock = item.get('newStock', 'N/A')
                    
                    log_entry += f"  - {product_name} (SKU: {product_sku}): {previous_stock} -> {new_stock}\n"
            else:
                log_entry += "No products were updated.\n"
            
            log_entry += "-" * 50 + "\n"
            
        except Exception as graphql_error:
            log_entry = f"[{timestamp}] ERROR executing GraphQL mutation: {str(graphql_error)}\n"
        
        # ============================================
        # WRITE TO LOG FILE
        # ============================================
        
        try:
            with open(LOG_FILE, 'a') as log_file:
                log_file.write(log_entry)
            
            # Also print to console for debugging
            print(f"Low stock update executed: {timestamp}")
            print(log_entry)
            
            return True
            
        except Exception as log_error:
            print(f"[{timestamp}] ERROR writing to log file: {str(log_error)}")
            return False
            
    except Exception as e:
        # Global error handling
        error_msg = f"[{timestamp}] CRITICAL ERROR in update_low_stock: {str(e)}\n"
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(error_msg)
        except:
            print(error_msg)
        return False


# ============================================================================
# ALTERNATIVE: Using Direct Django ORM (if GraphQL isn't working)
# ============================================================================

def update_low_stock_direct():
    """
    Alternative version that uses Django ORM directly instead of GraphQL.
    Useful for debugging or if GraphQL mutation isn't working.
    """
    
    from datetime import datetime
    import os
    import django
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
    django.setup()
    
    from crm.models import Product
    from django.db.models import F
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG_FILE = "/tmp/low_stock_updates_log.txt"
    
    try:
        # Get low stock products
        low_stock = Product.objects.filter(stock__lt=10)
        count = low_stock.count()
        
        log_entry = f"[{timestamp}] "
        
        if count == 0:
            log_entry += "No products with stock < 10 found.\n"
        else:
            # Get details before update
            product_details = []
            for product in low_stock:
                product_details.append({
                    'name': product.name,
                    'sku': product.sku,
                    'previous_stock': product.stock,
                    'new_stock': product.stock + 10
                })
            
            # Update stock
            updated = low_stock.update(stock=F('stock') + 10)
            
            log_entry += f"Updated {updated} low-stock products:\n"
            for detail in product_details:
                log_entry += f"  - {detail['name']} (SKU: {detail['sku']}): {detail['previous_stock']} -> {detail['new_stock']}\n"
        
        log_entry += "-" * 50 + "\n"
        
        # Write to log
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
        
        print(f"Direct update executed: {log_entry}")
        return True
        
    except Exception as e:
        error_msg = f"[{timestamp}] ERROR in direct update: {str(e)}\n"
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(error_msg)
        except:
            print(error_msg)
        return False


# ============================================================================
# TEST FUNCTION
# ============================================================================

def test_update_low_stock():
    """Test the update_low_stock function"""
    print("Testing low stock update...")
    
    # Test with GraphQL
    print("Testing GraphQL version...")
    result = update_low_stock()
    
    if result:
        print("✓ GraphQL update completed")
        
        # Show log file
        try:
            with open("/tmp/low_stock_updates_log.txt", 'r') as f:
                lines = f.readlines()
                if lines:
                    print("Last 5 log entries:")
                    for line in lines[-10:]:
                        print(line.rstrip())
        except:
            pass
    else:
        print("✗ GraphQL update failed")
        
        # Try direct version
        print("\nTrying direct Django ORM version...")
        result2 = update_low_stock_direct()
        if result2:
            print("✓ Direct update completed")
        else:
            print("✗ Both methods failed")
    
    return result


if __name__ == "__main__":
    # When testing, you might want to use the direct version first
    # success = update_low_stock_direct()
    success = update_low_stock()
    sys.exit(0 if success else 1)
