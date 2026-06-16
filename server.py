import os
import urllib.parse
from flask import Flask, request, jsonify
import pandas as pd
import json

# 웹 서버 스레드 안전성과 메모리 누수 방지를 위한 Matplotlib 비대화형(non-interactive) 백엔드 설정
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import folium
from api_client import IncheonLibraryAPIClient

# 윈도우 환경에서 Matplotlib 차트의 한글 깨짐 방지를 위한 맑은 고딕 폰트 설정
try:
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
    matplotlib.rcParams['axes.unicode_minus'] = False
except Exception as e:
    print(f"폰트 설정 오류: {e}")

app = Flask(__name__, static_folder='static', static_url_path='')

# 정적 이미지 및 지도 생성 파일을 저장할 디렉토리 생성
GENERATED_DIR = os.path.join(app.static_folder, 'generated')
os.makedirs(GENERATED_DIR, exist_ok=True)

# API 클라이언트 초기화
client = IncheonLibraryAPIClient()

@app.route('/')
def index():
    """대시보드 메인 페이지를 제공합니다."""
    return app.send_static_file('index.html')

@app.route('/api/libraries', methods=['GET'])
def get_libraries():
    """정제된 도서관 데이터 전체를 JSON 형식으로 반환합니다."""
    try:
        df, is_mock = client.get_library_dataframe()
        records = df.to_dict(orient='records')
        return jsonify({
            "status": "success",
            "is_mock": is_mock,
            "data": records
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/generate_visuals', methods=['GET'])
def generate_visuals():
    """
    필터 쿼리(군·구, 도서관 유형)를 수신하여 데이터프레임을 필터링하고,
    folium 대화형 지도와 matplotlib 통계 차트를 서버 측에서 동적으로 생성하여 저장합니다.
    최종적으로 4가지 핵심 통계 지표(KPI)를 JSON으로 응답합니다.
    """
    try:
        districts_param = request.args.get('districts', '')
        types_param = request.args.get('types', '')

        # 설정파일(.env) 및 환경변수의 API 키를 사용하는 기본 클라이언트를 사용하여 데이터프레임을 로드합니다.
        df, is_mock = client.get_library_dataframe()

        if df.empty:
            return jsonify({
                "status": "success",
                "is_mock": is_mock,
                "total_records": 0,
                "total_books": 0,
                "total_seats": 0,
                "largest_name": "N/A",
                "largest_books": 0
            })

        # 군·구 필터링 적용
        if districts_param:
            selected_districts = [urllib.parse.unquote(d.strip()) for d in districts_param.split(',')]
            df = df[df['SGG_NM'].isin(selected_districts)]

        # 도서관 유형 필터링 적용
        if types_param:
            selected_types = [urllib.parse.unquote(t.strip()) for t in types_param.split(',')]
            df = df[df['LBRRY_TYPE'].isin(selected_types)]

        # 핵심 지표(KPI) 계산
        total_records = len(df)
        total_books = int(df['BOOK_CNT'].sum())
        total_seats = int(df['PRSL_SEAT_CNT'].sum())
        
        if not df.empty:
            largest_lib = df.loc[df['BOOK_CNT'].idxmax()]
            largest_name = largest_lib['LBRRY_NM']
            largest_books = int(largest_lib['BOOK_CNT'])
        else:
            largest_name = "N/A"
            largest_books = 0

        # 필터링된 데이터가 존재하는 경우에만 시각화 파일을 재생성합니다.
        if not df.empty:
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

            m.save(os.path.join(GENERATED_DIR, 'map.html'))

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
            
            # 막대 위에 값 레이블 표기
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2.0, height + 0.1, f'{int(height)}', 
                        ha='center', va='bottom', fontsize=8, color='#1f2937', fontweight='bold')
                
            # 격자선 및 외곽 테두리선 정리 (Modern Aesthetics)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#d1d5db')
            ax.spines['bottom'].set_color('#d1d5db')
            ax.yaxis.grid(True, linestyle='--', alpha=0.5, color='#e5e7eb')
            ax.set_axisbelow(True)
            plt.tight_layout()
            
            fig.savefig(os.path.join(GENERATED_DIR, 'chart_district.png'), dpi=150)
            plt.close(fig)

            # ----------------------------------------------------
            # 3. Matplotlib 차트 2: 도서관 유형 비율 도넛 차트
            # ----------------------------------------------------
            fig, ax = plt.subplots(figsize=(6, 4))
            type_counts = df['LBRRY_TYPE'].value_counts()
            color_palette = ['#3B82F6', '#10B981', '#F59E0B', '#6B7280', '#EC4899', '#8B5CF6']
            
            # 파이 차트 생성 (도넛 형태를 만들기 위해 width=0.4 설정)
            wedges, texts, autotexts = ax.pie(
                type_counts.values, 
                labels=type_counts.index, 
                autopct='%1.1f%%',
                startangle=90, 
                colors=color_palette[:len(type_counts)],
                wedgeprops=dict(width=0.4, edgecolor='w', linewidth=2),
                textprops=dict(color='#1f2937', fontsize=9)
            )
            # 파이 영역 글자 스타일링
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(8)
                autotext.set_weight('bold')
                
            plt.tight_layout()
            fig.savefig(os.path.join(GENERATED_DIR, 'chart_type.png'), dpi=150)
            plt.close(fig)

            # ----------------------------------------------------
            # 4. Matplotlib 차트 3: 도서 보유량 상위 10개 관 가로 막대 차트
            # ----------------------------------------------------
            fig, ax = plt.subplots(figsize=(10, 4))
            top_books = df.nlargest(10, 'BOOK_CNT').sort_values('BOOK_CNT', ascending=True)
            y_labels = [name if len(name) <= 15 else name[:14] + '...' for name in top_books['LBRRY_NM']]
            
            bars = ax.barh(y_labels, top_books['BOOK_CNT'] / 1000, color='#6366F1', edgecolor='none', height=0.55)
            ax.set_xlabel("소장 도서 수 (천 권)", fontsize=9, color='#4b5563')
            ax.tick_params(colors='#4b5563', labelsize=9)
            
            # 막대 옆에 수치 및 단위 레이블 표기
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
            
            fig.savefig(os.path.join(GENERATED_DIR, 'chart_top_books.png'), dpi=150)
            plt.close(fig)

        return jsonify({
            "status": "success",
            "is_mock": is_mock,
            "total_records": total_records,
            "total_books": total_books,
            "total_seats": total_seats,
            "largest_name": largest_name,
            "largest_books": largest_books
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    # 로컬 네트워크에서 5000번 포트로 백엔드 Flask 서버 가동
    app.run(host='0.0.0.0', port=5000, debug=True)
