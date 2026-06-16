// 글로벌 변수로 도서관 데이터셋 저장 (libraries.js에서 선언된 LATEST_LIBRARY_DATA 참조)
let allLibraries = [];
let filteredLibraries = [];

document.addEventListener("DOMContentLoaded", () => {
    // 최초 실행 시 도서관 기초 데이터 바인딩 및 화면 초기화
    initDashboard();

    // 필터 적용 버튼 이벤트 리스너 등록
    document.getElementById("applyBtn").addEventListener("click", () => {
        applyFilters();
    });

    // 테이블 실시간 검색 리스너 등록
    document.getElementById("tableSearch").addEventListener("input", (e) => {
        handleTableSearch(e.target.value);
    });
});

/**
 * 대시보드를 최초로 로드하고 체크박스 필터 옵션을 동적으로 생성합니다.
 */
function initDashboard() {
    const statusAlert = document.getElementById("statusAlert");

    // libraries.js가 정상 로드되었는지 검증
    if (typeof LATEST_LIBRARY_DATA !== 'undefined' && Array.isArray(LATEST_LIBRARY_DATA)) {
        allLibraries = LATEST_LIBRARY_DATA;
        filteredLibraries = [...allLibraries];

        // 데이터 상태 메시지 업데이트 (latest data 용어 사용)
        if (typeof IS_LATEST_DATA_MODE !== 'undefined' && IS_LATEST_DATA_MODE) {
            statusAlert.className = "alert-box alert-info";
            statusAlert.innerHTML = "🟡 **최신 데이터 모드 (latest data)**: API 인증키가 설정되지 않아 로컬 저장된 최신 데이터를 사용 중입니다. 실시간 데이터를 연동하려면 프로젝트 내 .env 파일에 API 인증키를 입력하고 generator.py를 실행하세요.";
        } else {
            statusAlert.className = "alert-box alert-success";
            statusAlert.innerHTML = "🟢 **실시간 데이터 모드**: Open API를 통해 수집된 실시간 데이터를 사용 중입니다.";
        }

        // 군·구명 및 도서관 유형 분류 체크박스 목록을 동적으로 구성
        populateFilters(allLibraries);

        // 기본 필터를 적용해 KPI 및 테이블 렌더링
        applyFilters(true);
    } else {
        statusAlert.className = "alert-box alert-danger";
        statusAlert.innerText = "❌ 데이터 연동 실패: generated/libraries.js 파일을 찾을 수 없거나 데이터 형식이 잘못되었습니다. generator.py를 먼저 실행해 주세요.";
    }
}

/**
 * 수집한 도서관 데이터셋으로부터 고유 군·구 및 도서관 유형을 추출하여 사이드바 체크박스를 구성합니다.
 */
function populateFilters(data) {
    const districts = [...new Set(data.map(item => item.SGG_NM))].sort();
    const types = [...new Set(data.map(item => item.LBRRY_TYPE))].sort();

    // 1. 군·구 체크박스 생성
    const districtContainer = document.getElementById("districtFilters");
    districtContainer.innerHTML = "";
    districts.forEach(dist => {
        if (!dist || dist === 'undefined') return;
        districtContainer.appendChild(createCheckboxItem(dist, "district"));
    });

    // 2. 도서관 유형 체크박스 생성
    const typeContainer = document.getElementById("typeFilters");
    typeContainer.innerHTML = "";
    types.forEach(t => {
        if (!t || t === 'undefined') return;
        typeContainer.appendChild(createCheckboxItem(t, "type"));
    });
}

/**
 * 개별 체크박스 아이템 HTML 구조를 생성합니다.
 */
function createCheckboxItem(value, groupName) {
    const label = document.createElement("label");
    label.className = "checkbox-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = value;
    checkbox.checked = true; // 최초 상태는 전체 선택
    checkbox.dataset.group = groupName;

    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(" " + value));
    return label;
}

/**
 * 체크박스 일괄 선택 및 해제를 지원합니다.
 */
function toggleAllCheckboxes(containerId, isChecked) {
    const container = document.getElementById(containerId);
    const checkboxes = container.querySelectorAll("input[type='checkbox']");
    checkboxes.forEach(cb => {
        cb.checked = isChecked;
    });
}

/**
 * 선택된 필터를 기반으로 클라이언트 단의 통계 지표 및 테이블을 즉시 동기화합니다.
 */
