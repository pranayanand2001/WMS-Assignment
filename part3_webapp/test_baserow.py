import requests
import sys

def test_baserow_connection(api_token: str, database_id: int):
    """Test Baserow API connection and database access."""
    base_url = "https://api.baserow.io/api"
    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/json"
    }

    print("\nTesting Baserow connection...")
    print("-" * 50)

    # Test 1: Check if we can access Baserow API
    print("\n1. Testing API token...")
    try:
        response = requests.get(f"{base_url}/applications/", headers=headers)
        response.raise_for_status()
        print("✓ API token is valid! Successfully connected to Baserow.")
        print(f"  User has access to {len(response.json())} workspaces.")
    except requests.exceptions.HTTPError as e:
        print("✗ API token test failed!")
        if e.response.status_code == 401:
            print("  Error: Invalid API token")
        elif e.response.status_code == 403:
            print("  Error: Token lacks necessary permissions")
        else:
            print(f"  Error: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error connecting to Baserow: {str(e)}")
        return False

    # Test 2: Check database access
    print("\n2. Testing database access...")
    try:
        response = requests.get(f"{base_url}/database/tables/database/{database_id}/", headers=headers)
        response.raise_for_status()
        tables = response.json()
        print(f"✓ Successfully accessed database {database_id}!")
        if isinstance(tables, list):
            print(f"  Database contains {len(tables)} tables:")
            for table in tables:
                print(f"  - {table.get('name', 'Unnamed')} (ID: {table.get('id')})")
    except requests.exceptions.HTTPError as e:
        print("✗ Database access test failed!")
        if e.response.status_code == 404:
            print(f"  Error: Database {database_id} not found")
        elif e.response.status_code == 401:
            print("  Error: Invalid API token")
        elif e.response.status_code == 403:
            print("  Error: Token lacks access to this database")
        else:
            print(f"  Error: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error accessing database: {str(e)}")
        return False

    print("\n✓ All tests passed! Your Baserow configuration is valid.")
    return True

if __name__ == "__main__":
    # Get configuration from app.py
    try:
        from app import app
        api_token = app.config.get('BASEROW_API_TOKEN')
        database_id = app.config.get('BASEROW_DATABASE_ID')
        
        if not api_token or not database_id:
            print("Error: API token or Database ID not found in app configuration.")
            sys.exit(1)
            
        test_baserow_connection(api_token, database_id)
    except ImportError:
        print("Error: Could not import Flask app configuration.")
        print("Please make sure you're running this script from the correct directory.")
        sys.exit(1)
