import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import folium
from streamlit_folium import st_folium
import os

from api_client import IncheonLibraryAPIClient

# Configure Matplotlib for Korean fonts on Windows
try:
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
    matplotlib.rcParams['axes.unicode_minus'] = False
except Exception as e:
    print(f"Font configuration error: {e}")

# Page config
st.set_page_config(
    page_title="인천광역시 도서관 현황 대시보드",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS styling (glassmorphism, clean fonts, card styling)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', 'Outfit', sans-serif;
    }
    
    /* Title styling */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        padding-bottom: 0.5rem;
    }
    .subtitle {
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Custom metric card */
    .metric-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(229, 231, 235, 0.8);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 1rem;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        color: #4B5563;
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        color: #111827;
        font-size: 1.875rem;
        font-weight: 700;
        line-height: 1;
    }
    .metric-sub {
        color: #9CA3AF;
        font-size: 0.75rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 사이드바 영역
# ----------------------------------------------------
st.sidebar.markdown("### ⚙️ 설정 및 필터")


@st.cache_data(show_spinner="인천 도서관 데이터를 불러오는 중...")
def load_data():
    """API 클라이언트를 통해 도서관 데이터를 불러와 캐싱합니다."""
    client = IncheonLibraryAPIClient()
    df, is_mock = client.get_library_dataframe()
    return df, is_mock

# 환경 변수에 기반하여 데이터를 로드합니다.
df, is_mock = load_data()

# 데이터 소스 상태 메시지 출력
if is_mock:
    st.info("🟡 **데모 모드**: API 인증키가 설정되지 않아 로컬 백업 데이터(JSON)를 표시하고 있습니다. 실시간 데이터를 연동하려면 프로젝트 내 .env 파일에 API 인증키를 입력해주세요.")
else:
    st.success("🟢 **실시간 모드**: 인천데이터포털의 OpenAPI 실시간 데이터를 수신하여 표시하고 있습니다.")

# Sidebar Filters
st.sidebar.markdown("---")
st.sidebar.markdown("#### 🔍 필터링")

# District Filter
all_districts = sorted(df['SGG_NM'].unique())
selected_districts = st.sidebar.multiselect(
    "군·구 선택",
    options=all_districts,
    default=all_districts,
    help="특정 군·구의 도서관만 필터링합니다."
)

# Library Type Filter
all_types = sorted(df['LBRRY_TYPE'].unique())
selected_types = st.sidebar.multiselect(
    "도서관 유형",
    options=all_types,
    default=all_types,
    help="도서관 운영 유형별로 필터링합니다."
)

# Apply filters
df_filtered = df[df['SGG_NM'].isin(selected_districts) & df['LBRRY_TYPE'].isin(selected_types)]

# ----------------------------------------------------
# Main Dashboard Header
# ----------------------------------------------------
st.markdown('<div class="main-title">인천광역시 도서관 현황 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">인천데이터포털 Open API를 기반으로 시각화한 도서관 데이터 분석 대시보드입니다.</div>', unsafe_allow_html=True)

if df_filtered.empty:
    st.warning("⚠️ 선택한 조건에 부합하는 도서관 데이터가 없습니다. 필터를 조정해주세요.")
else:
    # ----------------------------------------------------
    # KPI Cards Section
    # ----------------------------------------------------
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">총 도서관 수</div>
            <div class="metric-value">{len(df_filtered):,} 개소</div>
            <div class="metric-sub">선택된 지역/유형 도서관 수</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col2:
        total_books = df_filtered['BOOK_CNT'].sum()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">총 소장 도서 수</div>
            <div class="metric-value">{total_books:,} 권</div>
            <div class="metric-sub">누적 도서 보유량</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col3:
        total_seats = df_filtered['PRSL_SEAT_CNT'].sum()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">총 열람 좌석 수</div>
            <div class="metric-value">{total_seats:,} 석</div>
            <div class="metric-sub">누적 독서/열람 공간</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col4:
        if not df_filtered.empty:
            largest_lib = df_filtered.loc[df_filtered['BOOK_CNT'].idxmax()]
            largest_name = largest_lib['LBRRY_NM']
            largest_books = largest_lib['BOOK_CNT']
            # Limit name length for UI neatness
            if len(largest_name) > 12:
                largest_name = largest_name[:11] + "..."
        else:
            largest_name = "N/A"
            largest_books = 0
            
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">최대 도서 보유관</div>
            <div class="metric-value">{largest_name}</div>
            <div class="metric-sub">{largest_books:,} 권 보유</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("###")

    # ----------------------------------------------------
    # Map & Details Section
    # ----------------------------------------------------
    map_col, info_col = st.columns([3, 2])
    
    with map_col:
        st.markdown("#### 📍 도서관 위치 분포 지도")
        
        # Filter libraries with valid lat/lot for drawing the map
        df_map = df_filtered.dropna(subset=['LAT', 'LOT'])
        
        # Center map around Incheon coordinates
        incheon_center = [37.456, 126.705]
        if not df_map.empty:
            incheon_center = [df_map['LAT'].mean(), df_map['LOT'].mean()]
            
        m = folium.Map(location=incheon_center, zoom_start=11, tiles="OpenStreetMap")
        
        # Colors mapping for library types
        type_colors = {
            "공공도서관": "blue",
            "작은도서관": "green",
            "어린이도서관": "orange",
            "기타": "gray"
        }
        
        # Add markers
        for idx, row in df_map.iterrows():
            lib_type = row['LBRRY_TYPE']
            color = type_colors.get(lib_type, "cadetblue")
            
            # HTML styled Popup for rich details
            popup_html = f"""
            <div style="font-family: 'Malgun Gothic', 'Helvetica Neue', Arial; width: 260px; font-size: 13px;">
                <h4 style="margin: 0 0 5px 0; color: #1e3a8a; font-weight: bold;">{row['LBRRY_NM']}</h4>
                <span style="background-color: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600;">{lib_type}</span>
                <hr style="margin: 8px 0; border: 0; border-top: 1px solid #e5e7eb;"/>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="color: #6b7280; padding: 2px 0; vertical-align: top; width: 60px;">주소:</td>
                        <td style="color: #1f2937; padding: 2px 0;">{row['LCTN_ROAD_NM_ADDR']}</td>
                    </tr>
                    <tr>
                        <td style="color: #6b7280; padding: 2px 0;">전화번호:</td>
                        <td style="color: #1f2937; padding: 2px 0;"><a href="tel:{row['LBRRY_TELNO']}" style="color: #2563eb; text-decoration: none;">{row['LBRRY_TELNO']}</a></td>
                    </tr>
                    <tr>
                        <td style="color: #6b7280; padding: 2px 0;">도서/좌석:</td>
                        <td style="color: #1f2937; padding: 2px 0;">{row['BOOK_CNT']:,}권 / {row['PRSL_SEAT_CNT']:,}석</td>
                    </tr>
                    <tr>
                        <td style="color: #6b7280; padding: 2px 0; vertical-align: top;">휴관일:</td>
                        <td style="color: #ef4444; padding: 2px 0; font-size: 11px;">{row['CLSDY_GUID']}</td>
                    </tr>
                </table>
            """
            
            if row['HMPG_ADDR'] and str(row['HMPG_ADDR']).lower() != 'nan':
                # Clean URL (ensure starts with http)
                url = str(row['HMPG_ADDR']).strip()
                if not url.startswith('http'):
                    url = 'http://' + url
                popup_html += f"""
                <div style="margin-top: 10px; text-align: right;">
                    <a href="{url}" target="_blank" style="background-color: #2563eb; color: white; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">홈페이지 방문</a>
                </div>
                """
            popup_html += "</div>"
            
            folium.Marker(
                location=[row['LAT'], row['LOT']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=row['LBRRY_NM'],
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(m)
            
        # Draw map in Streamlit
        st_folium(m, width="100%", height=500, returned_objects=[])

    with info_col:
        st.markdown("#### 📊 도서관 현황 비교 요약")
        
        # Summary statistics by District (SGG_NM)
        dist_stats = df_filtered.groupby('SGG_NM').agg(
            도서관수=('LBRRY_NM', 'count'),
            총도서수=('BOOK_CNT', 'sum')
        ).sort_values(by='도서관수', ascending=False)
        
        # Display styled comparison dataframe
        st.dataframe(
            dist_stats.style.background_gradient(cmap='Blues', subset=['도서관수', '총도서수'])
                      .format({'총도서수': '{:,}'}),
            use_container_width=True,
            height=200
        )
        
        # Display operational hours info snippet
        st.markdown("💡 **도서관 이용 안내**")
        st.info("대부분의 공공도서관은 **평일 09:00 ~ 22:00**까지 종합자료실을 운영하고 있습니다. 주말(토, 일)에는 단축 운영되거나 휴관하는 경우가 많으며, 세부 휴관 정보는 지도의 마커를 클릭하여 확인할 수 있습니다.")

    st.markdown("---")

    # ----------------------------------------------------
    # Charts Section
    # ----------------------------------------------------
    st.markdown("#### 📈 데이터 시각화 분석")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Chart 1: Number of libraries by district
        st.markdown("##### 군·구별 도서관 수")
        fig, ax = plt.subplots(figsize=(6, 4))
        
        district_counts = df_filtered['SGG_NM'].value_counts()
        colors = plt.cm.Blues(range(100, 256, int(156/len(district_counts)) + 1))[:len(district_counts)]
        
        bars = ax.bar(district_counts.index, district_counts.values, color=colors, edgecolor='none', width=0.6)
        
        # Customize ticks and labels
        ax.set_ylabel("도서관 수 (개)", fontsize=9, color='#4b5563')
        ax.tick_params(colors='#4b5563', labelsize=9)
        plt.xticks(rotation=45)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, height + 0.1, f'{int(height)}', 
                    ha='center', va='bottom', fontsize=8, color='#1f2937', fontweight='bold')
            
        # Clean spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#d1d5db')
        ax.spines['bottom'].set_color('#d1d5db')
        
        # Light gridlines
        ax.yaxis.grid(True, linestyle='--', alpha=0.5, color='#e5e7eb')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        st.pyplot(fig)
        
    with chart_col2:
        # Chart 2: Library Type Distribution (Donut Chart)
        st.markdown("##### 도서관 운영 유형 비율")
        fig, ax = plt.subplots(figsize=(6, 4))
        
        type_counts = df_filtered['LBRRY_TYPE'].value_counts()
        color_palette = ['#3B82F6', '#10B981', '#F59E0B', '#6B7280', '#EC4899', '#8B5CF6']
        
        # Wedge styling
        wedges, texts, autotexts = ax.pie(
            type_counts.values, 
            labels=type_counts.index, 
            autopct='%1.1f%%',
            startangle=90, 
            colors=color_palette[:len(type_counts)],
            wedgeprops=dict(width=0.4, edgecolor='w', linewidth=2),
            textprops=dict(color='#1f2937', fontsize=9)
        )
        
        # Clean autotexts styling
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(8)
            autotext.set_weight('bold')
            
        plt.tight_layout()
        st.pyplot(fig)

    st.markdown("###")
    
    # Chart 3: Top 10 libraries by book count
    st.markdown("##### 도서 보유량 상위 10개 도서관")
    fig, ax = plt.subplots(figsize=(12, 4.5))
    
    top_books = df_filtered.nlargest(10, 'BOOK_CNT').sort_values('BOOK_CNT', ascending=True)
    
    # Format library names for bar chart labels to avoid overlap
    y_labels = [name if len(name) <= 15 else name[:14] + '...' for name in top_books['LBRRY_NM']]
    
    bars = ax.barh(y_labels, top_books['BOOK_CNT'] / 1000, color='#6366F1', edgecolor='none', height=0.55)
    
    # Customize labels and ticks
    ax.set_xlabel("소장 도서 수 (천 권)", fontsize=9, color='#4b5563')
    ax.tick_params(colors='#4b5563', labelsize=9)
    
    # Add value labels inside/next to horizontal bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 2, bar.get_y() + bar.get_height()/2.0, f'{width:.1f}k ({int(width*1000):,}권)', 
                ha='left', va='center', fontsize=8, color='#1f2937', fontweight='bold')
        
    # Clean spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#d1d5db')
    ax.spines['bottom'].set_color('#d1d5db')
    
    # Light gridlines
    ax.xaxis.grid(True, linestyle='--', alpha=0.5, color='#e5e7eb')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("---")

    # ----------------------------------------------------
    # Data Table Section
    # ----------------------------------------------------
    st.markdown("#### 📂 인천 도서관 상세 데이터 브라우저")
    
    # Select columns to display
    display_cols = [
        "LBRRY_NM", "LBRRY_TYPE", "SGG_NM", "BOOK_CNT", 
        "PRSL_SEAT_CNT", "LCTN_ROAD_NM_ADDR", "LBRRY_TELNO", "CLSDY_GUID"
    ]
    
    df_display = df_filtered[display_cols].rename(columns={
        "LBRRY_NM": "도서관명",
        "LBRRY_TYPE": "유형",
        "SGG_NM": "군·구",
        "BOOK_CNT": "소장도서수",
        "PRSL_SEAT_CNT": "열람좌석수",
        "LCTN_ROAD_NM_ADDR": "소재지 도로명주소",
        "LBRRY_TELNO": "전화번호",
        "CLSDY_GUID": "휴관일 안내"
    })
    
    # Search input for libraries
    search_query = st.text_input("📝 도서관 이름 또는 주소 검색", "", help="도서관 이름 또는 주소를 입력하여 실시간 검색합니다.")
    if search_query:
        df_display = df_display[
            df_display['도서관명'].str.contains(search_query, case=False, na=False) |
            df_display['소재지 도로명주소'].str.contains(search_query, case=False, na=False)
        ]

    st.dataframe(
        df_display.style.format({'소장도서수': '{:,}', '열람좌석수': '{:,}'}),
        use_container_width=True,
        height=300
    )
    
    st.markdown(f"총 **{len(df_display)}**개의 도서관 레코드가 로드되었습니다.")