function applyFilters(isInitial = false) {
    // 체크박스로부터 선택된 항목 수집
    const checkedDistricts = Array.from(document.querySelectorAll("input[data-group='district']:checked")).map(cb => cb.value);
    const checkedTypes = Array.from(document.querySelectorAll("input[data-group='type']:checked")).map(cb => cb.value);

    if (checkedDistricts.length === 0 || checkedTypes.length === 0) {
        alert("⚠️ 최소 하나의 군·구와 도서관 유형을 선택해야 대시보드를 생성할 수 있습니다.");
        return;
    }

    // 로컬 메모리에 있는 도서관 배열 필터링
    filteredLibraries = allLibraries.filter(item => 
        checkedDistricts.includes(item.SGG_NM) && checkedTypes.includes(item.LBRRY_TYPE)
    );

    // 1. KPI 통계 카드 화면 연산 및 동기화
    const totalRecords = filteredLibraries.length;
    const totalBooks = filteredLibraries.reduce((sum, item) => sum + Number(item.BOOK_CNT || 0), 0);
    const totalSeats = filteredLibraries.reduce((sum, item) => sum + Number(item.PRSL_SEAT_CNT || 0), 0);

    let largestName = "N/A";
    let largestBooks = 0;
    if (totalRecords > 0) {
        const largestLib = filteredLibraries.reduce((max, item) => 
            Number(item.BOOK_CNT || 0) > Number(max.BOOK_CNT || 0) ? item : max
        , filteredLibraries[0]);
        largestName = largestLib.LBRRY_NM;
        largestBooks = Number(largestLib.BOOK_CNT || 0);
    }

    document.getElementById("kpiTotalLibraries").innerText = totalRecords.toLocaleString() + " 개소";
    document.getElementById("kpiTotalBooks").innerText = totalBooks.toLocaleString() + " 권";
    document.getElementById("kpiTotalSeats").innerText = totalSeats.toLocaleString() + " 석";
    
    // 최대 도서관 명칭이 길면 축소 처리
    let displayLargestName = largestName;
    if (displayLargestName.length > 12) {
        displayLargestName = displayLargestName.substring(0, 11) + "...";
    }
    document.getElementById("kpiLargestLibrary").innerText = displayLargestName;
    document.getElementById("kpiLargestLibraryBooks").innerText = largestBooks.toLocaleString() + "권 보유";

    // 2. 캐시를 피하기 위해 타임스탬프를 부여하여 정적 리소스 로드
    // (사용자가 CLI에서 generator.py를 다시 작동시켰을 때 즉각 갱신용)
    if (isInitial) {
        const timestamp = Date.now();
        document.getElementById("mapIframe").src = `generated/map.html?t=${timestamp}`;
        document.getElementById("districtChart").src = `generated/chart_district.png?t=${timestamp}`;
        document.getElementById("typeChart").src = `generated/chart_type.png?t=${timestamp}`;
        document.getElementById("topBooksChart").src = `generated/chart_top_books.png?t=${timestamp}`;
    }

    // 3. 테이블 다시 그리기
    const searchVal = document.getElementById("tableSearch").value;
    if (searchVal) {
        handleTableSearch(searchVal);
    } else {
        renderLibraryTable(filteredLibraries);
    }
}

/**
 * 필터링이 반영된 도서관 목록을 테이블 HTML로 렌더링합니다.
 */
function renderLibraryTable(data) {
    const tableBody = document.getElementById("libraryTableBody");
    tableBody.innerHTML = "";

    if (data.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #94a3b8;">검색 및 필터 조건에 부합하는 도서관이 존재하지 않습니다.</td></tr>`;
        document.getElementById("recordCountText").innerText = "조회된 레코드가 없습니다.";
        return;
    }

    data.forEach(item => {
        const row = document.createElement("tr");

        // 소장도서수 및 열람좌석수 쉼표 포맷팅
        const bookCountFormatted = Number(item.BOOK_CNT).toLocaleString();
        const seatCountFormatted = Number(item.PRSL_SEAT_CNT).toLocaleString();

        row.innerHTML = `
            <td style="font-weight: 700; color: #1e3a8a;">${item.LBRRY_NM}</td>
            <td><span style="background-color: #f1f5f9; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600;">${item.LBRRY_TYPE}</span></td>
            <td>${item.SGG_NM}</td>
            <td style="text-align: right; font-weight: 500;">${bookCountFormatted}권</td>
            <td style="text-align: right; font-weight: 500;">${seatCountFormatted}석</td>
            <td style="font-size: 11px;">${item.LCTN_ROAD_NM_ADDR}</td>
            <td>${item.LBRRY_TELNO || '-'}</td>
            <td style="color: #ef4444; font-size: 11px;">${item.CLSDY_GUID || '-'}</td>
        `;

        tableBody.appendChild(row);
    });

    document.getElementById("recordCountText").innerText = `총 ${data.length}개의 도서관 레코드가 조회되었습니다.`;
}

/**
 * 테이블 내 도서관명 또는 주소 키워드를 실시간으로 검색하여 렌더링합니다.
 */
function handleTableSearch(keyword) {
    const query = keyword.toLowerCase().trim();
    if (!query) {
        renderLibraryTable(filteredLibraries);
        return;
    }

    const searchResults = filteredLibraries.filter(item => 
        (item.LBRRY_NM && item.LBRRY_NM.toLowerCase().includes(query)) ||
        (item.LCTN_ROAD_NM_ADDR && item.LCTN_ROAD_NM_ADDR.toLowerCase().includes(query))
    );

    renderLibraryTable(searchResults);
}
