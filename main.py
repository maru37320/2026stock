import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="글로벌 주식 비교 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@300;400;700&display=swap');

:root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a26;
    --border: #2a2a3a;
    --accent: #00f5a0;
    --accent2: #00d9f5;
    --red: #ff4b6e;
    --text: #e8e8f0;
    --muted: #6b6b8a;
}

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background-color: var(--bg);
    color: var(--text);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Header */
.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.6rem;
    letter-spacing: 0.06em;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
    margin-bottom: 0;
}
.hero-sub {
    color: var(--muted);
    font-size: 0.85rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 4px;
}

/* Metric Cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
    margin: 16px 0;
}
.metric-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.metric-card.red::before { background: var(--red); }
.mc-ticker { font-size: 0.7rem; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; }
.mc-name   { font-size: 0.82rem; color: var(--text); margin: 2px 0 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mc-price  { font-size: 1.3rem; font-weight: 700; color: var(--text); }
.mc-ret    { font-size: 0.85rem; font-weight: 700; margin-top: 4px; }
.mc-ret.pos { color: var(--accent); }
.mc-ret.neg { color: var(--red); }

/* Section label */
.section-label {
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--muted);
    border-left: 3px solid var(--accent);
    padding-left: 10px;
    margin: 24px 0 12px;
}

/* Divider */
.hdivider { border: none; border-top: 1px solid var(--border); margin: 20px 0; }

/* Tab styling override */
.stTabs [data-baseweb="tab-list"] { background: var(--surface); border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { color: var(--muted) !important; background: transparent; }
.stTabs [aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent); }

/* Selectbox, slider colors */
.stSelectbox > div, .stMultiSelect > div { background: var(--surface2); border-color: var(--border); }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
KR_STOCKS = {
    "삼성전자":   "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "현대차":     "005380.KS",
    "POSCO홀딩스":"005490.KS",
    "카카오":     "035720.KS",
    "네이버(NAVER)": "035420.KS",
    "셀트리온":   "068270.KS",
    "KB금융":     "105560.KS",
    "신한지주":   "055550.KS",
}

US_STOCKS = {
    "Apple":      "AAPL",
    "Microsoft":  "MSFT",
    "NVIDIA":     "NVDA",
    "Amazon":     "AMZN",
    "Alphabet(Google)": "GOOGL",
    "Meta":       "META",
    "Tesla":      "TSLA",
    "Berkshire":  "BRK-B",
    "JPMorgan":   "JPM",
    "Eli Lilly":  "LLY",
}

INDICES = {
    "KOSPI":      "^KS11",
    "KOSDAQ":     "^KQ11",
    "S&P 500":    "^GSPC",
    "NASDAQ":     "^IXIC",
    "Dow Jones":  "^DJI",
}

PERIODS = {
    "1개월":  ("1mo",  "1d"),
    "3개월":  ("3mo",  "1d"),
    "6개월":  ("6mo",  "1d"),
    "1년":    ("1y",   "1wk"),
    "3년":    ("3y",   "1wk"),
    "5년":    ("5y",   "1mo"),
}

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Noto Sans KR", color="#e8e8f0", size=12),
    xaxis=dict(gridcolor="#2a2a3a", linecolor="#2a2a3a", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#2a2a3a", linecolor="#2a2a3a", tickfont=dict(size=11)),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#2a2a3a"),
    hoverlabel=dict(bgcolor="#1a1a26", bordercolor="#2a2a3a", font_color="#e8e8f0"),
)

# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_info(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return info if info else {}
    except Exception:
        return {}

def calc_return(df: pd.DataFrame) -> float | None:
    if df.empty or "Close" not in df.columns or len(df) < 2:
        return None
    first = float(df["Close"].iloc[0])
    last  = float(df["Close"].iloc[-1])
    if first == 0:
        return None
    return (last - first) / first * 100

def fmt_ret(r: float | None) -> str:
    if r is None:
        return "N/A"
    sign = "+" if r >= 0 else ""
    return f"{sign}{r:.2f}%"

