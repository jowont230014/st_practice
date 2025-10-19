import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.title("🌍 글로벌 시가총액 Top 10 기업 주가 변화 (최근 1년)")
st.write("시가총액 상위 기업들의 최근 1년간 주가 흐름을 비교해봅니다.")

# → 시가총액 상위 10개 기업 (예시 티커)
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "TSM", "AVGO"]

# 기간 설정: 오늘 기준으로 1년 전부터
end_date = datetime.today()
start_date = end_date - timedelta(days=365)

# 여러 종목의 주가 데이터 가져오기
data = {}
for t in tickers:
    st.write(f"데이터 가져오는 중… {t}")
    df = yf.download(t, start=start_date, end=end_date, progress=False)["Adj Close"]
    data[t] = df

# 하나의 데이터프레임으로 합치기
df_all = pd.DataFrame(data)
df_all = df_all.dropna(how="any")  # 결측치 있는 날 제거하거나 보간 가능

# 시각화: 여러 라인으로 비교
fig = px.line(
    df_all,
    x=df_all.index,
    y=df_all.columns,
    labels={"value": "주가(조정종가)", "variable": "티커"},
    title="글로벌 시가총액 Top 10 기업 – 최근 1년 주가 흐름"
)
fig.update_layout(legend_title_text="기업 티커", xaxis_title="날짜", yaxis_title="주가 (USD)")
st.plotly_chart(fig, use_container_width=True)
