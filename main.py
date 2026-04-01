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
    /* 標準要素の非表示と余白削除 */
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; padding-bottom: 0rem !important; margin-top: -65px !important; }}

    /* ヘッダー: タイトルと言語スイッチを一行で中央揃え */
    .custom-header-container {{
        display: flex;
        justify-content: space-between;
        align-items: center; /* 垂直方向の中央揃え */
        width: 100%;
        padding: 10px 0;
    }}
    .header-logo-title {{
        font-family: 'Inter', sans-serif;
        font-size: 1.5rem;
        font-weight: 900;
        color: #111;
        letter-spacing: -0.04em;
        margin: 0;
        line-height: 1;
    }}
    .lang-switcher-box {{
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }}

    /* 市場ステータスの巨大一行スタイル */
    .status-line {{
        font-size: 1.6rem; font-weight: 900; padding: 12px; border: 1px solid #ddd;
        border-left: 8px solid #111; background-color: #fff; margin-bottom: 15px;
        line-height: 1.2; display: flex; flex-wrap: wrap; align-items: center; gap: 15px;
    }}
    .status-label {{ color: #111; }}
    .status-next {{ font-size: 1.1rem; color: #666; font-weight: 700; }}

    /* モバイルでも3列/一行を強制する設定 */
    .force-row [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 10px !important;
    }}
    .force-row [data-testid="stHorizontalBlock"] > div {{
        width: 100% !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }}

    /* 価格ボード */
    .indicator-box {{ 
        border: 1px solid #ddd; padding: 10px 2px; text-align: center; 
        background-color: #fff; margin-bottom: 10px; 
    }}
    .indicator-label {{ font-size: 0.75rem; color: #666; font-weight: 700; text-transform: uppercase; }}
    .indicator-value {{ font-size: 1.2rem; font-weight: 900; color: #111; }}
    
    /* カレンダーボタン */
    .stButton > button {{ 
        border-radius: 0px !important; border: 1px solid #ccc !important; 
        width: 100%; height: 40px; font-weight: 700; font-size: 0.85rem; 
    }}

    /* カレンダーテーブル */
    .calendar-table {{ font-family: sans-serif; text-align: center; width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 10px; }}
    .calendar-table th {{ font-weight: 800; padding-bottom: 8px; font-size: 0.9rem; }}
    .calendar-table th:first-child, .calendar-table th:last-child {{ color: #d71920; }}
    .holiday-red {{ color: #d71920 !important; font-weight: 800; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; font-weight: 800; }}
    
    .price-up {{ color: #d71920; }} .price-down {{ color: #0050b3; }}
    .market-section {{ margin-bottom: 50px; padding-bottom: 20px; border-bottom: 2px solid #eee; }}

    @media (max-width: 600px) {{
        .header-logo-title {{ font-size: 1.1rem; }}
        .status-line {{ font-size: 1.2rem; gap: 5px; }}
    }}
</style>
""", unsafe_allow_html=True)

# --- 4. ヘッダー（タイトルと言語スイッチを一行・中央揃え・右寄せ） ---
st.markdown('<div class="custom-header-container">', unsafe_allow_html=True)
header_left, header_right = st.columns([7, 3])
with header_left:
    st.markdown('<div class="header-logo-title">Stock Market Real-time</div>', unsafe_allow_html=True)
with header_right:
    st.markdown('<div class="lang-switcher-box">', unsafe_allow_html=True)
    new_lang = st.segmented_control("Language", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<hr style="margin: 0px 0 15px 0; border: 0; border-top: 1px solid #eee;">', unsafe_allow_html=True)

# --- 5. 価格ボード（3列横並び固定） ---
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
st.markdown('<div class="force-row">', unsafe_allow_html=True)
p_cols = st.columns(3)
for i, (name, d) in enumerate(prices.items()):
    c, s = ("price-up", "▲") if d['diff'] >= 0 else ("price-down", "▼")
    with p_cols[i]:
        st.markdown(f'<div class="indicator-box"><div class="indicator-label">{name}</div><div class="indicator-value">{d["val"]:,.0f}</div><div class="{c}" style="font-size:0.75rem; font-weight:700;">{s}{abs(d["diff"]):.1f} ({d["pct"]:.2f}%)</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

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

def draw_cal(now_full, cc, state_key, tz_name):
    view = st.session_state[state_key]
    st.markdown(f"<div style='font-weight:900; font-size:1.4rem; margin-bottom:10px;'>{view.strftime('%Y / %m' if st.session_state.lang=='JP' else '%B %Y')}</div>", unsafe_allow_html=True)
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
                txt = f'<span class="today-marker">{d}</span>' if curr == now_full.date() else str(d)
                html += f'<td><span class="{cls}">{txt}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)
    
    st.markdown('<div class="force-row">', unsafe_allow_html=True)
    b_cols = st.columns([1, 1, 1])
    with b_cols[0]:
        if st.button(L["prev_m"], key=f"p_{cc}"):
            m, y = (view.month-1, view.year) if view.month > 1 else (12, view.year-1)
            st.session_state[state_key] = date(y, m, 1); st.rerun()
    with b_cols[1]:
        if st.button(L["today"], key=f"t_{cc}"):
            st.session_state[state_key] = datetime.now(pytz.timezone(tz_name)).date().replace(day=1); st.rerun()
    with b_cols[2]:
        if st.button(L["next_m"], key=f"n_{cc}"):
            m, y = (view.month+1, view.year) if view.month < 12 else (1, view.year+1)
            st.session_state[state_key] = date(y, m, 1); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 表示実行（完全縦並び） ---
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

# 米国
st.markdown('<div class="market-section">', unsafe_allow_html=True)
st.header(L["us_market"])
st.markdown(get_market_status(n_ny, "US"), unsafe_allow_html=True)
draw_cal(n_ny, "US", "v_us", "America/New_York")
st.markdown('</div>', unsafe_allow_html=True)

# 日本
st.markdown('<div class="market-section">', unsafe_allow_html=True)
st.header(L["jp_market"])
st.markdown(get_market_status(n_jp, "JP"), unsafe_allow_html=True)
draw_cal(n_jp, "JP", "v_jp", "Asia/Tokyo")
st.markdown('</div>', unsafe_allow_html=True)
