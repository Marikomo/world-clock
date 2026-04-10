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

# 祝日データの完全分離
US_HOLIDAYS_LIST = holidays.US()
JP_HOLIDAYS_LIST = holidays.Japan()

T = {
    "JP": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場",
        "open": "開場中", "closed": "閉場中", "next_prefix": "次回開場まで: ",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶",
        "news_title": "🚀 今週のAI株式ニュース (TOP 10)", "event_title": "注目の株式イベント",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土"
    },
    "EN": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market",
        "open": "OPEN", "closed": "CLOSED", "next_prefix": "Next Open in: ",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶",
        "news_title": "🚀 Weekly AI Stock News (TOP 10)", "event_title": "Monthly Events",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT"
    }
}
L = T[st.session_state.lang]

# --- 2. 時刻取得 (JSTから13時間戻して米国時間を生成) ---
now_jp_abs = datetime.now(pytz.timezone('Asia/Tokyo')).replace(tzinfo=None)
now_ny_abs = now_jp_abs - timedelta(hours=13)

# --- 3. CSS (デザイナー仕様: 余白を詰め、配色を厳格化) ---
st.markdown(f"""
<style>
    .stApp {{ background-color: #ffffff !important; color: #000000 !important; }}
    [data-testid="stHeader"] {{ display: none !important; }}
    .header-sticky {{
        position: fixed; top: 0; left: 0; width: 100%; background: #ffffff;
        z-index: 9999; padding: 15px 40px; display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #eeeeee;
    }}
    .logo-text {{ font-size: 1.4rem; font-weight: 900; color: #000000; letter-spacing: -0.02em; }}
    .block-container {{ padding-top: 3.5rem !important; margin-top: -20px !important; }}
    .price-box {{ border: 1px solid #cccccc; padding: 12px; text-align: center; border-radius: 4px; background: #fff; }}
    .price-val {{ font-size: 1.6rem; font-weight: 900; line-height: 1.1; }}
    .status-line {{ font-size: 1.15rem; font-weight: 900; padding: 10px; border: 1px solid #cccccc; border-left: 10px solid #000000; background: #fff; margin-bottom: 15px; }}
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; border: 1px solid #cccccc; table-layout: fixed; }}
    .calendar-table th, .calendar-table td {{ border: 1px solid #cccccc; padding: 8px 0; }}
    .today-marker {{ background: #000; color: #fff !important; padding: 4px 8px; border-radius: 4px; font-weight: 800; }}
    .item-row {{ font-size: 0.88rem; border-bottom: 1px dotted #cccccc; padding: 8px 0; text-align: left; }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #000000; padding-bottom: 5px; margin-bottom: 10px; }}
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="header-sticky"><div class="logo-text">{L["logo"]}</div></div>', unsafe_allow_html=True)

# 言語切替
_, col_lang = st.columns([8, 2])
with col_lang:
    new_lang = st.segmented_control("Lang", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()

# --- 4. 市場データ ---
@st.cache_data(ttl=60)
def get_prices():
    tickers = {"S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X"}
    res = {}
    for k, v in tickers.items():
        try:
            t = yf.Ticker(v); h = t.history(period="2d")
            res[k] = {"val": h['Close'].iloc[-1], "diff": h['Close'].iloc[-1] - h['Close'].iloc[-2]}
        except: res[k] = {"val": 0, "diff": 0}
    return res
prices_dict = get_prices()
p_cols = st.columns(3)
for i, (k, v) in enumerate(prices_dict.items()):
    with p_cols[i]:
        st.markdown(f'<div class="price-box"><div style="font-weight:900; font-size:0.9rem;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800; font-size:0.85rem;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

# セッション
if 'v_us' not in st.session_state: st.session_state.v_us = now_ny_abs.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = now_jp_abs.date().replace(day=1)

c_left, c_right = st.columns(2, gap="medium")

# ==========================================
# 🇺🇸 米国市場 (US)
# ==========================================
with c_left:
    st.header(L["us_m"])
    is_op_u = (time(9,30) <= now_ny_abs.time() < time(16,0) and now_ny_abs.weekday() < 5 and now_ny_abs.date() not in US_HOLIDAYS_LIST)
    st.markdown(f'<div class="status-line" style="background:{"#f0fff4" if is_op_u else "#fff5f5"};">{L["open"] if is_op_u else L["closed"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:900; font-size:1.35rem; margin-bottom:15px;">{now_ny_abs.strftime("%Y/%m/%d %H:%M:%S")} <span style="font-size:0.75rem; color:gray; font-weight:normal;">(EDT)</span></div>', unsafe_allow_html=True)

    # 米国カレンダー
    vu = st.session_state.v_us
    cu = calendar.monthcalendar(vu.year, vu.month)
    hu = f'<table class="calendar-table"><tr>'
    for i, d_name in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]):
        color = "#d71920" if i==0 else ("#0050b3" if i==6 else "#000")
        hu += f'<th style="color:{color} !important;">{d_name}</th>'
    hu += '</tr>'
    for row in cu:
        hu += '<tr>'
        for i, d in enumerate(row):
            if d == 0: hu += '<td></td>'
            else:
                curr = date(vu.year, vu.month, d)
                d_c = "#d71920" if (i==0 or curr in US_HOLIDAYS_LIST) else ("#0050b3" if i==6 else "#000000")
                d_txt = f'<span class="today-marker">{d}</span>' if curr == now_ny_abs.date() else str(d)
                hu += f'<td><span style="color:{d_c} !important; font-weight:800;">{d_txt}</span></td>'
    st.markdown(hu + "</table>", unsafe_allow_html=True)

    # 米国イベント
    with st.container(border=True):
        st.markdown(f'<div class="box-header">{vu.month}月 米国市場イベント</div>', unsafe_allow_html=True)
        edu = {"2026-04-10": "🇺🇸 米CPI発表", "2026-04-30": "🇺🇸 FOMC発表", "2026-05-01": "🇺🇸 米雇用統計"}
        meu = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(edu.items()) if k.startswith(vu.strftime("%Y-%m"))]
        st.markdown('<div style="height:120px; overflow-y:auto;">' + ("".join(meu) if meu else "予定なし") + '</div>', unsafe_allow_html=True)

    # AIニュース (米国)
    with st.container(border=True):
        st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
        nu = "".join([f'<div class="item-row">{i+1}. 米国テック・金融 最新ニュース {i+1}</div>' for i in range(10)])
        st.markdown(f'<div style="height:200px; overflow-y:auto;">{nu}</div>', unsafe_allow_html=True)

# ==========================================
# 🇯🇵 日本市場 (JP)
# ==========================================
with c_right:
    st.header(L["jp_m"])
    is_op_j = (time(9,0) <= now_jp_abs.time() < time(15,0) and now_jp_abs.weekday() < 5 and now_jp_abs.date() not in JP_HOLIDAYS_LIST)
    st.markdown(f'<div class="status-line" style="background:{"#f0fff4" if is_op_j else "#fff5f5"};">{L["open"] if is_op_j else L["closed"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:900; font-size:1.35rem; margin-bottom:15px;">{now_jp_abs.strftime("%Y/%m/%d %H:%M:%S")}</div>', unsafe_allow_html=True)

    # 日本カレンダー
    vj = st.session_state.v_jp
    cj = calendar.monthcalendar(vj.year, vj.month)
    hj = f'<table class="calendar-table"><tr>'
    for i, d_name in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]):
        color = "#d71920" if i==0 else ("#0050b3" if i==6 else "#000")
        hj += f'<th style="color:{color} !important;">{d_name}</th>'
    hj += '</tr>'
    for row in cj:
        hj += '<tr>'
        for i, d in enumerate(row):
            if d == 0: hj += '<td></td>'
            else:
                curr = date(vj.year, vj.month, d)
                d_c = "#d71920" if (i==0 or curr in JP_HOLIDAYS_LIST) else ("#0050b3" if i==6 else "#000000")
                d_txt = f'<span class="today-marker">{d}</span>' if curr == now_jp_abs.date() else str(d)
                hj += f'<td><span style="color:{d_c} !important; font-weight:800;">{d_txt}</span></td>'
    st.markdown(hj + "</table>", unsafe_allow_html=True)

    # 日本イベント
    with st.container(border=True):
        st.markdown(f'<div class="box-header">{vj.month}月 日本市場イベント</div>', unsafe_allow_html=True)
        edj = {"2026-04-28": "🇯🇵 日銀発表", "2026-04-29": "🇯🇵 昭和の日", "2026-05-03": "🇯🇵 憲法記念日"}
        mej = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(edj.items()) if k.startswith(vj.strftime("%Y-%m"))]
        st.markdown('<div style="height:120px; overflow-y:auto;">' + ("".join(mej) if mej else "予定なし") + '</div>', unsafe_allow_html=True)

    # AIニュース (日本)
    with st.container(border=True):
        st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
        nj = "".join([f'<div class="item-row">{i+1}. 日本国内AI関連 注目ニュース {i+1}</div>' for i in range(10)])
        st.markdown(f'<div style="height:200px; overflow-y:auto;">{nj}</div>', unsafe_allow_html=True)
