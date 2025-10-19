import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.title("🌍 글로벌 시가총액 Top 10 기업 주가 변화 (최근 1년)")
st.write("시가총액 상위 기업들의 최근 1년간 주가 흐름을 비교합니다.")

tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "TSM", "AVGO"]

end_date = datetime.today()
start_date = end_date - timedelta(days=365)

data = {}
for t in tickers:
    try:
        st.write(f"📈 {t} 데이터 불러오는 중...")
        df = yf.download(t, start=start_date, end=end_date, progress=False)
        if df.empty:
            st.warning(f"⚠️ {t}: 데이터를 불러오지 못했습니다.")
            continue
        col = "Adj Close" if "Adj Close" in df.columns else "Close"
        data[t] = df[col]
    except Exception as e:
        st.warning(f"⚠️ {t}: 오류 발생 ({e})")

# 데이터 확인
if not data:
    st.error("❌ 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
    st.stop()

df_all = pd.DataFrame(data)

# 인덱스가 Datetime 형식인지 확인
if not pd.api.types.is_datetime64_any_dtype(df_all.index):
    df_all.index = pd.to_datetime(df_all.index, errors="coerce")

# 모든 값이 NaN이면 종료
if df_all.isna().all().all():
    st.error("❌ 유효한 데이터가 없습니다. API 제한 또는 네트워크 문제일 수 있습니다.")
    st.stop()

# 결측치 제거
df_all = df_all.dropna(how="any")

# 데이터 검증
if df_all.empty:
    st.error("❌ 그래프로 표시할 데이터가 없습니다.")
    st.stop()

# Plotly 그래프 생성
fig = px.line(
    df_all,
    x=df_all.index,
    y=df_all.columns,
    labels={"value": "주가 (USD)", "variable": "티커"},
    title="글로벌 시가총액 Top 10 기업 – 최근 1년 주가 변화",
)

fig.update_layout(
    xaxis_title="날짜",
    yaxis_title="주가 (USD)",
    legend_title_text="기업 티커",
)

st.plotly_chart(fig, use_container_width=True)
