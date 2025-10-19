import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.title("🌍 글로벌 시가총액 Top 10 기업 주가 변화 (최근 1년)")
st.write("시가총액 상위 기업들의 최근 1년간 주가 흐름을 비교합니다.")

# 시가총액 상위 10개 기업 (예시)
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "TSM", "AVGO"]

# 기간 설정
end_date = datetime.today()
start_date = end_date - timedelta(days=365)

# 데이터 수집
data = {}
for t in tickers:
    try:
        st.write(f"📈 {t} 데이터 불러오는 중...")
        df = yf.download(t, start=start_date, end=end_date, progress=False)
        if df.empty:
            st.warning(f"⚠️ {t}: 데이터를 불러오지 못했습니다.")
            continue
        # 'Adj Close'가 없을 경우 'Close' 사용
        col_name = "Adj Close" if "Adj Close" in df.columns else "Close"
        data[t] = df[col_name]
    except Exception as e:
        st.error(f"❌ {t} 불러오기 실패: {e}")

# 데이터 병합
if not data:
    st.error("데이터를 불러오지 못했습니다. 나중에 다시 시도해주세요.")
    st.stop()

df_all = pd.DataFrame(data)
df_all = df_all.dropna(how="any")

# 시각화
fig = px.line(
    df_all,
    x=df_all.index,
    y=df_all.columns,
    labels={"value": "주가 (USD)", "variable": "티커"},
    title="글로벌 시가총액 Top 10 기업 – 최근 1년 주가 변화",
)
fig.update_layout(xaxis_title="날짜", yaxis_title="주가 (USD)", legend_title_text="기업 티커")
st.plotly_chart(fig, use_container_width=True)
