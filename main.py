import streamlit as st
from datetime import datetime, timedelta, date, time
import pytz
import calendar
import holidays
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. 言語設定 ---
if 'lang' not in st.session_state:
    st.session_state.lang = "JP"

# --- 2. 基本設定 ---
calendar.setfirstweekday(calendar.SUNDAY)
st_autorefresh(interval=60000, key="data_refresh")
st_autorefresh(interval=1000, key="clock_refresh")
st.set_page_config(page_title="Market Watch", layout="wide")

T = {
    "JP": {
        "us_market": "🇺🇸 米国市場", "jp_market": "🇯🇵 日本市場",
        "next": "次回の開場: ", "prev_m": "◀ 前月", "next_m": "次月 ▶", "today": "今月",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土",
        "waiting": "開場待ち", "open": "開場中", "closed": "本日終了", "weekend": "週末休み", "holiday": "祝日休み"
    },
    "EN": {
        "us_market": "🇺🇸 US Market", "jp_market": "🇯🇵 JP Market",
        "next": "Next Open: ", "prev_m": "◀ Prev", "next_m": "Next ▶", "today": "Current",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT",
        "waiting": "WAITING", "open": "OPEN", "closed": "CLOSED", "weekend": "WEEKEND", "holiday": "HOLIDAY"
    }
}
L = T[st.session_state.lang]

