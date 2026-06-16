import os
import requests
import pandas as pd
import json
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class IncheonLibraryAPIClient:
    """
    인천데이터포털에서 인천 도서관 정보를 가져오고 정제하는 API 클라이언트입니다.
    API 인증키가 없거나 연결에 실패할 경우 로컬 JSON 파일로 대체(Fallback)하는 기능이 내장되어 있습니다.
    """
    BASE_URL = "https://data.incheon.go.kr/openapi/LBRRY/LBRRY"

    def __init__(self, api_key=None):
        # 제공된 키를 우선으로 사용하고, 없으면 환경 변수(INCHEON_API_KEY)에서 가져옵니다.
        self.api_key = api_key or os.getenv("INCHEON_API_KEY")

    def has_valid_key(self):
        """API 인증키가 유효하게 설정되어 있는지 확인합니다."""
        return bool(self.api_key and self.api_key != "your_api_key_here")

    def fetch_raw_data(self):
        """
        인천데이터포털 Open API로부터 데이터를 호출하여 반환합니다. (pageNo=0 고정)
        인증키가 유효하지 않거나 통신 오류가 발생하면 None을 반환합니다.
        """
        if not self.has_valid_key():
            print("API 인증키가 설정되지 않았거나 유효하지 않습니다. 로컬 JSON 파일로 대체합니다.")
            return None

        params = {
            "apiKey": self.api_key,
            "pageNo": 0,
            "returnType": "json"
        }
        
        try:
            print("인천 도서관 API 호출 중... (pageNo: 0 고정)")
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            
            # HTTP 응답 상태 코드 확인
            if response.status_code != 200:
                print(f"API 호출 오류 발생. 상태 코드: {response.status_code}")
                return None
                
            data = response.json()
            
            # 인천데이터포털 API 표준 응답 형식: { "LBRRY": { "row": [...], "totalCount": 123 } }
            if "LBRRY" in data:
                lbrry_data = data["LBRRY"]
                rows = lbrry_data.get("row", [])
                print(f"성공적으로 {len(rows)}개의 행을 수신했습니다.")
                return rows
            else:
                # 잘못된 인증키 등의 API 오류 응답 처리
                print(f"예상치 못한 응답 구조 수신: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"HTTP 통신 중 오류 발생: {e}")
        except ValueError as e:
            print(f"JSON 파싱 중 오류 발생: {e}")

        return None

    def get_library_dataframe(self):
        """
        도서관 데이터를 가져와서 정제된 pandas DataFrame으로 변환하여 반환합니다.
        오픈 API 데이터를 가져오지 못하는 경우 real_api_response.json 파일에서 데이터를 로드합니다.
        """
        raw_data = self.fetch_raw_data()
        is_mock = False
        
        if raw_data is None:
            print("로컬 real_api_response.json 파일 데이터를 대체하여 로드합니다.")
            # Streamlit 실행 경로(v1/)와 로컬 실행 경로를 모두 지원하기 위해 두 경로 탐색
            fallback_paths = ["real_api_response.json", "../real_api_response.json"]
            for path in fallback_paths:
                if os.path.exists(path):
                    try:
                        with open(path, encoding='utf-8') as f:
                            json_data = json.load(f)
                            raw_data = json_data.get("data", [])
                            is_mock = True
                            print(f"성공적으로 로컬 파일({path})에서 백업 데이터를 로드했습니다.")
                            break
                    except Exception as e:
                        print(f"백업 데이터 로딩 오류 ({path}): {e}")
            if raw_data is None:
                print("경고: 로컬 백업 JSON 데이터를 찾거나 로드할 수 없습니다. 빈 데이터를 사용합니다.")
                raw_data = []
                is_mock = True
            
        df = pd.DataFrame(raw_data)
        return self.clean_dataframe(df), is_mock

    def clean_dataframe(self, df):
        """
        도서관 데이터프레임을 정제합니다:
        - 숫자형 컬럼 변환 및 결측치 처리 (도서수, 열람석수, 위도, 경도)
        - 행정구역명(SGG_NM) 정제 및 누락 구역 추출
        """
        if df.empty:
            return df

        # 필수 컬럼 존재 여부 확인 및 생성
        required_cols = ['LBRRY_NM', 'SGG_NM', 'LBRRY_TYPE', 'LCTN_ROAD_NM_ADDR', 'LAT', 'LOT', 'BOOK_CNT', 'PRSL_SEAT_CNT']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        # 숫자형 변환 및 결측치 0 처리
        df['BOOK_CNT'] = pd.to_numeric(df['BOOK_CNT'], errors='coerce').fillna(0).astype(int)
        df['PRSL_SEAT_CNT'] = pd.to_numeric(df['PRSL_SEAT_CNT'], errors='coerce').fillna(0).astype(int)
        df['LAT'] = pd.to_numeric(df['LAT'], errors='coerce')
        df['LOT'] = pd.to_numeric(df['LOT'], errors='coerce')

        # 군·구명 공백 제거
        df['SGG_NM'] = df['SGG_NM'].astype(str).str.strip()
        
        # 군·구명이 누락된 경우 도로명 주소에서 행정구역 추출 (예: '인천광역시 남동구 ...' -> '남동구')
        def extract_sgg_from_address(row):
            sgg = row['SGG_NM']
            if not sgg or sgg == 'None' or sgg == 'nan' or sgg == '':
                addr = str(row['LCTN_ROAD_NM_ADDR'])
                parts = addr.split()
                for part in parts:
                    if part.endswith('구') or part.endswith('군'):
                        return part
            return sgg

        df['SGG_NM'] = df.apply(extract_sgg_from_address, axis=1)
        df['SGG_NM'] = df['SGG_NM'].replace({'nan': '미분류', 'None': '미분류', '': '미분류'})
        
        # 도서관 유형 정보 정제
        df['LBRRY_TYPE'] = df['LBRRY_TYPE'].fillna('기타').astype(str).str.strip()
        df['LBRRY_TYPE'] = df['LBRRY_TYPE'].replace({'': '기타', 'None': '기타'})

        return df

if __name__ == "__main__":
    client = IncheonLibraryAPIClient()
    df, is_mock = client.get_library_dataframe()
    print(f"데모 모드 동작 여부: {is_mock}, 로드된 도서관 레코드 수: {len(df)}")
