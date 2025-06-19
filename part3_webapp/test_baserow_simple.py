import requests

# Baserow configuration
API_TOKEN = "Akk9FxAJcL9iDwPf1Tybq9AtFR1VxgvV"
DATABASE_ID = 244113
BASE_URL = "https://api.baserow.io/api"

def test_baserow_connection():
    """Test Baserow API connection and database access."""
    headers = {
        "Authorization": f"Token {API_TOKEN}",
        "Content-Type": "application/json"
    }

    print("\nTesting Baserow connection...")
    print("-" * 50)

    # Test 1: List databases/applications
    print("\n1. Testing API token...")
    try:
        response = requests.get(f"{BASE_URL}/applications/", headers=headers)
        if response.status_code == 401:
            print("✗ API token is invalid!")
            print("  Please check your API token and make sure it has the necessary permissions.")
            return
        elif response.status_code != 200:
            print(f"✗ API request failed with status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return
            
        print("✓ API token is valid!")
        data = response.json()
        print(f"  Found {len(data)} workspace(s)")
        for app in data:
            print(f"  - Workspace: {app.get('name', 'Unnamed')}")

    except Exception as e:
        print(f"✗ Error connecting to Baserow: {str(e)}")
        return

    # Test 2: Check specific database access
    print("\n2. Testing database access...")
    try:
        response = requests.get(f"{BASE_URL}/database/tables/database/{DATABASE_ID}/", headers=headers)
        if response.status_code == 404:
            print(f"✗ Database {DATABASE_ID} not found!")
            print("  Please verify your database ID.")
            return
        elif response.status_code == 401:
            print("✗ Not authorized to access this database!")
            print("  Please check if your API token has access to this database.")
            return
        elif response.status_code != 200:
            print(f"✗ Database request failed with status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return
            
        tables = response.json()
        print(f"✓ Successfully accessed database {DATABASE_ID}!")
        if isinstance(tables, list):
            print(f"  Database contains {len(tables)} tables:")
            for table in tables:
                print(f"  - {table.get('name', 'Unnamed')} (ID: {table.get('id')})")
        else:
            print("  Warning: Unexpected response format when listing tables")
            print(f"  Response: {tables}")

    except Exception as e:
        print(f"✗ Error accessing database: {str(e)}")
        return

    print("\nStatus Summary:")
    print("-" * 50)
    print("API Token Status: Valid")
    print(f"Database {DATABASE_ID} Access: Successful")
    print("\n✓ Your Baserow configuration appears to be working correctly!")

if __name__ == "__main__":
    test_baserow_connection()
