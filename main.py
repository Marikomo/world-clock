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
st.set_page_config(page_title="Market Watch", layout="wide")

T = {
    "JP": {
        "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場", "next": "次回の開場: ",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土",
        "open": "開場中", "closed": "閉場中", "holiday": "休場", "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶"
    },
    "EN": {
        "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market", "next": "Next Open: ",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT",
        "open": "OPEN", "closed": "CLOSED", "holiday": "HOLIDAY", "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶"
    }
}
L = T[st.session_state.lang]

# --- 2. 究極のCSS（Streamlitのカラム要素を使わずにレイアウトする） ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; margin-top: -65px !important; }}

    /* 全ての横並び要素を強制するフレックスボックス */
    .absolute-row {{
        display: flex !important; flex-direction: row !important;
        justify-content: space-between !important; align-items: center !important;
        width: 100% !important; gap: 5px !important; margin-bottom: 10px;
    }}
    .flex-fill {{ flex: 1 !important; text-align: center; }}

    /* ヘッダー */
    .header-logo-title {{ font-family: 'Inter', sans-serif; font-size: 1.1rem; font-weight: 900; color: #111; letter-spacing: -0.04em; }}

    /* 市場ステータス */
    .status-line {{
        font-size: 1.3rem; font-weight: 900; padding: 10px; border: 1px solid #ddd;
        border-left: 8px solid #111; background-color: #fff; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }}
    .status-next {{ font-size: 0.8rem; color: #666; font-weight: 700; }}

    /* 日付・時計 */
    .cal-header {{ font-family: 'Inter', sans-serif; display: flex; align-items: baseline; gap: 8px; margin-bottom: 5px; }}
    .cal-date, .cal-time {{ font-weight: 900; font-size: 1.05rem; color: #111; }}
    .cal-dst {{ font-size: 0.75rem; font-weight: 700; color: #666; }}

    /* 価格ボード */
    .price-box {{ border: 1px solid #ddd; padding: 6px 2px; background-color: #fff; }}
    .price-label {{ font-size: 0.6rem; color: #666; font-weight: 700; }}
    .price-val {{ font-size: 0.9rem; font-weight: 900; }}

    /* ボタン（生のHTMLボタン用） */
    .custom-html-btn {{
        background: #fff; border: 1px solid #ccc; width: 100%; height: 36px;
        font-weight: 700; font-size: 0.75rem; cursor: pointer; color: #333;
    }}

    .calendar-table {{ font-family: sans-serif; text-align: center; width: 100%; border-collapse: collapse; table-layout: fixed; }}
    .calendar-table th {{ font-weight: 800; padding-bottom: 5px; font-size: 0.8rem; }}
    .calendar-table th:first-child, .calendar-table th:last-child {{ color: #d71920; }}
    .holiday-red {{ color: #d71920 !important; font-weight: 800; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; font-weight: 800; }}
    
    .price-up {{ color: #d71920; }} .price-down {{ color: #0050b3; }}

    @media (max-width: 600px) {{
        .header-logo-title {{ font-size: 0.85rem; }}
        .status-line {{ font-size: 1.0rem; }}
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. データ取得 ---
@st.cache_data(ttl=60)
def get_prices():
    tickers = { "S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X" }
    res = {}
    for k, v in tickers.items():
        try:
            t = yf.Ticker(v); h = t.history(period="2d")
            c, p = h['Close'].iloc[-1], h['Close'].iloc[-2]
            res[k] = {"val": c, "diff": c - p}
        except: res[k] = {"val": 0, "diff": 0}
    return res
prices = get_prices()

# --- 4. ヘッダー（絶対一行：言語ボタンを独自に配置） ---
# 言語切り替えロジック
if 'lang_select' not in st.session_state: st.session_state.lang_select = st.session_state.lang

# HTMLでヘッダーを組む（ボタンだけはStreamlitを呼び出すために空けておく）
st.markdown('<div class="absolute-row">', unsafe_allow_html=True)
h_col1, h_col2 = st.columns([6, 4])
with h_col1:
    st.markdown('<div class="header-logo-title" style="margin-top:10px;">Stock Market Real-time</div>', unsafe_allow_html=True)
with h_col2:
    new_lang = st.segmented_control("Language", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()
st.markdown('</div><hr style="margin: 0px 0 10px 0; border: 0; border-top: 1px solid #eee;">', unsafe_allow_html=True)

# --- 5. 価格ボード（絶対一行） ---
p_html = '<div class="absolute-row">'
for name, d in prices.items():
    c = "price-up" if d['diff'] >= 0 else "price-down"
    s = "▲" if d['diff'] >= 0 else "▼"
    p_html += f'''<div class="flex-fill price-box"><div class="price-label">{name}</div><div class="price-val">{d["val"]:,.0f}</div><div class="{c}" style="font-size:0.55rem;">{s}{abs(d["diff"]):.0f}</div></div>'''
p_html += '</div>'
st.markdown(p_html, unsafe_allow_html=True)

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
    st_text = L["open"] if (ot <= now.time() < ct and td.weekday() < 5 and td not in th) else (L["holiday"] if (td.weekday() >= 5 or td in th) else L["closed"])
    bg = "#e6ffed" if st_text == L["open"] else ("#f9f9f9" if st_text == L["holiday"] else "#fff1f0")
    return f'<div class="status-line" style="background-color: {bg};"><span>{st_text}</span><span class="status-next">{L["next"]}{nx.strftime("%m/%d %H:%M")}</span></div>'

def draw_cal(now, cc, state_key, suffix):
    view = st.session_state[state_key]
    dst = f'DST: {"サマータイム中" if now.dst() != timedelta(0) else "非サマータイム中"}' if cc == "US" else ""
    st.markdown(f'<div class="cal-header"><span class="cal-date">{now.strftime("%Y/%m/%d")}</span><span class="cal-time">{now.strftime("%H:%M:%S")}</span><span class="cal-dst">{dst}</span></div>', unsafe_allow_html=True)
    
    th = holidays.CountryHoliday(cc, years=view.year)
    cal = calendar.monthcalendar(view.year, view.month)
    html = f'<table class="calendar-table"><tr><th>{L["sun"]}</th><th>{L["mon"]}</th><th>{L["tue"]}</th><th>{L["wed"]}</th><th>{L["thu"]}</th><th>{L["fri"]}</th><th>{L["sat"]}</th></tr>'
    for w in cal:
        html += '<tr>'
        for i, d in enumerate(w):
            if d == 0: html += '<td></td>'
            else:
                curr = date(view.year, view.month, d)
                cls = "holiday-red" if (i==0 or i==6 or curr in th) else ""
                txt = f'<span class="today-marker">{d}</span>' if curr == now.date() else str(d)
                html += f'<td><span class="{cls}">{txt}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)
    
    # ボタン一行強制（絶対命令）
    st.markdown('<div class="absolute-row">', unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button(L["prev"], key=f"p_{suffix}"):
            m, y = (view.month-1, view.year) if view.month > 1 else (12, view.year-1)
            st.session_state[state_key] = date(y, m, 1); st.rerun()
    with b2:
        if st.button(L["today"], key=f"t_{suffix}"):
            st.session_state[state_key] = now.date().replace(day=1); st.rerun()
    with b3:
        if st.button(L["next_m"], key=f"n_{suffix}"):
            m, y = (view.month+1, view.year) if view.month < 12 else (1, view.year+1)
            st.session_state[state_key] = date(y, m, 1); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. レイアウト実行 ---
tz_ny, tz_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(tz_ny), datetime.now(tz_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

# PCでは左右並び、モバイルでは自動縦積みを活かす大枠のカラム
c1, c2 = st.columns(2, gap="large")
with c1:
    st.header(L["us_m"])
    st.markdown(get_market_status(n_ny, "US"), unsafe_allow_html=True)
    draw_cal(n_ny, "US", "v_us", "us")
with c2:
    st.header(L["jp_m"])
    st.markdown(get_market_status(n_jp, "JP"), unsafe_allow_html=True)
    draw_cal(n_jp, "JP", "v_jp", "jp")
