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
