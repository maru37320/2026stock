import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="한/미 주식 비교 분석", page_icon="📈", layout="wide")

st.title("📈 한/미 주요 주식 수익률 비교 분석기")
st.write("현재 시세 및 누적 수익률과 주가 흐름을 한눈에 비교해보세요.")

# 2. 분석할 종목 딕셔너리
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

selected_names = st.sidebar.multiselect(
    "비교할 종목을 선택하세요:",
    options=list(TICKERS.keys()),
    default=["삼성전자", "Apple", "KOSPI 지수", "S&P 500"]
)

today = datetime.today()
one_year_ago = today - timedelta(days=365)

start_date = st.sidebar.date_input("시작일", one_year_ago)
end_date = st.sidebar.date_input("종료일", today)

# 4. 실시간(현재가) 데이터 불러오기 함수 (1분마다 캐시 갱신)
@st.cache_data(ttl=60)
def get_current_prices(names):
    prices = {}
    for name in names:
        ticker = TICKERS[name]
        try:
            # 최근 5일 데이터를 가져와서 어제와 오늘(현재) 가격 비교
            df_recent = yf.download(ticker, period="5d", progress=False)
            if len(df_recent) >= 2:
                # yfinance 멀티인덱스 구조 처리
                if isinstance(df_recent.columns, pd.MultiIndex):
                    closes = df_recent['Close'].iloc[:, 0]
                else:
                    closes = df_recent['Close']
                
                current_price = closes.iloc[-1]
                prev_price = closes.iloc[-2]
                change_pct = ((current_price - prev_price) / prev_price) * 100
                
                # 통화 기호 설정
                currency = "₩" if ticker.endswith((".KS", ".KQ")) else "$"
                if "^" in ticker: # 지수인 경우
                    currency = "pt"
                    
                prices[name] = {
                    "price": current_price,
                    "change_pct": change_pct,
                    "currency": currency
                }
        except Exception:
            prices[name] = None
    return prices

# 5. 과거 추세 데이터 불러오기 함수
@st.cache_data
def load_data(names, start, end):
    data = pd.DataFrame()
    for name in names:
        ticker = TICKERS[name]
        df = yf.download(ticker, start=start, end=end, progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                data[name] = df['Close'].iloc[:, 0]
            else:
                data[name] = df['Close']
    return data

# 6. 메인 화면 로직
if selected_names:
    
    # --- 섹션 1: 실시간 시세 요약 보드 ---
    st.subheader("⚡ 현재가 및 일일 등락률 (약 15분 지연)")
    current_prices = get_current_prices(selected_names)
    
    # 선택된 종목 수만큼 컬럼을 나누어 현재가 표시
    cols = st.columns(len(selected_names))
    for i, name in enumerate(selected_names):
        data = current_prices.get(name)
        if data:
            price_formatted = f"{data['currency']} {data['price']:,.2f}"
            delta_formatted = f"{data['change_pct']:.2f}%"
            cols[i].metric(label=name, value=price_formatted, delta=delta_formatted)
        else:
            cols[i].metric(label=name, value="데이터 없음")

    st.divider()
    
    # --- 섹션 2: 기간 내 수익률 비교 ---
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦을 수 없습니다. 날짜를 다시 설정해주세요.")
    else:
        with st.spinner("주가 추세 데이터를 불러오는 중입니다... ⏳"):
            df = load_data(selected_names, start_date, end_date)

        if not df.empty:
            df = df.ffill() # 결측치 처리
            df_returns = (df / df.iloc[0] - 1) * 100

            st.subheader(f"📊 선택 기간 누적 수익률 추이 ({start_date} ~ {end_date})")
            
            # Plotly 차트
            fig = px.line(
                df_returns, 
                x=df_returns.index, 
                y=df_returns.columns,
                labels={'value': '누적 수익률 (%)', 'Date': '날짜', 'variable': '종목'},
                template='plotly_white'
            )
            fig.update_traces(mode="lines", hovertemplate='%{y:.2f}%')
            fig.update_layout(hovermode="x unified", legend_title_text='선택 종목')
            
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("🔍 종가 원본 데이터 보기"):
                st.dataframe(df.round(2), use_container_width=True)
        else:
            st.warning("해당 기간에 조회 가능한 데이터가 없습니다.")
else:
    st.info("👈 좌측 사이드바에서 비교할 종목을 하나 이상 선택해주세요.")
