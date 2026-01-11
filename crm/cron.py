"""
CRM Heartbeat Logger Cron Job
This module defines cron jobs for the CRM application.
"""

import os
import sys
from datetime import datetime
import logging

# Optional: Import Django components for GraphQL verification
try:
    from django.conf import settings
    # Only import graphene if you want to verify GraphQL endpoint
    # from graphene import Schema
    # from your_app.schema import schema
except ImportError:
    # Django not available in some contexts
    pass

# ============================================================================
# HEARTBEAT LOGGER FUNCTION
# ============================================================================

def log_crm_heartbeat():
    """
    Logs a heartbeat message every 5 minutes to confirm CRM health.
    
    This function:
    1. Logs timestamped "CRM is alive" message
    2. Optionally verifies GraphQL endpoint is responsive
    3. Appends to log file without overwriting
    """
    
    # Log file path
    LOG_FILE = "/tmp/crm_heartbeat_log.txt"
    
    # Get current timestamp in required format: DD/MM/YYYY-HH:MM:SS
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    
    # Prepare the heartbeat message
    heartbeat_message = f"{timestamp} CRM is alive"
    
    try:
        # ============================================
        # OPTIONAL: Verify GraphQL endpoint is responsive
        # ============================================
        # Uncomment and adapt this section if you want to verify GraphQL
        """
        try:
            # Example: Query a simple GraphQL field
            # This assumes you have a GraphQL schema with a 'hello' field
            from graphene import Schema
            from your_app.schema import Query
            
            schema = Schema(query=Query)
            result = schema.execute('{ hello }')
            
            if result.data and result.data.get('hello'):
                heartbeat_message += f" | GraphQL: {result.data['hello']}"
            else:
                heartbeat_message += " | GraphQL: No response"
                
        except Exception as graphql_error:
            heartbeat_message += f" | GraphQL Error: {str(graphql_error)}"
        """
        
        # ============================================
        # ALTERNATIVE: Simple GraphQL verification
        # ============================================
        # If you want to test the GraphQL endpoint without executing queries
        
        graphql_status = "Not checked"
        
        try:
            # Simple check: Verify GraphQL endpoint exists
            # You could make an HTTP request to the GraphQL endpoint
            import requests
            response = requests.post(
                'http://localhost:8000/graphql',
                json={'query': '{ __schema { queryType { name } } }'},
                timeout=5
            )
            if response.status_code == 200:
                graphql_status = "GraphQL: Responsive"
            else:
                graphql_status = f"GraphQL: HTTP {response.status_code}"
                
            heartbeat_message += f" | {graphql_status}"
            
        except requests.exceptions.RequestException as e:
            heartbeat_message += f" | GraphQL: Unreachable ({str(e)})"
        except ImportError:
            # requests not installed
            heartbeat_message += " | GraphQL: Check skipped (requests not installed)"
        except Exception as e:
            heartbeat_message += f" | GraphQL: Check failed ({str(e)})"
        
        # ============================================
        # LOG THE HEARTBEAT MESSAGE
        # ============================================
        
        # Append to log file (creates file if doesn't exist)
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(heartbeat_message + "\n")
        
        # Also print to console for debugging (visible when running manually)
        print(f"Heartbeat logged: {heartbeat_message}")
        
        return True
        
    except Exception as e:
        # If logging fails, try to log the error
        error_message = f"{timestamp} ERROR: Failed to log heartbeat - {str(e)}"
        try:
            with open(LOG_FILE, 'a') as log_file:
                log_file.write(error_message + "\n")
        except:
            # Last resort: print to stderr
            sys.stderr.write(error_message + "\n")
        
        return False


# ============================================================================
# ADDITIONAL CRON JOBS (Optional)
# ============================================================================

def log_crm_status():
    """Optional: More detailed CRM status check"""
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{timestamp} CRM status check completed"
    
    try:
        # You could add database checks, cache checks, etc.
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "Database: OK"
    except Exception as e:
        db_status = f"Database: Error - {str(e)}"
    
    full_message = f"{message} | {db_status}"
    
    with open("/tmp/crm_status_log.txt", 'a') as f:
        f.write(full_message + "\n")
    
    return True


def cleanup_old_logs():
    """Optional: Clean up old log files"""
    import os
    import glob
    from datetime import datetime, timedelta
    
    log_pattern = "/tmp/crm_*.log"
    days_to_keep = 7
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    for log_file in glob.glob(log_pattern):
        try:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            if file_mtime < cutoff_date:
                os.remove(log_file)
                print(f"Removed old log: {log_file}")
        except Exception as e:
            print(f"Error removing {log_file}: {e}")
    
    return True


# ============================================================================
# TEST FUNCTION (for manual testing)
# ============================================================================

if __name__ == "__main__":
    """Test the heartbeat function manually"""
    print("Testing CRM heartbeat logger...")
    result = log_crm_heartbeat()
    
    if result:
        print("✓ Heartbeat logged successfully")
        # Show last line of log
        try:
            with open("/tmp/crm_heartbeat_log.txt", 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"Last log entry: {lines[-1].strip()}")
        except:
            pass
    else:
        print("✗ Heartbeat logging failed")
    
    sys.exit(0 if result else 1)
