# 인천광역시 도서관 정보 시각화 대시보드 📚

이 프로젝트는 **인천데이터포털**의 오픈 API를 통해 인천광역시 내의 도서관 정보를 수집하고, 이를 가독성 높은 대시보드 형태로 시각화하는 파이썬 애플리케이션입니다. 

실시간 API 데이터를 연동하여 현황을 파악할 수 있으며, API 인증키가 없는 사용자도 프로젝트를 즉시 탐색해볼 수 있도록 정밀하게 구성된 데모용 데이터(Mock Data) 자동 대체(Fallback) 기능을 기본으로 지원합니다.

---

## 🛠️ 기술 스택 (Tech Stack)

- **Language**: Python (3.10 이상 권장)
- **Data Engineering**: `pandas`
- **Visualization**: `matplotlib` (도서관 통계 차트), `folium` & `streamlit-folium` (대화형 위치 지도)
- **Dashboard Interface**: `Streamlit`
- **Security & Config**: `python-dotenv`, `requests`

---

## ✨ 주요 기능 (Key Features)

1. **실시간 데이터 동기화 및 Fallback**: 
   - 인천데이터포털 API를 활용해 최신 도서관 정보를 실시간으로 페이징 수집합니다.
   - API 키가 없거나 요청이 실패하는 경우, 사전에 구축한 가상의 인천 도서관 지리 데이터셋(Mock Data)이 활성화되어 정상 동작을 보장합니다.
2. **지리 정보 시각화 (Interactive Map)**:
   - `folium` 지도를 활용하여 인천 각 지역의 도서관 위치를 마커로 표시합니다.
   - 도서관 종류(공공도서관, 작은도서관, 어린이도서관 등)에 따라 마커 색상을 분류하여 가시성을 높였습니다.
   - 마커 클릭 시 **도서관명, 유형, 도로명 주소, 전화번호(바로 연결 가능), 소장 도서/열람석 수, 휴관일 정보, 공식 홈페이지 링크**가 포함된 카드형 팝업이 나타납니다.
3. **통계 분석 차트**:
   - **군·구별 도서관 수**: 인천의 행정구역별 도서관 인프라 분포를 비교하는 막대 그래프
   - **도서관 운영 유형 비율**: 인천 내 도서관 형태의 비율을 보여주는 도넛 차트
   - **도서 보유량 상위 10개 관**: 가장 많은 책을 보유하고 있는 대표 도서관 목록을 보여주는 가로 막대 그래프
4. **동적 데이터 필터 및 브라우저**:
   - 사이드바를 통해 군·구별, 도서관 유형별 필터를 제공하며, 필터가 적용되면 지도와 차트가 실시간으로 재계산되어 갱신됩니다.
   - 하단에 검색 가능한 상세 데이터 테이블을 배치하여 개별 도서관의 정보를 텍스트로 검색하거나 정렬할 수 있습니다.

---

## 🚀 시작하기 (Getting Started)

### 1. 저장소 클론
```bash
git clone https://github.com/hjn5018/inchoen_library_visualization.git
cd inchoen_library_visualization
```

### 2. 패키지 설치
프로젝트 루트 폴더에서 아래 명령어를 실행하여 필수 의존 라이브러리를 설치합니다.
```bash
pip install -r requirements.txt
```

### 3. API Key 설정 (선택 사항)
실시간 API 데이터를 받아오려면 다음 두 가지 방법 중 하나로 API 키를 설정하십시오. (입력하지 않으면 자동으로 데모 모드로 실행됩니다.)

#### 방법 A: `.env` 파일 설정
1. 루트 폴더의 `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.
2. [인천데이터포털](https://data.incheon.go.kr/)에 가입 후 **인천 도서관정보 API** 사용 승인을 받습니다.
3. 발급받은 인증키를 `.env` 파일에 기입합니다.
   ```env
   INCHEON_API_KEY=발급받은_오픈API_인증키
   ```

#### 방법 B: 대시보드 화면에서 직접 입력
애플리케이션을 구동한 뒤, 왼쪽 사이드바의 **"인천데이터포털 API Key 입력"** 란에 자신의 API 키를 붙여넣으면 즉시 실시간 데이터로 자동 전환됩니다.

### 4. 대시보드 구동
터미널에서 아래 명령어를 통해 Streamlit 서버를 실행합니다.
```bash
streamlit run app.py
```
명령어가 실행되면 기본 브라우저에서 `http://localhost:8501` 주소로 대시보드가 자동으로 열립니다.

---

## 📂 프로젝트 구조 (Directory Structure)

```
incheon_library_visualization/
├── .env.example       # 환경변수 템플릿 파일
├── .gitignore         # Git 추적 제외 설정 파일
├── requirements.txt   # 파이썬 의존성 패키지 목록
├── mock_data.py       # 실시간 통신 불가 시 사용되는 인천 도서관 데모 데이터 모듈
├── api_client.py      # OpenAPI 호출 및 데이터 전처리/클리닝 클래스 (객체지향 설계)
├── app.py             # Streamlit 대시보드 메인 애플리케이션
└── README.md          # 프로젝트 안내 문서
```
