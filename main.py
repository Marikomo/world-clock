import streamlit as st
from datetime import datetime, timedelta, date, time
import pytz
import calendar
import holidays
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 言語設定の初期化 ---
if 'lang' not in st.session_state:
    st.session_state.lang = "JP"

# --- 基本設定 ---
calendar.setfirstweekday(calendar.SUNDAY)
st_autorefresh(interval=60000, key="data_refresh")
st_autorefresh(interval=1000, key="clock_refresh")
st.set_page_config(page_title="Stock Market Calendar", layout="wide")

# テキスト辞書
T = {
    "JP": {
        "us_market": "🇺🇸 米国市場", "jp_market": "🇯🇵 日本市場",
        "next_open": "次回の開場まで: ", "prev": "◀", "next": "▶", "today": "今月"
    },
    "EN": {
        "us_market": "🇺🇸 US Market", "jp_market": "🇯🇵 JP Market",
        "next_open": "Next Open in: ", "prev": "Prev", "next": "Next", "today": "Current"
    }
}
L = T[st.session_state.lang]

# --- スタイル設定（余白・レスポンシブ） ---
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none !important; }
    .block-container { 
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important;
        margin-top: -50px !important; 
    }
    
    .lang-container { position: absolute; top: 0px; right: 20px; z-index: 1000; }

    .main-big-title {
        font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 3.5rem; font-weight: 900; color: #111; text-align: center;
        letter-spacing: -0.04em; margin-top: 0px !important; margin-bottom: 30px; 
        line-height: 1.1; padding-top: 20px;
    }

    @media (max-width: 800px) {
        .main-big-title { font-size: 1.8rem; margin-bottom: 20px; }
        .desktop-only { display: none !important; }
        .mobile-only { display: block !important; }
    }
    @media (min-width: 801px) {
        .mobile-only { display: none !important; }
        .desktop-only { display: block !important; }
    }

    .indicator-box { border: 1px solid #ddd; padding: 10px; text-align: center; background-color: #fff; margin-bottom: 15px; }
    .indicator-label { font-size: 0.75rem; color: #666; font-weight: 700; text-transform: uppercase; }
    .indicator-value { font-size: 1.1rem; font-weight: 800; margin: 2px 0; color: #111; }
    .stButton > button { border-radius: 0px !important; border: 1px solid #ccc !important; width: 100%; height: 38px; font-weight: 700; font-size: 0.85rem; }
    .calendar-table { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; text-align: center; width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 0.9rem; }
    .calendar-table th { font-weight: 800; color: #222; padding-bottom: 5px; }
    .today-marker { background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; }
    .price-up { color: #d71920; } .price-down { color: #0050b3; }
    .market-status { font-size: 0.95rem; font-weight: 800; padding: 12px; border: 1px solid #ddd; margin-bottom: 15px; background-color: #fff; border-left: 5px solid #333; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="lang-container">', unsafe_allow_html=True)
c_empty, c_lang = st.columns([10, 1.5])
with c_lang:
    new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="main-big-title">US/Japan Stock Market<br>Real-time Calendar</div>', unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_market_prices():
    tickers = { "S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X" }
    data = {}
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker); h = t.history(period="2d")
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            data[name] = {"price": curr, "diff": curr - prev, "pct": ((curr-prev)/prev)*100}
        except: data[name] = {"price": 0, "diff": 0, "pct": 0}
    return data

p = get_market_prices()
m_cols = st.columns(3)
for i, (name, d) in enumerate(p.items()):
    c, s = ("price-up", "▲") if d['diff'] >= 0 else ("price-down", "▼")
    with m_cols[i]:
        st.markdown(f'<div class="indicator-box"><div class="indicator-label">{name}</div><div class="indicator-value">{d["price"]:,.1f}</div><div class="{c}" style="font-size:0.75rem; font-weight:700;">{s}{abs(d["diff"]):.1f} ({d["pct"]:.2f}%)</div></div>', unsafe_allow_html=True)

def get_market_status_ui(now, market_type):
    cc, th = ("US", holidays.CountryHoliday("US")) if market_type == "US" else ("JP", holidays.CountryHoliday("JP"))
    is_h = now.date() in th
    ot, ct = (now.replace(hour=9, minute=30, second=0), now.replace(hour=16, minute=0, second=0)) if market_type == "US" else (now.replace(hour=9, minute=0, second=0), now.replace(hour=15, minute=0, second=0))
    nx = now + timedelta(days=1); nx = nx.replace(hour=ot.hour, minute=ot.minute)
    cd = f"Next Open: {nx.strftime('%m/%d %H:%M')}"
    if not (0 <= now.weekday() <= 4) or is_h: return f"CLOSED ({'HOLIDAY' if is_h else 'WEEKEND'})<br><small>{cd}</small>", "#f9f9f9"
    if now < ot: return f"WAITING... (Opens in {(ot-now).seconds//3600:02d}:{(ot-now).seconds//60%60:02d})", "#fffbe6"
    elif ot <= now < ct: return f"OPEN (Closes in {(ct-now).seconds//3600:02d}:{(ct-now).seconds//60%60:02d})", "#e6ffed"
    else: return f"CLOSED (DAY END)<br><small>{cd}</small>", "#fff1f0"

# --- 重複を避けるために suffix (接尾辞) を追加 ---
def draw_cal_ui(now_full, country_code, state_key, country_tz, suffix=""):
    view_date = st.session_state[state_key]
    st.markdown(f"<div style='font-weight:900; font-size:1.1rem; margin-bottom:5px;'>{view_date.strftime('%Y / %m' if st.session_state.lang == 'JP' else '%B %Y')}</div>", unsafe_allow_html=True)
    target_holidays = holidays.CountryHoliday(country_code)
    cal = calendar.monthcalendar(view_date.year, view_date.month)
    html = f'<table class="calendar-table"><tr><th>SUN</th><th>MON</th><th>TUE</th><th>WED</th><th>THU</th><th>FRI</th><th>SAT</th></tr>'
    for week in cal:
        html += '<tr>'
        for i, day in enumerate(week):
            if day == 0: html += '<td></td>'
            else:
                curr = date(view_date.year, view_date.month, day); h = target_holidays.get(curr)
                cls = "holiday-red" if (h or i==0 or i==6) else ""
                cnt = f'<span class="today-marker">{day}</span>' if curr == now_full.date() else str(day)
                html += f'<td><span class="{cls}">{cnt}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)
    
    b1, b2, b3 = st.columns([1, 1, 1])
    # keyにsuffixを追加して一意にする
    if b1.button(L["prev"], key=f"prev_{state_key}_{suffix}"):
        m, y = (view_date.month-1, view_date.year) if view_date.month > 1 else (12, view_date.year-1)
        st.session_state[state_key] = date(y, m, 1); st.rerun()
    if b2.button(L["today"], key=f"today_{state_key}_{suffix}"):
        st.session_state[state_key] = datetime.now(pytz.timezone(country_tz)).date().replace(day=1); st.rerun()
    if b3.button(L["next"], key=f"next_{state_key}_{suffix}"):
        m, y = (view_date.month+1, view_date.year) if view_date.month < 12 else (1, view_date.year+1)
        st.session_state[state_key] = date(y, m, 1); st.rerun()

tz_ny, tz_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
now_ny, now_jp = datetime.now(tz_ny), datetime.now(tz_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = now_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = now_jp.date().replace(day=1)

# 1. デスクトップ表示 (suffix="d")
st.markdown('<div class="desktop-only">', unsafe_allow_html=True)
d_col_us, d_col_jp = st.columns(2, gap="large")
with d_col_us:
    st.header(L["us_market"])
    s, c = get_market_status_ui(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {c};">{s}</div>', unsafe_allow_html=True)
    draw_cal_ui(now_ny, "US", "v_us", "America/New_York", suffix="d")
with d_col_jp:
    st.header(L["jp_market"])
    s, c = get_market_status_ui(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {c};">{s}</div>', unsafe_allow_html=True)
    draw_cal_ui(now_jp, "JP", "v_jp", "Asia/Tokyo", suffix="d")
st.markdown('</div>', unsafe_allow_html=True)

# 2. モバイル表示 (suffix="m")
st.markdown('<div class="mobile-only">', unsafe_allow_html=True)
m_tab_us, m_tab_jp = st.tabs([L["us_market"], L["jp_market"]])
with m_tab_us:
    s, c = get_market_status_ui(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {c};">{s}</div>', unsafe_allow_html=True)
    draw_cal_ui(now_ny, "US", "v_us", "America/New_York", suffix="m")
with m_tab_jp:
    s, c = get_market_status_ui(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {c};">{s}</div>', unsafe_allow_html=True)
    draw_cal_ui(now_jp, "JP", "v_jp", "Asia/Tokyo", suffix="m")
st.markdown('</div>', unsafe_allow_html=True)
