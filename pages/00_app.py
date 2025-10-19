import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 연령별 인구 시각화", layout="wide")

st.title("📊 연령별 인구 현황 (2025년 9월 기준)")
st.write("CSV 데이터를 기반으로 지역별 연령 인구 분포를 시각화합니다.")

# --- 데이터 불러오기 ---
@st.cache_data
def load_data():
    file_path = "202509_202509_연령별인구현황_월간_남녀합계.csv"
    df = pd.read_csv(file_path, header=None, encoding="utf-8")

    # '행정기관코드'가 들어 있는 행 찾기
    header_row = df.index[df.iloc[:, 0] == "행정기관코드"][0]

    # 헤더 설정
    df.columns = df.iloc[header_row]
    df = df[header_row + 1 :].reset_index(drop=True)

    # 불필요한 열 제거
    df = df.dropna(axis=1, how="all")

    # 쉼표 제거 및 숫자형 변환
    for col in df.columns[3:]:
        df[col] = df[col].astype(str).str.replace(",", "").astype(float)

    return df

df = load_data()

# --- 지역 선택 ---
region_list = df["행정기관"].dropna().unique()
region = st.selectbox("지역 선택", sorted(region_list), index=0)

# --- 데이터 필터링 ---
region_df = df[df["행정기관"] == region]
if not region_df.empty:
    region_data = region_df.iloc[0, 4:]  # 연령별 인구 데이터만 추출

    # --- Plotly 그래프 ---
    fig = px.bar(
        x=region_data.index,
        y=region_data.values,
        title=f"{region} 연령별 인구 분포 (2025년 9월 기준)",
        labels={"x": "연령", "y": "인구수"},
        color=region_data.values,
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        template="plotly_white",
        width=1000,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("선택한 지역의 데이터가 없습니다.")
