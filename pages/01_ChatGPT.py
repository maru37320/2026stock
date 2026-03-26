# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Stock Comparison", layout="wide")

st.title("📈 한국 vs 미국 주식 비교 웹앱")

# 기본 종목 리스트
korea_stocks = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "네이버": "035420.KS",
    "카카오": "035720.KS"
}

us_stocks = {
    "애플": "AAPL",
    "마이크로소프트": "MSFT",
    "엔비디아": "NVDA",
    "테슬라": "TSLA"
}

st.sidebar.header("종목 선택")
selected_korea = st.sidebar.multiselect("한국 주식", list(korea_stocks.keys()), default=["삼성전자"])
selected_us = st.sidebar.multiselect("미국 주식", list(us_stocks.keys()), default=["애플"])

period = st.sidebar.selectbox("기간", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

@st.cache_data
def load_data(tickers, period):
    data = yf.download(tickers, period=period)["Adj Close"]
    return data

# 티커 변환
selected_tickers = [korea_stocks[s] for s in selected_korea] + [us_stocks[s] for s in selected_us]

if selected_tickers:
    data = load_data(selected_tickers, period)

    # 수익률 계산
    returns = (data / data.iloc[0] - 1) * 100

    st.subheader("📊 수익률 비교 (%)")
    st.dataframe(returns.tail())

    # 그래프
    st.subheader("📉 주가 및 수익률 그래프")
    fig, ax = plt.subplots()

    for col in returns.columns:
        ax.plot(returns.index, returns[col], label=col)

    ax.set_ylabel("Return (%)")
    ax.legend()

    st.pyplot(fig)

    # 원본 가격 데이터
    st.subheader("💰 원본 주가 데이터")
    st.dataframe(data.tail())

else:
    st.warning("하나 이상의 종목을 선택해주세요.")


# requirements.txt
# 아래 내용을 requirements.txt 파일로 저장하세요

"""
streamlit
yfinance
pandas
matplotlib
"""
