# 인천광역시 도서관 정보 시각화 대시보드 프로젝트 📚

이 프로젝트는 **인천데이터포털**의 오픈 API를 통해 인천광역시 내의 도서관 정보를 수집하고 시각화하는 다중 버전 대시보드 프로젝트입니다. 

기존의 **Streamlit 기반 버전(v1)**과 새롭게 개발된 **순수 HTML, CSS, JavaScript 및 Flask 연동 버전(v2)**을 모두 제공하며, 두 버전 모두 개별 파이썬 가상환경(Virtual Environment)을 사용하여 격리된 구동을 지원합니다.

API 인증키가 없는 사용자도 프로젝트를 즉시 구동할 수 있도록 실제 API의 응답을 수집해놓은 로컬 백업 파일 `real_api_response.json` 기반의 자동 대체(Fallback) 메커니즘이 탑재되어 있습니다.

---

## 🛠️ 버전별 아키텍처 및 스택 (Architecture)

### 1. 버전 1 (v1) - Streamlit 대시보드
- **특징**: 파이썬 코드로 프론트엔드 UI와 통계 로직을 빠르게 구현한 대시보드입니다.
- **기술 스택**: `Python`, `Streamlit`, `streamlit-folium`, `folium`, `pandas`, `matplotlib`, `python-dotenv`

### 2. 버전 2 (v2) - HTML/CSS/JS 및 Flask 대시보드 (추천)
- **특징**: Streamlit을 사용하지 않고 직접 설계한 세련된 모던 웹 프론트엔드(HTML/CSS/JS)와 파이썬 데이터 백엔드(Flask)가 결합된 아키텍처입니다.
- **기술 스택**: 
  - **프론트엔드**: HTML5, Vanilla CSS (모던 글래스모피즘 및 HSL 색상계 적용), Vanilla JavaScript (API 비동기 호출, 동적 필터 제어, 실시간 클라이언트 테이블 검색)
  - **백엔드**: `Flask` (웹 서버 및 API 엔드포인트 제공), `pandas` (데이터 가공 및 필터링), `matplotlib` (`Agg` 스레드 안전 비대화형 백엔드를 통한 통계 차트 동적 렌더링), `folium` (대화형 지도 생성 및 팝업 카드 퍼블리싱), `python-dotenv`

---

## 🚀 시작하기 (How to Run)

### 공통 전제조건
저장소를 클론한 후 프로젝트 루트 폴더에 위치합니다.
```bash
git clone https://github.com/hjn5018/inchoen_library_visualization.git
cd inchoen_library_visualization
```

---

### 📂 [v1] Streamlit 버전 구동하기

1. **v1 폴더로 이동**:
   ```bash
   cd v1
   ```

2. **가상환경 생성 및 활성화** (Windows 기준):
   ```bash
   python -m venv venv
   # PowerShell 사용 시:
   .\venv\Scripts\Activate.ps1
   # 기본 CMD 사용 시:
   .\venv\Scripts\activate.bat
   ```

3. **의존성 패키지 설치**:
   ```bash
   pip install -r requirements.txt
   ```

4. **API 키 설정 (선택)**:
   - `v1/.env.example` 파일을 복사하여 `v1/.env` 파일을 만들고 본인의 API 키를 입력합니다.
   - 키를 입력하지 않거나 비어있는 경우 루트 폴더의 `real_api_response.json` 백업 데이터를 사용하여 실행됩니다.

5. **대시보드 구동**:
   ```bash
   python -m streamlit run app.py
   ```
   브라우저가 자동으로 실행되며 `http://localhost:8501`에서 대시보드가 구동됩니다.

---

### 📂 [v2] HTML/CSS/JS + Flask 버전 구동하기

1. **v2 폴더로 이동** (루트 폴더 기준):
   ```bash
   cd v2
   ```

2. **가상환경 생성 및 활성화** (Windows 기준):
   ```bash
   python -m venv venv
   # PowerShell 사용 시:
   .\venv\Scripts\Activate.ps1
   # 기본 CMD 사용 시:
   .\venv\Scripts\activate.bat
   ```

3. **의존성 패키지 설치**:
   ```bash
   pip install -r requirements.txt
   ```

4. **API 키 설정 (선택)**:
   - `v2/` 폴더 내에 `.env` 파일을 생성하고 아래 형식을 입력합니다. (혹은 실행 후 웹 화면 왼쪽 사이드바에서 키를 직접 입력할 수도 있습니다.)
     ```env
     INCHEON_API_KEY=본인의_API_키
     ```

5. **Flask 웹 서버 구동**:
   ```bash
   python server.py
   ```
   서버가 정상 구동되면 웹 브라우저에서 아래 주소로 접속합니다.
   **접속 주소**: `http://localhost:5000`

---

## 📂 프로젝트 구조 (Directory Structure)

```
incheon_library_visualization/
├── real_api_response.json   # 실제 도서관 API 응답 수집본 (Fallback 백업 파일)
├── .gitignore               # Git 추적 제외 설정 파일 (generated 폴더 및 env 차단)
├── README.md                # 프로젝트 통합 가이드 (본 문서)
│
├── v1/                      # 버전 1: Streamlit 구현체 폴더
│   ├── venv/                # v1 전용 파이썬 가상환경
│   ├── .env.example         # v1 환경변수 템플릿
│   ├── requirements.txt     # v1 의존성 라이브러리 목록
│   ├── api_client.py        # v1 도서관 API 수집 및 백업 파일 로딩 모듈
│   └── app.py               # v1 Streamlit 대시보드 구동 코드
│
└── v2/                      # 버전 2: HTML/CSS/JS + Flask 구현체 폴더
    ├── venv/                # v2 전용 파이썬 가상환경
    ├── requirements.txt     # v2 의존성 라이브러리 목록 (Flask, pandas 등)
    ├── api_client.py        # v2 도서관 API 수집 및 백업 파일 로딩 모듈
    ├── server.py            # v2 Flask 백엔드 서버 (시각화 파일 생성 및 데이터 API 공급)
    └── static/              # v2 프론트엔드 정적 웹 리소스 폴더
        ├── index.html       # 대시보드 레이아웃 구조 정의
        ├── style.css        # 대시보드 글래스모피즘 CSS 스타일시트
        ├── app.js           # 동적 필터 제어, 비동기 호출 및 검색 자바스크립트
        └── generated/       # 백엔드가 동적 생성하는 시각화 파일 저장소 (.gitignore 적용)
            ├── map.html     # folium 기반 동적 생성 위치 지도
            └── chart_*.png  # matplotlib 기반 동적 생성 통계 차트 이미지들
```