# --- 3. スタイル設定 ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; margin-top: -65px !important; }}

    .header-row {{
        display: flex; justify-content: space-between; align-items: center; 
        padding: 10px 0; margin-bottom: 5px;
    }}
    .header-logo-title {{
        font-family: 'Inter', sans-serif; font-size: 1.4rem; font-weight: 900; 
        color: #111; letter-spacing: -0.04em;
    }}

    /* ステータス行：本日終了 ＋ 次回開場 */
    .status-line {{
        font-size: 1.5rem; font-weight: 900; padding: 12px; border: 1px solid #ddd;
        border-left: 8px solid #111; background-color: #fff; margin-bottom: 15px;
        line-height: 1.2; display: flex; align-items: center; gap: 15px;
    }}
    .status-label {{ color: #111; }}
    .status-next {{ font-size: 1.0rem; color: #666; font-weight: 700; }}

    /* カレンダーヘッダー（日付・時刻・DST） */
    .cal-info-header {{
        display: flex; align-items: baseline; gap: 10px; margin-bottom: 8px;
    }}
    .cal-title {{ font-weight: 900; font-size: 1.2rem; }}
    .cal-time {{ font-family: 'Courier New', monospace; font-size: 1.1rem; font-weight: 800; color: #111; }}
    .cal-dst {{ font-size: 0.8rem; font-weight: 700; color: #666; background: #eee; padding: 2px 6px; }}

    [data-testid="column"] [data-testid="stHorizontalBlock"] {{
        display: flex !important; flex-direction: row !important; align-items: center !important; gap: 5px !important;
    }}
    [data-testid="column"] [data-testid="stHorizontalBlock"] > div {{
        width: 100% !important; flex: 1 1 0% !important; min-width: 0 !important;
    }}

    .indicator-box {{ border: 1px solid #ddd; padding: 8px 2px; text-align: center; background-color: #fff; }}
    .indicator-label {{ font-size: 0.65rem; color: #666; font-weight: 700; text-transform: uppercase; }}
    .indicator-value {{ font-size: 1.0rem; font-weight: 900; color: #111; }}
    
    .stButton > button {{ border-radius: 0px !important; border: 1px solid #ccc !important; width: 100%; height: 38px; font-weight: 700; font-size: 0.75rem; }}

    .calendar-table {{ font-family: sans-serif; text-align: center; width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 10px; }}
    .calendar-table th {{ font-weight: 800; padding-bottom: 5px; font-size: 0.85rem; }}
    .calendar-table th:first-child, .calendar-table th:last-child {{ color: #d71920; }}
    .holiday-red {{ color: #d71920 !important; font-weight: 800; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; font-weight: 800; }}
    
    .price-up {{ color: #d71920; }} .price-down {{ color: #0050b3; }}

    @media (max-width: 600px) {{
        .status-line {{ font-size: 1.1rem; flex-direction: column; align-items: flex-start; gap: 5px; }}
        .cal-info-header {{ flex-wrap: wrap; gap: 5px; }}
    }}
</style>
""", unsafe_allow_html=True)

# --- 4. ヘッダー ---
st.markdown('<div class="header-row">', unsafe_allow_html=True)
h_l, h_r = st.columns([7, 3])
with h_l:
    st.markdown('<div class="header-logo-title">Stock Market Real-time</div>', unsafe_allow_html=True)
with h_r:
    new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<hr style="margin: 0px 0 15px 0; border: 0; border-top: 1px solid #eee;">', unsafe_allow_html=True)

# --- 5. 価格ボード ---
@st.cache_data(ttl=60)
def get_prices():
    tickers = { "S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X" }
    res = {}
    for k, v in tickers.items():
        try:
            t = yf.Ticker(v); h = t.history(period="2d")
            c, p = h['Close'].iloc[-1], h['Close'].iloc[-2]
            res[k] = {"val": c, "diff": c - p, "pct": (c-p)/p*100}
        except: res[k] = {"val": 0, "diff": 0, "pct": 0}
    return res

prices = get_prices()
p_cols = st.columns(3)
for i, (name, d) in enumerate(prices.items()):
    c, s = ("price-up", "▲") if d['diff'] >= 0 else ("price-down", "▼")
    with p_cols[i]:
        st.markdown(f'<div class="indicator-box"><div class="indicator-label">{name}</div><div class="indicator-value">{d["val"]:,.0f}</div><div class="{c}" style="font-size:0.6rem; font-weight:700;">{s}{abs(d["diff"]):.1f}</div></div>', unsafe_allow_html=True)

# --- 6. 共通ロジック ---
def get_market_status(now, m_type):
    cc, th = ("US", holidays.CountryHoliday("US")) if m_type == "US" else ("JP", holidays.CountryHoliday("JP"))
    ot, ct = (time(9, 30), time(16, 0)) if m_type == "US" else (time(9, 0), time(15, 0))
    td = now.date()
    nx = td
    if now.time() >= ct or td.weekday() >= 5 or td in th:
        while True:
            nx += timedelta(days=1)
            if nx.weekday() < 5 and nx not in th: break
    next_open_str = f"{L['next']}{nx.strftime('%m/%d')} {ot.strftime('%H:%M')}"
    if td.weekday() >= 5 or td in th:
        st_text = L["holiday"] if td in th else L["weekend"]; bg = "#f9f9f9"
    elif now.time() < ot: st_text = L["waiting"]; bg = "#fffbe6"
    elif ot <= now.time() < ct: st_text = L["open"]; bg = "#e6ffed"
    else: st_text = L["closed"]; bg = "#fff1f0"
    return f'<div class="status-line" style="background-color: {bg};"><span class="status-label">{st_text}</span> <span class="status-next">{next_open_str}</span></div>'

def draw_cal_section(now, cc, state_key, tz_name, suffix):
    view = st.session_state[state_key]
    
    # 日付・時刻・DST情報の生成
    date_str = now.strftime('%Y / %m / %d')
    time_str = now.strftime('%H:%M:%S')
    dst_label = ""
    if cc == "US":
        is_dst = now.dst() != timedelta(0)
        dst_label = f'<span class="cal-dst">{"DST" if is_dst else "ST"}</span>'
    
    # ヘッダー描画
    st.markdown(f'''
    <div class="cal-info-header">
        <span class="cal-title">{date_str}</span>
        <span class="cal-time">{time_str}</span>
        {dst_label}
    </div>
    ''', unsafe_allow_html=True)
    
    th = holidays.CountryHoliday(cc, years=view.year)
    cal = calendar.monthcalendar(view.year, view.month)
    html = f'<table class="calendar-table"><tr><th>{L["sun"]}</th><th>{L["mon"]}</th><th>{L["tue"]}</th><th>{L["wed"]}</th><th>{L["thu"]}</th><th>{L["fri"]}</th><th>{L["sat"]}</th></tr>'
    for w in cal:
        html += '<tr>'
        for i, d in enumerate(w):
            if d == 0: html += '<td></td>'
            else:
                curr = date(view.year, view.month, d)
                is_red = (i==0 or i==6 or curr in th)
                cls = "holiday-red" if is_red else ""
                txt = f'<span class="today-marker">{d}</span>' if curr == now.date() else str(d)
                html += f'<td><span class="{cls}">{txt}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)
    
    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        if st.button(L["prev_m"], key=f"p_{suffix}"):
            m, y = (view.month-1, view.year) if view.month > 1 else (12, view.year-1)
            st.session_state[state_key] = date(y, m, 1); st.rerun()
    with b2:
        if st.button(L["today"], key=f"t_{suffix}"):
            st.session_state[state_key] = now.date().replace(day=1); st.rerun()
    with b3:
        if st.button(L["next_m"], key=f"n_{suffix}"):
            m, y = (view.month+1, view.year) if view.month < 12 else (1, view.year+1)
            st.session_state[state_key] = date(y, m, 1); st.rerun()

# --- 7. 表示実行 ---
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

m_col1, m_col2 = st.columns(2, gap="large")
with m_col1:
    st.header(L["us_market"])
    st.markdown(get_market_status(n_ny, "US"), unsafe_allow_html=True)
    draw_cal_section(n_ny, "US", "v_us", "America/New_York", "dus")
with m_col2:
    st.header(L["jp_market"])
    st.markdown(get_market_status(n_jp, "JP"), unsafe_allow_html=True)
    draw_cal_section(n_jp, "JP", "v_jp", "Asia/Tokyo", "djp")
