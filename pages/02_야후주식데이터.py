# app.py
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Optional
import time

st.set_page_config(layout="wide", page_title="Global Top10 Price Chart", initial_sidebar_state="expanded")

st.title("🌍 글로벌 시가총액 Top10 — 최근 1년 주가 변화 (안정화된 버전)")
st.write("yfinance로 데이터를 가져와 Plotly로 시각화합니다. 오류가 나면 아래 로그를 확인해 주세요.")

# --- Sidebar: 사용자 옵션 ---
with st.sidebar:
    st.header("설정")
    default_tickers = ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","BRK-B","TSM","AVGO"]
    ticker_input = st.text_area("티커 리스트 (쉼표로 구분)", value=",".join(default_tickers))
    normalize = st.checkbox("정규화: 시작일을 100으로 맞춰 비교하기 (수익률 비교)", value=True)
    start_date = st.date_input("시작일", value=(datetime.today() - timedelta(days=365)).date())
    end_date = st.date_input("종료일", value=datetime.today().date())
    dropna_method = st.selectbox("결측 처리 방식", options=["dropna(how='any')", "ffill_then_dropna", "interpolate_then_dropna"], index=0)
    st.write("---")
    st.caption("팁: 일부 티커는 yfinance에서 데이터가 없거나 제한되어 빈 데이터프레임이 반환될 수 있습니다. 그러면 로그에 표시됩니다.")

# Parse tickers
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
if not tickers:
    st.error("적어도 하나 이상의 티커를 입력하세요.")
    st.stop()

# --- 유틸리티: 안정적 데이터 수집 ---
@st.cache_data(ttl=3600)
def fetch_single_ticker(ticker: str, start: datetime, end: datetime) -> Optional[pd.Series]:
    """
    안전하게 단일 티커의 Adj Close(또는 Close) 시리즈를 가져오는 함수.
    실패시 None 반환.
    """
    try:
        # primary: yf.download (빠르고 여러 티커에 효율적)
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df is None or df.empty:
            # fallback: yf.Ticker.history
            t = yf.Ticker(ticker)
            df = t.history(start=start, end=end)
        if df is None or df.empty:
            return None
        col = "Adj Close" if "Adj Close" in df.columns else ("Close" if "Close" in df.columns else None)
        if col is None:
            return None
        # ensure datetime index
        df.index = pd.to_datetime(df.index, errors="coerce")
        series = df[col].dropna()
        if series.empty:
            return None
        series = series.sort_index()
        return series
    except Exception as e:
        # 호출 제한 등 예외 발생 시 None 반환 (상위에서 상세 메시지 표기)
        return None

# --- 데이터 수집 ---
st.info(f"티커 수: {len(tickers)} — {', '.join(tickers)}")
start_dt = datetime.combine(start_date, datetime.min.time())
end_dt = datetime.combine(end_date, datetime.max.time())

progress_bar = st.progress(0)
status_cols = st.columns(3)
succ_list = []
fail_list = []
series_dict: Dict[str, pd.Series] = {}

for i, tk in enumerate(tickers):
    status_cols[0].write(f"▶ 수집: **{tk}**")
    # fetch with retry/backoff small attempts
    series = None
    for attempt in range(3):
        series = fetch_single_ticker(tk, start_dt, end_dt)
        if series is not None:
            break
        time.sleep(1)  # 짧은 대기
    if series is None:
        fail_list.append(tk)
        status_cols[1].warning(f"⚠️ {tk} 데이터 없음")
    else:
        succ_list.append(tk)
        series_dict[tk] = series
        status_cols[2].success(f"✅ {tk} OK ({series.index.min().date()} ~ {series.index.max().date()}, {len(series)} rows)")
    progress_bar.progress((i+1)/len(tickers))

progress_bar.empty()

# --- 실패 로그 표시 ---
if fail_list:
    st.warning(f"다음 티커들에서 데이터를 가져오지 못했습니다: {', '.join(fail_list)}. (yfinance 제한 또는 티커 오타 가능)")
else:
    st.success("모든 티커에서 데이터 수집 성공")

# --- 데이터 프레임 합치기 및 전처리 ---
if not series_dict:
    st.error("유효한 데이터가 없습니다. 티커를 확인하거나 네트워크/API 제한을 확인하세요.")
    st.stop()

# make unified index (date union) and create DataFrame
all_index = pd.to_datetime(sorted({d for s in series_dict.values() for d in s.index}))
df_all = pd.DataFrame(index=all_index)
for tk, s in series_dict.items():
    # reindex to union index to align dates; keep NaN for missing days
    df_all[tk] = s.reindex(all_index)

# 결측 처리 옵션
if dropna_method == "dropna(how='any')":
    df_proc = df_all.dropna(how="any")
elif dropna_method == "ffill_then_dropna":
    df_proc = df_all.ffill().dropna(how="any")
else:  # interpolate_then_dropna
    df_proc = df_all.interpolate(method="time").dropna(how="any")

# 검증: 비어있거나 모든 값이 NaN이면 종료
if df_proc.empty or df_proc.isna().all().all():
    st.error("그래프로 만들 수 있는 유효한 행(날짜)이 없습니다. 다른 결측 처리 방법을 선택하거나 기간을 확대하세요.")
    st.write("원본 티커별 데이터 요약:")
    for tk, s in series_dict.items():
        st.write(f"- {tk}: rows={len(s)}, date_range=({s.index.min().date()} ~ {s.index.max().date()})")
    st.stop()

# 정규화 옵션: 시작일 기준 100
if normalize:
    # choose first available date row as base
    df_norm = df_proc.divide(df_proc.iloc[0]) * 100
    y_label = "지수화된 주가 (시작=100)"
    plot_df = df_norm
else:
    y_label = "주가 (USD)"
    plot_df = df_proc

# 요약 정보 출력
with st.expander("데이터 요약 (클릭해서 보기)"):
    st.write("원본(티커별) 요약:")
    for tk, s in series_dict.items():
        st.write(f"- **{tk}**: rows={len(s)}, date_range=({s.index.min().date()} ~ {s.index.max().date()})")
    st.write("---")
    st.write(f"그래프에 사용한 날짜 범위: {plot_df.index.min().date()} ~ {plot_df.index.max().date()} ({len(plot_df)} 영업일/행)")
    st.dataframe(plot_df.head())

# --- Plotly 시각화 (long form) ---
try:
    df_long = plot_df.reset_index().melt(id_vars="index", var_name="Ticker", value_name="Price")
    df_long = df_long.rename(columns={"index": "Date"})
    fig = px.line(df_long, x="Date", y="Price", color="Ticker",
                  title=f"티커별 주가 흐름 ({'정규화' if normalize else '원시값'})",
                  labels={"Price": y_label, "Date": "날짜"})
    fig.update_layout(legend_title_text="Ticker", xaxis_title="날짜", yaxis_title=y_label, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error("그래프 생성 중 오류가 발생했습니다. 아래 예외를 확인하세요.")
    st.exception(e)
    # 자세한 디버그 정보 (필요시 활성화)
    st.write("Plotly용 데이터 샘플:")
    st.dataframe(df_long.head())
    st.stop()

st.success("완료 — 그래프가 표시되었습니다.")
