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
        "dst": "サマータイム中", "std": "標準時",
        "open": "🟢 OPEN (閉場まで: ", "closed_pre": "⏳ CLOSED (開場まで: ",
        "closed_post": "🔴 CLOSED (本日終了)", "next_open": "次回の開場まで: ",
        "weekend": "週末", "holiday": "祝日", "prev": "◀", "next": "▶", "today": "今月"
    },
    "EN": {
        "us_market": "🇺🇸 US Market", "jp_market": "🇯🇵 JP Market",
        "dst": "Daylight Saving", "std": "Standard Time",
        "open": "🟢 OPEN (Closes in: ", "closed_pre": "⏳ CLOSED (Opens in: ",
        "closed_post": "🔴 CLOSED (Market Closed)", "next_open": "Next Open in: ",
        "weekend": "Weekend", "holiday": "Holiday", "prev": "Prev", "next": "Next", "today": "Current"
    }
}
L = T[st.session_state.lang]

# --- スタイル設定（モバイル最適化） ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,500&display=swap" rel="stylesheet">
<style>
    header[data-testid="stHeader"] { background-color: white; height: 4rem; display: flex; align-items: center; padding: 0 1rem; border-bottom: 1px solid #f0f2f6; }
    header[data-testid="stHeader"] div:first-child, header[data-testid="stHeader"] .stHeaderActionElements { display: none !important; }
    .header-logo-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #444; font-style: italic; }
    .main-big-title { font-family: 'Playfair Display', serif; font-size: 1.8rem; color: #333; font-style: italic; text-align: center; margin-bottom: 20px; line-height: 1.2; }
    .main-spacer { margin-top: 60px; }
    
    /* 価格ボードをモバイルでも横一列に強制 */
    [data-testid="stHorizontalBlock"] > div { min-width: 0 !important; }
    .indicator-box { border: 1px solid #ddd; padding: 5px; text-align: center; background-color: #fff; margin-bottom: 10px; }
    .indicator-label { font-size: 0.7rem; color: #888; font-weight: bold; overflow: hidden; white-space: nowrap; }
    .indicator-value { font-size: 0.9rem; font-weight: bold; margin: 2px 0; }
    
    /* カレンダー操作ボタンを一行に強制 */
    .stButton > button { border-radius: 0px !important; border: 1px solid #ddd !important; width: 100%; height: 35px; font-weight: bold; font-size: 0.8rem; padding: 0 !important; }
    
    /* カレンダーテーブルの調整 */
    .calendar-table { font-family: 'Courier New', Courier, monospace; text-align: center; width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 0.8rem; }
    .calendar-table tr { height: 35px; }
    .today-marker { background-color: #ff4b4b; color: white; display: inline-flex; align-items: center; justify-content: center; width: 25px; height: 25px; font-weight: bold; }
    
    .price-up { color: #ff4b4b; } .price-down { color: #1e90ff; }
    .market-status { font-size: 0.9rem; font-weight: bold; padding: 8px; border: 1px solid #ddd; margin-bottom: 10px; }
    
    /* モバイル用のメディアクエリ */
    @media (max-width: 640px) {
        .main-big-title { font-size: 1.3rem; }
        [data-testid="column"] { padding: 0 !important; margin-bottom: 20px; }
        .indicator-value { font-size: 0.8rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- ヘッダー描画 ---
st.markdown(f"""
    <div style="position: fixed; top: 0; left: 0; width: 100%; background: white; z-index: 999; padding: 10px 20px; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center;">
        <div class="header-logo-title">Stock Calendar</div>
        <div id="lang-trigger"></div>
    </div>
""", unsafe_allow_html=True)

with st.container():
    h_col1, h_col2 = st.columns([6, 2])
    with h_col2:
        new_lang = st.segmented_control("Lang", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
        if new_lang and new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

st.markdown('<div class="main-spacer"></div>', unsafe_allow_html=True)
st.markdown('<div class="main-big-title">Japan/US Stock Market<br>Real-time Calendar</div>', unsafe_allow_html=True)

# --- 価格ボード（常に横一列） ---
@st.cache_data(ttl=60)
def get_market_prices():
    tickers = { "S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X" }
    data = {}
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker); hist = t.history(period="2d")
            curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            data[name] = {"price": curr, "diff": curr - prev, "pct": ((curr - prev)/prev)*100}
        except: data[name] = {"price": 0, "diff": 0, "pct": 0}
    return data

p = get_market_prices()
m_cols = st.columns(3)
for i, (name, d) in enumerate(p.items()):
    c_cls, sym = ("price-up", "▲") if d['diff'] >= 0 else ("price-down", "▼")
    with m_cols[i]:
        st.markdown(f'<div class="indicator-box"><div class="indicator-label">{name}</div><div class="indicator-value">{d["price"]:,.1f}</div><div class="{c_cls}" style="font-size:0.6rem;">{sym}{abs(d["diff"]):.1f}</div></div>', unsafe_allow_html=True)

# --- 市場ステータス計算 ---
def get_next_open(now, country_code):
    cc, th = ("US", holidays.CountryHoliday("US")) if country_code == "US" else ("JP", holidays.CountryHoliday("JP"))
    ot = time(9, 30) if country_code == "US" else time(9, 0)
    td = now.date()
    if now < datetime.combine(td, ot).replace(tzinfo=now.tzinfo) and td.weekday() < 5 and td not in th: return datetime.combine(td, ot).replace(tzinfo=now.tzinfo)
    while True:
        td += timedelta(days=1)
        if td.weekday() < 5 and td not in th: return datetime.combine(td, ot).replace(tzinfo=now.tzinfo)

def get_market_status_ui(now, market_type):
    cc, th = ("US", holidays.CountryHoliday("US")) if market_type == "US" else ("JP", holidays.CountryHoliday("JP"))
    is_h = now.date() in th
    ot, ct = (now.replace(hour=9, minute=30, second=0), now.replace(hour=16, minute=0, second=0)) if market_type == "US" else (now.replace(hour=9, minute=0, second=0), now.replace(hour=15, minute=0, second=0))
    nx = get_next_open(now, market_type); df = nx - now
    cd = f"{df.days*24 + df.seconds//3600}:{(df.seconds//60)%60:02d}:{df.seconds%60:02d}"
    if not (0 <= now.weekday() <= 4) or is_h: return f"😴 CLOSED <br><small>{L['next_open']} {cd}</small>", "#f5f5f5"
    if now < ot: d = ot-now; return f"{L['closed_pre']} {d.seconds//3600:02d}:{(d.seconds//60)%60:02d})", "#fffbe6"
    elif ot <= now < ct: d = ct-now; return f"{L['open']} {d.seconds//3600:02d}:{(d.seconds//60)%60:02d})", "#e6ffed"
    else: return f"{L['closed_post']} <br><small>{L['next_open']} {cd}</small>", "#fff1f0"

def draw_cal(now_full, country_code, state_key, country_tz):
    view_date = st.session_state[state_key]
    st.markdown(f"##### {view_date.strftime('%Y/%m' if st.session_state.lang == 'JP' else '%B %Y')}")
    target_holidays = holidays.CountryHoliday(country_code)
    cal = calendar.monthcalendar(view_date.year, view_date.month)
    html = f'<table class="calendar-table"><tr><th>{"Su" if st.session_state.lang == "EN" else "日"}</th><th>{"Mo" if st.session_state.lang == "EN" else "月"}</th><th>{"Tu" if st.session_state.lang == "EN" else "火"}</th><th>{"We" if st.session_state.lang == "EN" else "水"}</th><th>{"Th" if st.session_state.lang == "EN" else "木"}</th><th>{"Fr" if st.session_state.lang == "EN" else "金"}</th><th>{"Sa" if st.session_state.lang == "EN" else "土"}</th></tr>'
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
    # ボタンを一行に並べる
    b1, b2, b3 = st.columns([1, 2, 1])
    with b1: 
        if st.button(L["prev"], key=f"p_{state_key}"):
            m, y = (st.session_state[state_key].month-1, st.session_state[state_key].year) if st.session_state[state_key].month > 1 else (12, st.session_state[state_key].year-1)
            st.session_state[state_key] = date(y, m, 1)
    with b2:
        if st.button(L["today"], key=f"t_{state_key}"): st.session_state[state_key] = datetime.now(pytz.timezone(country_tz)).date().replace(day=1)
    with b3:
        if st.button(L["next"], key=f"n_{state_key}"):
            m, y = (st.session_state[state_key].month+1, st.session_state[state_key].year) if st.session_state[state_key].month < 12 else (1, st.session_state[state_key].year+1)
            st.session_state[state_key] = date(y, m, 1)

# --- モバイル：タブ切り替え ---
tz_ny, tz_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
now_ny, now_jp = datetime.now(tz_ny), datetime.now(tz_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = now_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = now_jp.date().replace(day=1)

tab_us, tab_jp = st.tabs([L["us_market"], L["jp_market"]])

with tab_us:
    st.markdown(f'<div style="font-size:0.8rem; font-weight:bold;">{now_ny.strftime("%Y/%m/%d %H:%M:%S")}</div>', unsafe_allow_html=True)
    status, color = get_market_status_ui(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_cal(now_ny, "US", "v_us", "America/New_York")

with tab_jp:
    st.markdown(f'<div style="font-size:0.8rem; font-weight:bold;">{now_jp.strftime("%Y/%m/%d %H:%M:%S")}</div>', unsafe_allow_html=True)
    status, color = get_market_status_ui(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_cal(now_jp, "JP", "v_jp", "Asia/Tokyo")
