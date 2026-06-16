# 인천광역시 도서관 정보 시각화 대시보드 📚

이 프로젝트는 **인천데이터포털**의 오픈 API를 통해 인천광역시 내의 도서관 정보를 실시간 수집하고, 이를 세련되고 가독성 높은 모던 대시보드 형태로 시각화하는 웹 애플리케이션입니다.

**Streamlit 프레임워크를 걷어내고**, 순수 HTML, CSS, JavaScript 프론트엔드와 Flask 백엔드(`pandas`, `matplotlib`, `folium` 연동) 조합의 모던 웹 아키텍처로 통일하여 구성했습니다.

API 인증키가 없거나 유효하지 않은 경우에도 대시보드가 정상 기동하도록 실제 API 응답 데이터 수집본(`real_api_response.json`)을 활용한 자동 데이터 폴백(Fallback) 기능을 완비하고 있습니다.

---

## 🛠️ 기술 스택 (Tech Stack)

### 1. 프론트엔드 (Frontend)
- **HTML5 / Vanilla CSS**: 모던 글래스모피즘(카드 블러 효과) 및 커스텀 HSL 색상계를 적용한 반응형 디자인
- **Vanilla JavaScript**: Flask 백엔드와의 비동기 API 호출, 동적 행정구역/유형 필터 적용, 데이터 캐시 방징용 강제 리로드(Cache-Busting) 제어 및 한글 초성/완성형 실시간 검색 테이블 브라우징

### 2. 백엔드 (Backend)
- **Flask**: 웹 서비스 자원 및 API 엔드포인트 서빙
- **pandas**: 데이터 정제(Data Cleaning), 결측치 처리 및 다차원 데이터 필터링
- **Matplotlib**: 웹 스레드에 안전한 `Agg` 비대화형 백엔드를 통해 차트 이미지(막대 그래프, 도넛 차트 등) 동적 렌더링 (맑은 고딕 한글 폰트 적용)
- **folium**: 카르토그래픽 위치 정보 렌더링 및 클릭형 상세 마커 팝업 퍼블리싱

---

## 🚀 시작하기 (How to Run)

### 1. 저장소 클론 및 가상환경 생성
터미널(또는 PowerShell)에서 아래 명령어를 실행하여 저장소를 다운로드하고 전용 파이썬 가상환경을 활성화합니다.
```bash
git clone https://github.com/hjn5018/inchoen_library_visualization.git
cd inchoen_library_visualization

# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
# PowerShell:
.\venv\Scripts\Activate.ps1
# CMD:
.\venv\Scripts\activate.bat
```

### 2. 의존성 패키지 설치
가상환경이 활성화된 상태에서 아래 명령어를 실행합니다.
```bash
pip install -r requirements.txt
```

### 3. API Key 설정 (선택 사항)
실시간 데이터 동기를 원하실 경우:
1. 루트 경로에 `.env` 파일을 새로 생성합니다.
2. 아래 형식에 본인의 API 키를 입력합니다.
   ```env
   INCHEON_API_KEY=발급받은_인천데이터포털_오픈API_인증키
   ```
*(인증키가 기입되지 않았을 경우, 자동으로 데모 모드로 실행되어 `real_api_response.json` 파일의 65개 인천 도서관 데이터를 안전하게 로딩합니다.)*

### 4. 대시보드 서버 구동
가상환경 콘솔창에서 아래 명령어로 Flask 서버를 실행합니다.
```bash
python server.py
```

서버 가동 후 웹 브라우저를 열고 아래 로컬 호스트 주소로 접속합니다.
- **대시보드 접속 주소**: [http://localhost:5000](http://localhost:5000)

---

## 📂 프로젝트 구조 (Directory Structure)

```
incheon_library_visualization/
├── venv/                    # 파이썬 가상환경 폴더 (사용자 직접 빌드)
├── real_api_response.json   # 실제 인천 도서관 API 응답 수집본 (Fallback 데이터 백업)
├── requirements.txt         # 파이썬 의존성 패키지 목록 (Flask, pandas 등)
├── api_client.py            # 오픈 API 페이징 호출 및 데이터 정제 클래스 (객체지향 설계)
├── server.py                # Flask 웹서버 구동 파일 (API 핸들러 및 시각화 파일 실시간 렌더링)
├── .gitignore               # Git 파일 제외 설정 (.env 및 동적 생성 파일 차단)
├── README.md                # 프로젝트 통합 가이드 설명서 (본 파일)
└── static/                  # 프론트엔드 정적 리소스 보관 폴더
    ├── index.html           # 대시보드 화면 뼈대 정의
    ├── style.css            # 모던 HSL 색상 적용 대시보드 CSS 스타일시트
    ├── app.js               # 비동기 필터 갱신 및 테이블 검색 자바스크립트
    └── generated/           # 백엔드에 의해 실시간 생성되는 시각화 에셋 저장소 (Git 제외)
        ├── map.html         # 동적으로 생성되는 folium 지도 웹페이지
        └── chart_*.png      # 동적으로 빌드되는 matplotlib 통계 차트 이미지들
```
