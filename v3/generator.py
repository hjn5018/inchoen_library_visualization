import os
import sys
import argparse
import json
import urllib.parse
import pandas as pd

# Matplotlib 비대화형 백엔드 및 맑은 고딕 한글 폰트 설정
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import folium

# api_client 로드
from api_client import IncheonLibraryAPIClient

# 한글 폰트 설정
try:
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
    matplotlib.rcParams['axes.unicode_minus'] = False
except Exception as e:
    print(f"폰트 설정 오류: {e}")

def main():
    parser = argparse.ArgumentParser(description="인천 도서관 데이터 정적 시각화 빌더 (v3)")
    parser.add_argument("--districts", type=str, default="", help="필터링할 군·구 이름 (쉼표로 구분)")
    parser.add_argument("--types", type=str, default="", help="필터링할 도서관 유형 (쉼표로 구분)")
    args = parser.parse_args()

    # static/generated 디렉토리 생성
    script_dir = os.path.dirname(os.path.abspath(__file__))
    generated_dir = os.path.join(script_dir, "static", "generated")
    os.makedirs(generated_dir, exist_ok=True)

    # API 클라이언트 초기화
    client = IncheonLibraryAPIClient()
    df, is_latest_data = client.get_library_dataframe()

    if df.empty:
        print("경고: 가져온 도서관 데이터가 비어 있습니다. 정적 빌드를 진행할 수 없습니다.")
        sys.exit(1)

    print(f"전체 도서관 수: {len(df)}개 로드 완료 (최신 로컬 데이터 모드 여부: {is_latest_data})")

    # 군·구 필터 적용
    if args.districts:
        selected_districts = [d.strip() for d in args.districts.split(',') if d.strip()]
        if selected_districts:
            df = df[df['SGG_NM'].isin(selected_districts)]
            print(f"군·구 필터 적용: {selected_districts} (남은 레코드: {len(df)}개)")

    # 도서관 유형 필터 적용
    if args.types:
        selected_types = [t.strip() for t in args.types.split(',') if t.strip()]
        if selected_types:
            df = df[df['LBRRY_TYPE'].isin(selected_types)]
            print(f"도서관 유형 필터 적용: {selected_types} (남은 레코드: {len(df)}개)")

    if df.empty:
        print("오류: 필터링 조건에 부합하는 도서관이 없습니다.")
        sys.exit(1)

    # ----------------------------------------------------
    # 1. Folium 지도 시각화 생성
    # ----------------------------------------------------
    df_map = df.dropna(subset=['LAT', 'LOT'])
    incheon_center = [37.456, 126.705]
    if not df_map.empty:
        incheon_center = [df_map['LAT'].mean(), df_map['LOT'].mean()]

    m = folium.Map(location=incheon_center, zoom_start=11, tiles="OpenStreetMap")
    
    # 도서관 유형별 마커 색상 매핑
    type_colors = {
        "공공도서관": "blue",
        "작은도서관": "green",
        "어린이도서관": "orange",
        "기타": "gray"
    }

    for idx, row in df_map.iterrows():
        lib_type = row['LBRRY_TYPE']
        color = type_colors.get(lib_type, "cadetblue")
        
        # 지도 마커 클릭 시 보여줄 카드형 팝업 HTML 템플릿
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
        
        # 홈페이지 주소가 유효하게 등록되어 있는 경우 버튼 링크 추가
        if row['HMPG_ADDR'] and str(row['HMPG_ADDR']).lower() != 'nan':
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

    m.save(os.path.join(generated_dir, 'map.html'))
    print("지도 파일 생성 완료 (map.html)")

    # ----------------------------------------------------
    # 2. Matplotlib 차트 1: 군·구별 도서관 수 막대 차트
    # ----------------------------------------------------
    fig, ax = plt.subplots(figsize=(6, 4))
    district_counts = df['SGG_NM'].value_counts()
    colors = plt.cm.Blues(range(100, 256, int(200/max(len(district_counts), 1)) + 1))[:len(district_counts)]
    
    bars = ax.bar(district_counts.index, district_counts.values, color=colors, edgecolor='none', width=0.6)
    ax.set_ylabel("도서관 수 (개)", fontsize=9, color='#4b5563')
    ax.tick_params(colors='#4b5563', labelsize=9)
    plt.xticks(rotation=45)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, height + 0.1, f'{int(height)}', 
                ha='center', va='bottom', fontsize=8, color='#1f2937', fontweight='bold')
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#d1d5db')
    ax.spines['bottom'].set_color('#d1d5db')
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, color='#e5e7eb')
    ax.set_axisbelow(True)
    plt.tight_layout()
    
    fig.savefig(os.path.join(generated_dir, 'chart_district.png'), dpi=150)
    plt.close(fig)
    print("군·구별 도서관 수 차트 생성 완료 (chart_district.png)")

    # ----------------------------------------------------
    # 3. Matplotlib 차트 2: 도서관 유형 비율 도넛 차트
    # ----------------------------------------------------
    fig, ax = plt.subplots(figsize=(6, 4))
    type_counts = df['LBRRY_TYPE'].value_counts()
    color_palette = ['#3B82F6', '#10B981', '#F59E0B', '#6B7280', '#EC4899', '#8B5CF6']
    
    wedges, texts, autotexts = ax.pie(
        type_counts.values, 
        labels=type_counts.index, 
        autopct='%1.1f%%',
        startangle=90, 
        colors=color_palette[:len(type_counts)],
        wedgeprops=dict(width=0.4, edgecolor='w', linewidth=2),
        textprops=dict(color='#1f2937', fontsize=9)
    )
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(8)
        autotext.set_weight('bold')
        
    plt.tight_layout()
    fig.savefig(os.path.join(generated_dir, 'chart_type.png'), dpi=150)
    plt.close(fig)
    print("도서관 유형 비율 차트 생성 완료 (chart_type.png)")

    # ----------------------------------------------------
    # 4. Matplotlib 차트 3: 도서 보유량 상위 10개 관 가로 막대 차트
    # ----------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 4))
    top_books = df.nlargest(10, 'BOOK_CNT').sort_values('BOOK_CNT', ascending=True)
    y_labels = [name if len(name) <= 15 else name[:14] + '...' for name in top_books['LBRRY_NM']]
    
    bars = ax.barh(y_labels, top_books['BOOK_CNT'] / 1000, color='#6366F1', edgecolor='none', height=0.55)
    ax.set_xlabel("소장 도서 수 (천 권)", fontsize=9, color='#4b5563')
    ax.tick_params(colors='#4b5563', labelsize=9)
    
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2.0, f'{width:.1f}k ({int(width*1000):,}권)', 
                ha='left', va='center', fontsize=8, color='#1f2937', fontweight='bold')
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#d1d5db')
    ax.spines['bottom'].set_color('#d1d5db')
    ax.xaxis.grid(True, linestyle='--', alpha=0.5, color='#e5e7eb')
    ax.set_axisbelow(True)
    plt.tight_layout()
    
    fig.savefig(os.path.join(generated_dir, 'chart_top_books.png'), dpi=150)
    plt.close(fig)
    print("도서 보유량 상위 10개 관 차트 생성 완료 (chart_top_books.png)")

    # ----------------------------------------------------
    # 5. Frontend 연동용 JavaScript 데이터 파일 생성 (CORS 방지)
    # ----------------------------------------------------
    records = df.to_dict(orient='records')
    js_content = f"""// 자동 생성된 최신 도서관 데이터 파일입니다.
const LATEST_LIBRARY_DATA = {json.dumps(records, ensure_ascii=False, indent=2)};
const IS_LATEST_DATA_MODE = {"true" if is_latest_data else "false"};
"""
    
    js_path = os.path.join(generated_dir, 'libraries.js')
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"JavaScript 데이터 에셋 빌드 완료 (libraries.js -> {len(records)}개 레코드)")
    print("정적 시각화 빌드 완료!")

if __name__ == "__main__":
    main()
