"""
CRM Cron Jobs
Contains scheduled tasks for the CRM application
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
    Optionally queries GraphQL hello field to verify endpoint is responsive.
    """
    
    # Get timestamp in required format: DD/MM/YYYY-HH:MM:SS
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    
    # Base message
    message = f"{timestamp} CRM is alive"
    
    try:
        # ============================================
        # GRAPHQL ENDPOINT VERIFICATION (Optional)
        # ============================================
        try:
            # Import GraphQL client
            from gql import gql, Client
            from gql.transport.requests import RequestsHTTPTransport
            
            # Configure GraphQL client
            transport = RequestsHTTPTransport(
                url='http://localhost:8000/graphql',
                verify=True,
                timeout=5,
            )
            
            client = Client(
                transport=transport,
                fetch_schema_from_transport=True,
            )
            
            # Try to query hello field
            try:
                query = gql("""
                    query {
                        hello
                    }
                """)
                
                result = client.execute(query)
                
                if result and 'hello' in result:
                    graphql_status = f"GraphQL: {result['hello']}"
                else:
                    # If no hello field, try introspection
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
                        
            except Exception as query_error:
                graphql_status = f"GraphQL: Query failed - {str(query_error)[:50]}"
                
        except ImportError:
            graphql_status = "GraphQL: gql library not installed"
        except Exception as e:
            graphql_status = f"GraphQL: Connection failed - {str(e)[:50]}"
        
        # Add GraphQL status to message
        message += f" | {graphql_status}"
        
        # ============================================
        # LOG TO FILE
        # ============================================
        
        log_file_path = "/tmp/crm_heartbeat_log.txt"
        
        # Append to log file (creates if doesn't exist)
        with open(log_file_path, 'a') as log_file:
            log_file.write(message + "\n")
        
        # Print to console for debugging (when run manually)
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
# Other cron functions (keep your existing functions)
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
        
        mutation = gql("""
            mutation {
                updateLowStockProducts {
                    success
                    message
                    updatedCount
                }
            }
        """)
        
        result = client.execute(mutation)
        data = result.get('updateLowStockProducts', {})
        
        log_entry = f"[{timestamp}] {data.get('message', 'No message')}\n"
        log_entry += "-" * 50 + "\n"
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
        
        print(f"Low stock update: {log_entry}")
        return True
        
    except Exception as e:
        error_msg = f"[{timestamp}] ERROR: {str(e)}\n"
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(error_msg)
        except:
            print(error_msg)
        return False


# ============================================================================
# TEST FUNCTION
# ============================================================================

if __name__ == "__main__":
    """
    Test the heartbeat function when script is run directly
    """
    print("Testing CRM heartbeat logger...")
    
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
    
    try:
        import django
        django.setup()
    except Exception as e:
        print(f"Django setup warning: {e}")
    
    # Test heartbeat function
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