import streamlit as st
from datetime import datetime, timedelta, date, time
import pytz
import calendar
import holidays
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. 基本設定 ---
if 'lang' not in st.session_state: st.session_state.lang = "JP"
calendar.setfirstweekday(calendar.SUNDAY)
st_autorefresh(interval=60000, key="data_refresh")
st_autorefresh(interval=1000, key="clock_refresh")
st.set_page_config(page_title="Market Analytics Dashboard", layout="wide")

# 祝日定義
US_HOLIDAYS = holidays.US()
JP_HOLIDAYS = holidays.Japan()

T = {
    "JP": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場",
        "open": "開場中", "closed": "閉場中", "next_prefix": "次回開場まで: ",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶",
        "news_title": "🚀 今週のAI株式ニュース (TOP 10)", "event_title": "注目の株式イベント",
        "dst_on": "（サマータイム）", "dst_off": "",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土"
    },
    "EN": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market",
        "open": "OPEN", "closed": "CLOSED", "next_prefix": "Next Open in: ",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶",
        "news_title": "🚀 Weekly AI Stock News (TOP 10)", "event_title": "Monthly Events",
        "dst_on": "(EDT)", "dst_off": "",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT"
    }
}
L = T[st.session_state.lang]

# --- 2. 時刻取得 ---
# ニューヨーク時間
now_ny = datetime.now(pytz.timezone('America/New_York')).replace(tzinfo=None)
# 日本時間
now_jp = datetime.now(pytz.timezone('Asia/Tokyo')).replace(tzinfo=None)

