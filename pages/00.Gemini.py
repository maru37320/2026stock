import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="한/미 주식 비교 분석", page_icon="📈", layout="wide")

st.title("📈 한/미 주요 주식 수익률 비교 분석기")
st.write("한국과 미국의 주요 주식 및 시장 지수의 **누적 수익률**과 **주가 흐름**을 한눈에 비교해보세요.")

# 2. 분석할 종목 딕셔너리 (한국 주식은 .KS 또는 .KQ가 붙습니다)
TICKERS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "NAVER": "035420.KS",
    "KOSPI 지수": "^KS11",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "S&P 500": "^GSPC"
}

# 3. 사이드바 UI 설정
st.sidebar.header("⚙️ 설정")

# 종목 다중 선택
selected_names = st.sidebar.multiselect(
    "비교할 종목을 선택하세요:",
    options=list(TICKERS.keys()),
    default=["삼성전자", "Apple", "KOSPI 지수", "S&P 500"]
)

# 날짜 선택
today = datetime.today()
one_year_ago = today - timedelta(days=365)

start_date = st.sidebar.date_input("시작일", one_year_ago)
end_date = st.sidebar.date_input("종료일", today)

# 4. 데이터 불러오기 함수 (캐싱하여 속도 최적화)
@st.cache_data
def load_data(selected_names, start, end):
    data = pd.DataFrame()
    for name in selected_names:
        ticker = TICKERS[name]
        # yfinance로 데이터 다운로드 (진행률 표시 숨김)
        df = yf.download(ticker, start=start, end=end, progress=False)
        
        if not df.empty:
            # yfinance 최신 버전의 MultiIndex 구조 방지 및 종가 추출
            if isinstance(df.columns, pd.MultiIndex):
                data[name] = df['Close'].iloc[:, 0]
            else:
                data[name] = df['Close']
    return data

# 5. 메인 화면 로직
if selected_names:
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦을 수 없습니다. 날짜를 다시 설정해주세요.")
    else:
        with st.spinner("주가 데이터를 불러오는 중입니다... ⏳"):
            df = load_data(selected_names, start_date, end_date)

        if not df.empty:
            # 결측치 처리 (이전 값으로 채우기)
            df = df.ffill()

            # 수익률 계산: (현재가 / 기준가 - 1) * 100
            # 기준가는 선택한 기간의 첫 번째 유효한 데이터입니다.
            df_returns = (df / df.iloc[0] - 1) * 100

            st.divider()

            # --- 섹션 1: 기간 내 누적 수익률 요약 (Metric) ---
            st.subheader(f"📊 선택 기간 누적 수익률 ({start_date} ~ {end_date})")
            cols = st.columns(len(selected_names))
            
            for i, name in enumerate(selected_names):
                if name in df_returns.columns:
                    # 마지막 날의 수익률
                    final_return = df_returns[name].iloc[-1]
                    cols[i].metric(label=name, value=f"{final_return:.2f}%")

            # --- 섹션 2: 수익률 비교 차트 (Plotly) ---
            st.subheader("📉 수익률 비교 차트")
            fig = px.line(
                df_returns, 
                x=df_returns.index, 
                y=df_returns.columns,
                labels={'value': '누적 수익률 (%)', 'Date': '날짜', 'variable': '종목'},
                template='plotly_white'
            )
            # 마우스 호버 시 편리하게 볼 수 있도록 설정
            fig.update_traces(mode="lines", hovertemplate='%{y:.2f}%')
            fig.update_layout(hovermode="x unified", legend_title_text='선택 종목')
            
            st.plotly_chart(fig, use_container_width=True)

            # --- 섹션 3: 원본 데이터 테이블 ---
            with st.expander("🔍 종가 원본 데이터 보기"):
                st.dataframe(df.round(2), use_container_width=True)
        else:
            st.warning("해당 기간에 조회 가능한 데이터가 없습니다.")
else:
    st.info("👈 좌측 사이드바에서 비교할 종목을 하나 이상 선택해주세요.")
