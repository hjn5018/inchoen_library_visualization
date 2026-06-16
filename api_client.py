import os
import requests
import pandas as pd
from dotenv import load_dotenv
from mock_data import get_mock_library_data

# Load environment variables
load_dotenv()

class IncheonLibraryAPIClient:
    """
    API client for fetching and cleaning Incheon Library Information from Incheon Data Portal.
    Includes robust error handling and automatic mock data fallback.
    """
    BASE_URL = "https://data.incheon.go.kr/openapi/LBRRY/LBRRY"

    def __init__(self, api_key=None):
        # Prefer provided key, fallback to env variable
        self.api_key = api_key or os.getenv("INCHEON_API_KEY")

    def has_valid_key(self):
        """Checks if the API key is configured."""
        return bool(self.api_key and self.api_key != "your_api_key_here")

    def fetch_raw_data(self):
        """
        Fetches all pages from the Open API.
        If no API key is present or request fails, returns None.
        """
        if not self.has_valid_key():
            print("API Key not found or invalid. Falling back to mock data.")
            return None

        all_rows = []
        page_no = 0
        limit = 1000  # Safety limit to prevent infinite loops
        
        while page_no < limit:
            params = {
                "apiKey": self.api_key,
                "pageNo": page_no,
                "returnType": "json"
            }
            
            try:
                print(f"Fetching Incheon Library API page {page_no}...")
                response = requests.get(self.BASE_URL, params=params, timeout=10)
                
                # Check status code
                if response.status_code != 200:
                    print(f"API returned status code {response.status_code}")
                    break
                    
                data = response.json()
                
                # Incheon Data Portal API format is typically { "LBRRY": { "row": [...], "totalCount": 123 } }
                if "LBRRY" in data:
                    lbrry_data = data["LBRRY"]
                    rows = lbrry_data.get("row", [])
                    total_count = lbrry_data.get("totalCount", 0)
                    
                    if not rows:
                        print(f"No more data rows returned at page {page_no}.")
                        break
                        
                    all_rows.extend(rows)
                    print(f"Successfully fetched {len(rows)} rows from page {page_no}. Total fetched: {len(all_rows)}")
                    
                    # If we have fetched everything, stop
                    if len(all_rows) >= int(total_count):
                        print("All records fetched based on totalCount.")
                        break
                        
                    page_no += 1
                else:
                    # Check for API-level errors (like Invalid API Key)
                    print(f"Unexpected response structure: {data}")
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"HTTP Request error: {e}")
                break
            except ValueError as e:
                print(f"JSON Parsing error: {e}")
                # Print sample of response to debug if it's returning HTML error instead of JSON
                try:
                    print(f"Response snippet: {response.text[:200]}")
                except:
                    pass
                break

        return all_rows if all_rows else None

    def get_library_dataframe(self):
        """
        Fetches data and processes it into a cleaned pandas DataFrame.
        Falls back to mock data if API data cannot be fetched.
        """
        raw_data = self.fetch_raw_data()
        is_mock = False
        
        if raw_data is None:
            print("Using fallback mock library data.")
            raw_data = get_mock_library_data()
            is_mock = True
            
        df = pd.DataFrame(raw_data)
        return self.clean_dataframe(df), is_mock

    def clean_dataframe(self, df):
        """
        Cleans the library DataFrame:
        - Conversions of numeric columns (BOOK_CNT, PRSL_SEAT_CNT, LAT, LOT)
        - Handling missing coordinates
        - Standardizing and cleaning district names (SGG_NM)
        """
        if df.empty:
            return df

        # Define fields to ensure they exist
        required_cols = ['LBRRY_NM', 'SGG_NM', 'LBRRY_TYPE', 'LCTN_ROAD_NM_ADDR', 'LAT', 'LOT', 'BOOK_CNT', 'PRSL_SEAT_CNT']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        # Convert numeric columns
        df['BOOK_CNT'] = pd.to_numeric(df['BOOK_CNT'], errors='coerce').fillna(0).astype(int)
        df['PRSL_SEAT_CNT'] = pd.to_numeric(df['PRSL_SEAT_CNT'], errors='coerce').fillna(0).astype(int)
        df['LAT'] = pd.to_numeric(df['LAT'], errors='coerce')
        df['LOT'] = pd.to_numeric(df['LOT'], errors='coerce')

        # Clean/standardize SGG_NM (District Name)
        df['SGG_NM'] = df['SGG_NM'].astype(str).str.strip()
        
        # If SGG_NM is missing, empty or 'None', try to parse it from the road name address
        def extract_sgg_from_address(row):
            sgg = row['SGG_NM']
            if not sgg or sgg == 'None' or sgg == 'nan' or sgg == '':
                addr = str(row['LCTN_ROAD_NM_ADDR'])
                # Look for "군" or "구" in address like "인천광역시 남동구 ..."
                parts = addr.split()
                for part in parts:
                    if part.endswith('구') or part.endswith('군'):
                        return part
            return sgg

        df['SGG_NM'] = df.apply(extract_sgg_from_address, axis=1)
        # Normalize naming (remove "인천시" prefix if it exists in district names, though rare)
        df['SGG_NM'] = df['SGG_NM'].replace({'nan': '미분류', 'None': '미분류', '': '미분류'})
        
        # Clean library type
        df['LBRRY_TYPE'] = df['LBRRY_TYPE'].fillna('기타').astype(str).str.strip()
        df['LBRRY_TYPE'] = df['LBRRY_TYPE'].replace({'': '기타', 'None': '기타'})

        # Filter out invalid coordinates for mapping, but keep them for general stats (we'll handle NaN in map code)
        return df

if __name__ == "__main__":
    # Test execution
    client = IncheonLibraryAPIClient()
    df, is_mock = client.get_library_dataframe()
    print("\n--- Data Load Test ---")
    print(f"Data Source: {'Mock Data (Fallback)' if is_mock else 'Live API'}")
    print(f"Total Records: {len(df)}")
    print(df[['LBRRY_NM', 'SGG_NM', 'LBRRY_TYPE', 'BOOK_CNT', 'LAT', 'LOT']].head())