def color_class(r: float | None) -> str:
    if r is None:
        return ""
    return "pos" if r >= 0 else "neg"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    st.markdown("<hr style='border-color:#2a2a3a'>", unsafe_allow_html=True)

    period_label = st.selectbox("📅 기간", list(PERIODS.keys()), index=3)
    period, interval = PERIODS[period_label]

    st.markdown("**🇰🇷 한국 주식 선택**")
    kr_selected = st.multiselect(
        "한국 종목", list(KR_STOCKS.keys()),
        default=["삼성전자", "SK하이닉스", "현대차", "네이버(NAVER)"],
        label_visibility="collapsed",
    )

    st.markdown("**🇺🇸 미국 주식 선택**")
    us_selected = st.multiselect(
        "미국 종목", list(US_STOCKS.keys()),
        default=["Apple", "NVIDIA", "Tesla", "Microsoft"],
        label_visibility="collapsed",
    )

    st.markdown("**📊 지수 선택**")
    idx_selected = st.multiselect(
        "지수", list(INDICES.keys()),
        default=["KOSPI", "S&P 500"],
        label_visibility="collapsed",
    )

    chart_type = st.radio("차트 유형", ["라인 차트", "캔들스틱"], horizontal=True)
    show_volume = st.checkbox("거래량 표시", value=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("데이터: Yahoo Finance · 5분 캐시")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 8px 0 20px'>
  <div class='hero-title'>GLOBAL STOCK RADAR</div>
  <div class='hero-sub'>한국 · 미국 주요 주식 실시간 비교 대시보드</div>
</div>
""", unsafe_allow_html=True)

# ── Build ticker lists ────────────────────────────────────────────────────────
kr_tickers  = {n: KR_STOCKS[n] for n in kr_selected}
us_tickers  = {n: US_STOCKS[n] for n in us_selected}
idx_tickers = {n: INDICES[n]   for n in idx_selected}
all_tickers = {**kr_tickers, **us_tickers}

if not all_tickers and not idx_tickers:
    st.warning("사이드바에서 종목을 하나 이상 선택해 주세요.")
    st.stop()

# ── Fetch all data ────────────────────────────────────────────────────────────
with st.spinner("데이터 불러오는 중…"):
    hist: dict[str, pd.DataFrame] = {}
    for name, tkr in {**all_tickers, **idx_tickers}.items():
        hist[name] = fetch_history(tkr, period, interval)

# ── 수익률 카드 ───────────────────────────────────────────────────────────────
def render_cards(tickers: dict, flag: str):
    cards_html = "<div class='metric-grid'>"
    for name, tkr in tickers.items():
        df = hist.get(name, pd.DataFrame())
        ret = calc_return(df)
        last_price = float(df["Close"].iloc[-1]) if not df.empty and "Close" in df.columns else None
        price_str = f"{last_price:,.0f}" if last_price else "—"
        card_cls = "" if (ret is None or ret >= 0) else "red"
        ret_cls   = color_class(ret)
        cards_html += f"""
        <div class='metric-card {card_cls}'>
          <div class='mc-ticker'>{flag} {tkr}</div>
          <div class='mc-name'>{name}</div>
          <div class='mc-price'>{price_str}</div>
          <div class='mc-ret {ret_cls}'>{fmt_ret(ret)} ({period_label})</div>
        </div>"""
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

if kr_tickers:
    st.markdown("<div class='section-label'>🇰🇷 한국 종목</div>", unsafe_allow_html=True)
    render_cards(kr_tickers, "🇰🇷")

if us_tickers:
    st.markdown("<div class='section-label'>🇺🇸 미국 종목</div>", unsafe_allow_html=True)
    render_cards(us_tickers, "🇺🇸")

# ── Tabs ──────────────────────────────────────────────────────────────────────
st.markdown("<div class='hdivider'></div>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["📈 수익률 비교", "🕯 가격 차트", "📊 지수 비교", "🔢 상세 통계"])

# ─ Tab 1: Normalized return comparison ───────────────────────────────────────
with tab1:
    st.markdown("<div class='section-label'>정규화 수익률 (시작=100)</div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    def norm_chart(tickers: dict, title: str, col):
        fig = go.Figure()
        colors = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel
        for i, (name, _) in enumerate(tickers.items()):
            df = hist.get(name, pd.DataFrame())
            if df.empty or "Close" not in df.columns:
                continue
            close = df["Close"].squeeze()
            base  = float(close.iloc[0])
            if base == 0:
                continue
            norm = close / base * 100
            fig.add_trace(go.Scatter(
                x=norm.index, y=norm.values, name=name,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f"<b>{name}</b><br>%{{x|%Y-%m-%d}}<br>수익률: %{{y:.1f}}<extra></extra>",
            ))
        fig.add_hline(y=100, line_dash="dot", line_color="#6b6b8a", line_width=1)
        fig.update_layout(**PLOTLY_THEME, title=dict(text=title, font_size=14),
                          height=360, showlegend=True)
        col.plotly_chart(fig, use_container_width=True)

    norm_chart(kr_tickers, "🇰🇷 한국 종목 수익률", col_l)
    norm_chart(us_tickers, "🇺🇸 미국 종목 수익률", col_r)

    # ─ Bar chart: returns ranking
    st.markdown("<div class='section-label'>수익률 순위</div>", unsafe_allow_html=True)
    ret_data = []
    for name, tkr in all_tickers.items():
        r = calc_return(hist.get(name, pd.DataFrame()))
        flag = "🇰🇷" if name in kr_tickers else "🇺🇸"
        ret_data.append({"종목": f"{flag} {name}", "수익률(%)": r if r is not None else 0,
                         "시장": "한국" if name in kr_tickers else "미국"})
    if ret_data:
        rdf = pd.DataFrame(ret_data).sort_values("수익률(%)")
        fig_bar = go.Figure(go.Bar(
            x=rdf["수익률(%)"], y=rdf["종목"],
            orientation="h",
            marker_color=["#ff4b6e" if v < 0 else "#00f5a0" for v in rdf["수익률(%)"]],
            text=[f"{v:+.2f}%" for v in rdf["수익률(%)"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>수익률: %{x:.2f}%<extra></extra>",
        ))
        fig_bar.update_layout(**PLOTLY_THEME, height=max(300, len(rdf) * 38),
                              xaxis_title="수익률 (%)")
        st.plotly_chart(fig_bar, use_container_width=True)

# ─ Tab 2: Price chart (line or candlestick) ───────────────────────────────────
with tab2:
    st.markdown("<div class='section-label'>개별 가격 차트</div>", unsafe_allow_html=True)
    chart_target = list(all_tickers.keys())
    if chart_target:
        selected_stock = st.selectbox("종목 선택", chart_target, key="chart_sel")
        df_c = hist.get(selected_stock, pd.DataFrame())

        if df_c.empty:
            st.warning("데이터를 불러올 수 없습니다.")
        else:
            rows = 2 if show_volume else 1
            row_heights = [0.75, 0.25] if show_volume else [1.0]
            fig_c = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                                  row_heights=row_heights, vertical_spacing=0.04)

            close_arr = df_c["Close"].squeeze().values
            base_v    = float(close_arr[0])
            last_v    = float(close_arr[-1])
            is_up     = last_v >= base_v
            clr       = "#00f5a0" if is_up else "#ff4b6e"

            if chart_type == "캔들스틱" and all(c in df_c.columns for c in ["Open","High","Low","Close"]):
                fig_c.add_trace(go.Candlestick(
                    x=df_c.index,
                    open=df_c["Open"].squeeze(),
                    high=df_c["High"].squeeze(),
                    low=df_c["Low"].squeeze(),
                    close=df_c["Close"].squeeze(),
                    increasing=dict(line_color="#00f5a0", fillcolor="#00f5a050"),
                    decreasing=dict(line_color="#ff4b6e", fillcolor="#ff4b6e50"),
                    name=selected_stock,
                ), row=1, col=1)
            else:
                fig_c.add_trace(go.Scatter(
                    x=df_c.index, y=df_c["Close"].squeeze(),
                    line=dict(color=clr, width=2),
                    fill="tozeroy",
                    fillcolor=f"{'#00f5a0' if is_up else '#ff4b6e'}18",
                    name=selected_stock,
                    hovertemplate="%{x|%Y-%m-%d}<br>종가: %{y:,.2f}<extra></extra>",
                ), row=1, col=1)

            # MA lines
            close_s = df_c["Close"].squeeze()
            for ma, col_ma in [(20, "#00d9f5"), (60, "#f5a000")]:
                if len(close_s) >= ma:
                    fig_c.add_trace(go.Scatter(
                        x=close_s.index, y=close_s.rolling(ma).mean(),
                        line=dict(color=col_ma, width=1.2, dash="dot"),
                        name=f"MA{ma}", opacity=0.8,
                        hovertemplate=f"MA{ma}: %{{y:,.2f}}<extra></extra>",
                    ), row=1, col=1)

            if show_volume and "Volume" in df_c.columns:
                vol = df_c["Volume"].squeeze()
                fig_c.add_trace(go.Bar(
                    x=vol.index, y=vol,
                    marker_color="#2a2a3a", name="거래량",
                    hovertemplate="%{x|%Y-%m-%d}<br>거래량: %{y:,}<extra></extra>",
                ), row=2, col=1)

            layout_update = {**PLOTLY_THEME,
                             "height": 500 if show_volume else 400,
                             "title": dict(text=f"{selected_stock} — {period_label} 가격 추이", font_size=15),
                             "xaxis_rangeslider_visible": False}
            if show_volume:
                layout_update["yaxis2"] = dict(gridcolor="#2a2a3a", linecolor="#2a2a3a", tickfont=dict(size=10))
            fig_c.update_layout(**layout_update)
            st.plotly_chart(fig_c, use_container_width=True)

# ─ Tab 3: Index comparison ────────────────────────────────────────────────────
with tab3:
    st.markdown("<div class='section-label'>주요 지수 비교</div>", unsafe_allow_html=True)
    if not idx_tickers:
        st.info("사이드바에서 지수를 선택하세요.")
    else:
        fig_idx = go.Figure()
        colors_idx = ["#00f5a0", "#00d9f5", "#f5a000", "#f500d9", "#ff4b6e"]
        for i, (name, _) in enumerate(idx_tickers.items()):
            df_i = hist.get(name, pd.DataFrame())
            if df_i.empty or "Close" not in df_i.columns:
                continue
            close_i = df_i["Close"].squeeze()
            norm_i  = close_i / float(close_i.iloc[0]) * 100
            fig_idx.add_trace(go.Scatter(
                x=norm_i.index, y=norm_i.values, name=name,
                line=dict(color=colors_idx[i % len(colors_idx)], width=2.5),
                hovertemplate=f"<b>{name}</b><br>%{{x|%Y-%m-%d}}<br>정규화: %{{y:.1f}}<extra></extra>",
            ))
        fig_idx.add_hline(y=100, line_dash="dot", line_color="#6b6b8a", line_width=1)
        fig_idx.update_layout(**PLOTLY_THEME, height=420,
                              title=dict(text=f"지수 정규화 비교 ({period_label})", font_size=15))
        st.plotly_chart(fig_idx, use_container_width=True)

        # Index metric cards
        cards_html = "<div class='metric-grid'>"
        for name, tkr in idx_tickers.items():
            df_i = hist.get(name, pd.DataFrame())
            ret_i = calc_return(df_i)
            last_i = float(df_i["Close"].iloc[-1]) if not df_i.empty and "Close" in df_i.columns else None
            price_str_i = f"{last_i:,.2f}" if last_i else "—"
            card_cls = "" if (ret_i is None or ret_i >= 0) else "red"
            ret_cls  = color_class(ret_i)
            cards_html += f"""
            <div class='metric-card {card_cls}'>
              <div class='mc-ticker'>📊 {tkr}</div>
              <div class='mc-name'>{name}</div>
              <div class='mc-price'>{price_str_i}</div>
              <div class='mc-ret {ret_cls}'>{fmt_ret(ret_i)} ({period_label})</div>
            </div>"""
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

# ─ Tab 4: Statistics table ────────────────────────────────────────────────────
with tab4:
    st.markdown("<div class='section-label'>상세 통계</div>", unsafe_allow_html=True)
    rows_stat = []
    for name, tkr in all_tickers.items():
        df_s = hist.get(name, pd.DataFrame())
        if df_s.empty or "Close" not in df_s.columns:
            continue
        close_s = df_s["Close"].squeeze()
        ret_s   = calc_return(df_s)
        # Volatility (annualized)
        daily_ret = close_s.pct_change().dropna()
        vol = float(daily_ret.std() * np.sqrt(252) * 100) if len(daily_ret) > 1 else None
        # Max drawdown
        roll_max = close_s.cummax()
        drawdown = (close_s - roll_max) / roll_max
        max_dd   = float(drawdown.min() * 100)
        # Sharpe (simple, rf=0)
        sharpe = float(daily_ret.mean() / daily_ret.std() * np.sqrt(252)) if len(daily_ret) > 1 and daily_ret.std() != 0 else None

        flag = "🇰🇷" if name in kr_tickers else "🇺🇸"
        rows_stat.append({
            "종목": f"{flag} {name}",
            "티커": tkr,
            "수익률(%)": f"{ret_s:+.2f}" if ret_s is not None else "N/A",
            "연환산 변동성(%)": f"{vol:.1f}" if vol else "N/A",
            "최대 낙폭(%)": f"{max_dd:.2f}" if max_dd else "N/A",
            "샤프 지수": f"{sharpe:.2f}" if sharpe else "N/A",
            "시작가": f"{float(close_s.iloc[0]):,.2f}",
            "현재가": f"{float(close_s.iloc[-1]):,.2f}",
        })

    if rows_stat:
        df_stat = pd.DataFrame(rows_stat)
        st.dataframe(
            df_stat,
            use_container_width=True,
            hide_index=True,
        )

        # Correlation heatmap
        st.markdown("<div class='section-label'>수익률 상관관계 히트맵</div>", unsafe_allow_html=True)
        ret_dict = {}
        for name in all_tickers:
            df_h = hist.get(name, pd.DataFrame())
            if not df_h.empty and "Close" in df_h.columns:
                ret_dict[name] = df_h["Close"].squeeze().pct_change()
        if len(ret_dict) >= 2:
            corr_df = pd.DataFrame(ret_dict).dropna().corr()
            labels  = [f"{'🇰🇷' if n in kr_tickers else '🇺🇸'} {n}" for n in corr_df.columns]
            fig_heat = go.Figure(go.Heatmap(
                z=corr_df.values, x=labels, y=labels,
                colorscale=[[0, "#ff4b6e"], [0.5, "#1a1a26"], [1, "#00f5a0"]],
                zmin=-1, zmax=1,
                text=np.round(corr_df.values, 2),
                texttemplate="%{text}",
                hovertemplate="x: %{x}<br>y: %{y}<br>상관계수: %{z:.2f}<extra></extra>",
            ))
            fig_heat.update_layout(**PLOTLY_THEME, height=420,
                                   title=dict(text="종목 간 상관계수 (일간 수익률 기준)", font_size=14))
            st.plotly_chart(fig_heat, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; color:#6b6b8a; font-size:0.75rem; margin-top:40px; padding-top:20px;
            border-top:1px solid #2a2a3a; letter-spacing:0.08em;'>
  GLOBAL STOCK RADAR · Powered by yfinance &amp; Streamlit · 투자 참고용, 투자 권유 아님
</div>
""", unsafe_allow_html=True)
