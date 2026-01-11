"""
CRM Cron Jobs
Contains scheduled tasks for the CRM application
"""

import os
import sys
from datetime import datetime

# Add project to path for Django imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# HEARTBEAT LOGGER
# ============================================================================

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
        # ============================================
        try:
            # Import GraphQL client
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
                # Try introspection query if hello doesn't exist
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
# LOW STOCK UPDATER
# ============================================================================

def update_low_stock():
    """
    Cron job that runs every 12 hours to update low-stock products.
    Executes GraphQL mutation to increment stock for products with stock < 10.
    Logs updates to /tmp/low_stock_updates_log.txt
    """
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            
            # Define the mutation based on simplified schema
            # Using the simplified mutation that returns success, message, updated_count
            mutation = gql("""
                mutation {
                    updateLowStockProducts {
                        success
                        message
                        updatedCount
                    }
                }
            """)
            
            # Execute mutation
            result = client.execute(mutation)
            
            mutation_result = result.get('updateLowStockProducts', {})
            
            # Log the results
            success = mutation_result.get('success', False)
            message = mutation_result.get('message', 'No message received')
            updated_count = mutation_result.get('updatedCount', 0)
            
            # Prepare log entry
            log_entry = f"[{timestamp}] {message}\n"
            
            if success and updated_count > 0:
                log_entry += f"Successfully updated {updated_count} products with stock < 10\n"
            elif success:
                log_entry += "No products with stock < 10 found\n"
            else:
                log_entry += f"Update failed: {message}\n"
            
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
# TEST FUNCTIONS
# ============================================================================

def test_heartbeat():
    """Test the heartbeat function"""
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
    
    return success


def test_low_stock_update():
    """Test the update_low_stock function"""
    print("Testing low stock update...")
    
    success = update_low_stock()
    
    if success:
        print("✓ Low stock update completed")
        
        # Show log file
        try:
            with open("/tmp/low_stock_updates_log.txt", 'r') as f:
                lines = f.readlines()
                if lines:
                    print("Last log entries:")
                    for line in lines[-5:]:
                        print(line.rstrip())
        except:
            pass
    else:
        print("✗ Low stock update failed")
    
    return success


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Test both cron functions when script is run directly
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test CRM cron jobs")
    parser.add_argument('--test', choices=['heartbeat', 'lowstock', 'all'], 
                       default='all', help='Which test to run')
    
    args = parser.parse_args()
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
    
    try:
        import django
        django.setup()
    except Exception as e:
        print(f"Warning: Django setup failed: {e}")
    
    if args.test == 'heartbeat' or args.test == 'all':
        print("\n" + "="*50)
        print("TESTING HEARTBEAT LOGGER")
        print("="*50)
        heartbeat_success = test_heartbeat()
    
    if args.test == 'lowstock' or args.test == 'all':
        print("\n" + "="*50)
        print("TESTING LOW STOCK UPDATE")
        print("="*50)
        stock_success = test_low_stock_update()
    
    if args.test == 'all':
        print("\n" + "="*50)
        print("SUMMARY")
        print("="*50)
        print(f"Heartbeat: {'PASS' if heartbeat_success else 'FAIL'}")
        print(f"Low Stock: {'PASS' if stock_success else 'FAIL'}")
        
        sys.exit(0 if (heartbeat_success and stock_success) else 1)
    else:
        if args.test == 'heartbeat':
            sys.exit(0 if heartbeat_success else 1)
        else:  # lowstock
            sys.exit(0 if stock_success else 1)