# --- 3. CSS (デザイナー仕様) ---
st.markdown(f"""
<style>
    .stApp {{ background-color: #ffffff; color: #000000; }}
    [data-testid="stHeader"] {{ display: none; }}
    .header-sticky {{
        position: fixed; top: 0; left: 0; width: 100%; background: #ffffff;
        z-index: 9999; padding: 15px 40px; display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #eee;
    }}
    .logo-text {{ font-size: 1.4rem; font-weight: 900; color: #000000; }}
    .block-container {{ padding-top: 5rem !important; }}
    .price-box {{ border: 1px solid #cccccc; padding: 15px; text-align: center; border-radius: 4px; background: #fff; }}
    .price-val {{ font-size: 1.8rem; font-weight: 900; }}
    .status-line {{ font-size: 1.15rem; font-weight: 900; padding: 12px; border: 1px solid #cccccc; border-left: 10px solid #000000; background: #fff; margin-bottom: 15px; }}
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; table-layout: fixed; border: 1px solid #cccccc; }}
    .calendar-table th, .calendar-table td {{ border: 1px solid #cccccc; padding: 10px 0; }}
    .today-marker {{ background: #000; color: #fff; padding: 4px 8px; border-radius: 4px; font-weight: 800; }}
    .item-row {{ font-size: 0.88rem; border-bottom: 1px dotted #ccc; padding: 8px 0; }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #000; padding-bottom: 5px; margin-bottom: 10px; }}
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="header-sticky"><div class="logo-text">{L["logo"]}</div></div>', unsafe_allow_html=True)

# 言語切替
_, col_lang = st.columns([8, 2])
with col_lang:
    new_lang = st.segmented_control("Language", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

# --- 4. 市場データ ---
@st.cache_data(ttl=60)
def get_market_data():
    tickers = {"S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X"}
    res = {}
    for k, v in tickers.items():
        try:
            t = yf.Ticker(v); h = t.history(period="2d")
            res[k] = {"val": h['Close'].iloc[-1], "diff": h['Close'].iloc[-1] - h['Close'].iloc[-2]}
        except: res[k] = {"val": 0, "diff": 0}
    return res

prices = get_market_data()
cols = st.columns(3)
for i, (k, v) in enumerate(prices.items()):
    with cols[i]:
        st.markdown(f'<div class="price-box"><div style="font-weight:900;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

# --- 5. メイン表示 ---
if 'v_us' not in st.session_state: st.session_state.v_us = now_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = now_jp.date().replace(day=1)

c_us, c_jp = st.columns(2, gap="medium")

# 米国
with c_us:
    st.header(L["us_m"])
    is_op_u = (time(9,30) <= now_ny.time() < time(16,0) and now_ny.weekday() < 5 and now_ny.date() not in US_HOLIDAYS)
    st.markdown(f'<div class="status-line" style="background:{"#f0fff4" if is_op_u else "#fff5f5"};">{L["open"] if is_op_u else L["closed"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:900; font-size:1.35rem;">{now_ny.strftime("%Y/%m/%d %H:%M:%S")} <span style="font-size:0.8rem; color:gray;">{L["dst_on"]}</span></div>', unsafe_allow_html=True)
    
    # カレンダー (US)
    v_u = st.session_state.v_us
    cal = calendar.monthcalendar(v_u.year, v_u.month)
    html = f'<table class="calendar-table"><tr>'
    for i, d_n in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]):
        color = "#d71920" if i==0 else ("#0050b3" if i==6 else "#000")
        html += f'<th style="color:{color};">{d_n}</th>'
    html += '</tr>'
    for row in cal:
        html += '<tr>'
        for i, d in enumerate(row):
            if d == 0: html += '<td></td>'
            else:
                curr = date(v_u.year, v_u.month, d)
                color = "#d71920" if (i==0 or curr in US_HOLIDAYS) else ("#0050b3" if i==6 else "#000")
                day_val = f'<span class="today-marker">{d}</span>' if curr == now_ny.date() else str(d)
                html += f'<td><span style="color:{color}; font-weight:800;">{day_val}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)

    # イベント (US)
    with st.container(border=True):
        st.markdown(f'<div class="box-header">{v_u.month}月 {L["event_title"]}</div>', unsafe_allow_html=True)
        evs = {"2026-04-10": "🇺🇸 米CPI発表", "2026-04-30": "🇺🇸 FOMC発表", "2026-05-01": "🇺🇸 米雇用統計"}
        for k, v in sorted(evs.items()):
            if k.startswith(v_u.strftime("%Y-%m")):
                st.markdown(f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>', unsafe_allow_html=True)

# 日本
with c_jp:
    st.header(L["jp_m"])
    is_op_j = (time(9,0) <= now_jp.time() < time(15,0) and now_jp.weekday() < 5 and now_jp.date() not in JP_HOLIDAYS)
    st.markdown(f'<div class="status-line" style="background:{"#f0fff4" if is_op_j else "#fff5f5"};">{L["open"] if is_op_j else L["closed"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:900; font-size:1.35rem;">{now_jp.strftime("%Y/%m/%d %H:%M:%S")}</div>', unsafe_allow_html=True)

    # カレンダー (JP)
    v_j = st.session_state.v_jp
    cal = calendar.monthcalendar(v_j.year, v_j.month)
    html = f'<table class="calendar-table"><tr>'
    for i, d_n in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]):
        color = "#d71920" if i==0 else ("#0050b3" if i==6 else "#000")
        html += f'<th style="color:{color};">{d_n}</th>'
    html += '</tr>'
    for row in cal:
        html += '<tr>'
        for i, d in enumerate(row):
            if d == 0: html += '<td></td>'
            else:
                curr = date(v_j.year, v_j.month, d)
                color = "#d71920" if (i==0 or curr in JP_HOLIDAYS) else ("#0050b3" if i==6 else "#000")
                day_val = f'<span class="today-marker">{d}</span>' if curr == now_jp.date() else str(d)
                html += f'<td><span style="color:{color}; font-weight:800;">{day_val}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)

    # イベント (JP)
    with st.container(border=True):
        st.markdown(f'<div class="box-header">{v_j.month}月 {L["event_title"]}</div>', unsafe_allow_html=True)
        evs = {"2026-04-28": "🇯🇵 日銀発表", "2026-04-29": "🇯🇵 昭和の日", "2026-05-03": "🇯🇵 憲法記念日"}
        for k, v in sorted(evs.items()):
            if k.startswith(v_j.strftime("%Y-%m")):
                st.markdown(f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>', unsafe_allow_html=True)
