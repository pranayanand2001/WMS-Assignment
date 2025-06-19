import requests
import json
import pandas as pd
from typing import List, Dict, Any

class BaserowClient:
    def __init__(self, api_token: str, database_id: int | None = None, base_url: str = "https://api.baserow.io/api"):
        if not api_token:
            raise ValueError("API token is required")
        self.api_token = api_token
        self.base_url = base_url
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
        # Verify authentication on initialization
        self._verify_authentication()
        
    def _verify_authentication(self) -> None:
        """Verify that the API token is valid by checking database access."""
        try:
            # Try to access database information as a simple auth check
            url = f"{self.base_url}/database/applications/"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Check if we can access the specific database
            if hasattr(self, 'database_id'):
                url = f"{self.base_url}/database/tables/database/{self.database_id}/"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid API token. Please check your Baserow API token.") from e
            elif e.response.status_code == 404 and hasattr(self, 'database_id'):
                raise ValueError(f"Database with ID {self.database_id} not found or not accessible.") from e
            elif e.response.status_code == 403:
                raise ValueError("API token does not have sufficient permissions.") from e
            raise

    def create_table(self, database_id: int, name: str, fields: List[Dict[str, str]]) -> int:
        """Create a new table in the specified database."""
        if not database_id or not name or not fields:
            raise ValueError("Database ID, name, and fields are required")
            
        url = f"{self.base_url}/database/tables/database/{database_id}/"
        
        payload = {
            "name": name,
            "fields": fields
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()["id"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid API token or insufficient permissions") from e
            elif e.response.status_code == 404:
                raise ValueError(f"Database with ID {database_id} not found") from e
            raise

    def create_rows(self, table_id: int, rows: List[Dict]) -> List[Dict]:
        """Create multiple rows in a table."""
        url = f"{self.base_url}/database/rows/table/{table_id}/batch/"
        
        # Convert all values to strings to ensure compatibility
        processed_rows = []
        for row in rows:
            processed_row = {}
            for key, value in row.items():
                if pd.isna(value):
                    processed_row[str(key)] = ''
                else:
                    processed_row[str(key)] = str(value) if not isinstance(value, (int, float, bool)) else value
            processed_rows.append(processed_row)
        
        payload = {
            "items": processed_rows
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()["items"]

    def get_or_create_table(self, database_id: int, name: str, fields: List[Dict[str, str]]) -> int:
        """Get existing table or create a new one."""
        if not database_id or not name or not fields:
            raise ValueError("Database ID, name, and fields are required")

        try:
            # First try to create the table
            return self.create_table(database_id, name, fields)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                # If creation failed due to duplicate, try to find existing table
                try:
                    url = f"{self.base_url}/database/tables/database/{database_id}/"
                    response = requests.get(url, headers=self.headers)
                    response.raise_for_status()
                    
                    # Check if table exists
                    tables = response.json()
                    if isinstance(tables, list):
                        for table in tables:
                            if table.get("name") == name:
                                return table.get("id")
                    
                    # If we get here, table wasn't found
                    raise ValueError(f"Could not find or create table '{name}'")
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        raise ValueError("Invalid API token or insufficient permissions") from e
                    elif e.response.status_code == 404:
                        raise ValueError(f"Database with ID {database_id} not found") from e
                    raise
            elif e.response.status_code == 401:
                raise ValueError("Invalid API token or insufficient permissions") from e
            elif e.response.status_code == 404:
                raise ValueError(f"Database with ID {database_id} not found") from e
            raise

def prepare_fields_from_dataframe(df):
    """Convert DataFrame columns to Baserow field definitions."""
    fields = []
    for column in df.columns:
        field = {
            "name": column,
            "type": "text"  # Default to text type
        }
        
        # Try to determine appropriate field type
        sample = df[column].iloc[0] if not df[column].empty else None
        if pd.api.types.is_numeric_dtype(df[column]):
            if df[column].dtype == 'int64':
                field["type"] = "number"
                field["number_decimal_places"] = 0
            else:
                field["type"] = "number"
                field["number_decimal_places"] = 2
        elif pd.api.types.is_datetime64_any_dtype(df[column]):
            field["type"] = "date"
            
        fields.append(field)
    
    return fields

def prepare_rows_from_dataframe(df):
    """Convert DataFrame rows to Baserow row format."""
    return df.to_dict('records')
